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
import bibtexparser
import bibtexparser.model as model
import isbn_hyphenate
import pyisbn
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware, LibraryMiddleware)
from jgdv import Mixin, Proto

# ##-- end 3rd party imports

import bibble._interface as API
from . import _interface as MAPI
from bibble.util.middlecore import IdenBlockMiddleware

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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--|

@Proto(API.ReadTime_p)
class IsbnValidator(IdenBlockMiddleware):
    """
      Try to validate the entry's isbn number
    """

    @staticmethod
    def metadata_key():
        return "BM-isbn-validator"

    def on_read(self):
        return True

    def transform_entry(self, entry, library):
        match entry.get(MAPI.ISBN_K):
            case None:
                return entry
            case model.Field(value=str() as val) if bool(val):
                try:
                    isbn = pyisbn.Isbn(MAPI.ISBN_STRIP_RE.sub("", val))
                    if not isbn.validate():
                        raise pyisbn.IsbnError("validation fail")
                except pyisbn.IsbnError:
                    # TODO add a fail block
                    self._logger.warning("ISBN validation fail: %s : %s", entry.key, val)
                    entry.set_field(model.Field(MAPI.INVALID_ISBN_K, val))
                    entry.set_field(model.Field(MAPI.ISBN_K, ""))
            case model.Field(value=str() as val):
                del entry[MAPI.ISBN_K]

        return entry
