#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
import enum
import functools as ftz
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
import weakref
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from jgdv import Proto, Mixin
import bibtexparser
import bibtexparser.model as model
from bibtexparser.library import Library
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble import _interface as API
from bibble.util.mixins import ErrorRaiser_m, FieldMatcher_m
from bibble.util.middlecore import IdenBlockMiddleware

# ##-- end 1st party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Entry = model.Entry

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Mixin(ErrorRaiser_m, FieldMatcher_m)
class CleanUrls(IdenBlockMiddleware):
    """ Strip unnecessary doi and dblp prefixes from urls  """

    _whitelist = ("doi", "url", "ee")

    @staticmethod
    def metadata_key():
        return "BM-clean-urls"


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_field_matchers(white=self._whitelist, black=[])

    def on_read(self):
        return True

    def transform_entry(self, entry:Entry, library:Library):
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return x
            case Exception() as err:
                return [entry, self.make_error_block(entry, err)]
            case x:
                raise TypeError(type(x))

    def field_h(self, field, entry):
        fields = []
        match field.value:
            case str() as value if value.startswith("https://doi.org") and (field.key  == "doi" or "doi" not in entry):
                clean = value.removeprefix("https://doi.org/")
                fields.append(model.Field("doi", clean))
            case str() as value if value.startswith("db/") and "bibsource" not in entry:
                url = "".join(["https://dblp.org/", value])
                fields.append(model.Field("biburl", url))
                fields.append(model.Field("bibsource", "dblp computer science bibliography, https://dblp.org"))
            case str() as value if field.key == "ee" and "url" not in entry:
                fields.append(model.Field("url", value))
                fields.append(model.Field("ee", ""))
            case _:
                pass

        return entry
