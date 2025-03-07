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
from bibtexparser.middlewares.middleware import (BlockMiddleware, LibraryMiddleware)

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
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
    type Field = model.Field
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(API.WriteTime_p)
@Mixin(ErrorRaiser_m, FieldMatcher_m)
class PathWriter(IdenBlockMiddleware):
    """
      Relativize library paths back to strings
    """

    _whitelist = ("file",)

    def __init__(self, lib_root:pl.Path=None, **kwargs):
        super().__init__(**kwargs)
        self.set_field_matchers(white=self._whitelist, black=[])
        self._lib_root = lib_root

    def on_write(self):
        return True

    def transform_Entry(self, entry:Entry, library:Library):
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return [x]
            case list() as errs:
                return [entry, self.make_error_block(entry, errs)]
            case x:
                raise TypeError(type(x))

    def field_h(self, field:Field, entry:Entry):
        match field.value:
            case str():
                pass
            case pl.Path() as val if not val.exists():
                return ValueError(f"On Export file does not exist: {entry.key} : {val}")
            case pl.Path() as val:
                try:
                    as_str = val.relative_to(self._lib_root)
                    field.value = as_str
                except ValueError:
                    field.value = str(val)
                    return ValueError(f"Failed to Relativize path {entry.key}: {val}")

        return [field]
