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
from bibtexparser.middlewares.names import NameParts
from jgdv import Mixin, Proto

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from bibble.util.middlecore import IdenBlockMiddleware
from bibble.util.mixins import FieldMatcher_m
from bibble.util.name_parts import NameParts_d

# ##-- end 1st party imports

from . import _interface as API_N

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
    from jgdv import Maybe, Result
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type Entry = model.Entry
    type Field = model.Field
    from bibtexparser import Library

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(API.WriteTime_p)
@Mixin(FieldMatcher_m)
class NameWriter(IdenBlockMiddleware):
    """ Converts NameParts -> str's """
    _whitelist = ("author", "editor", "translator")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_field_matchers(white=self._whitelist, black=[])

    def on_write(self):
        return True

    def transform_Entry(self, entry:Entry, library:Library) -> list[Entry]:
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return [x]
            case Exception() as err:
                return [entry, self.make_error_block(entry, err)]
            case x:
                raise TypeError(type(x))

    def field_h(self, field:Field, entry:Entry) -> Result[list[Field], Exception]:
        result = []
        merger = self._merge_von_last_jr_first
        match field.value:
            case str():
                pass
            case [*xs] if all(isinstance(x, str) for x in xs):
                joined = API_N.JOIN_STR.join(xs)
                result.append(model.Field(field.key, joined, start_line=field.start_line))
            case [*xs] if all(isinstance(x, NameParts|NameParts_d) for x in xs):
                merged = [merger(x) for x in xs]
                joined = API_N.JOIN_STR.join(merged)
                result.append(model.Field(field.key, joined, start_line=field.start_line))
            case x:
                return TypeError("Unexpected name type", entry.key, type(x))


        return result

    def _merge_von_last_jr_first(self, name:NameParts|NameParts_d) -> str:
        match name:
            case NameParts() | NameParts_d():
                pass
            case x:
                raise TypeError(type(x))

        result = []
        if name.von:
            result.append(" ".join(name.von))
            result.append(" ")

        if name.last:
            result.append(" ".join(name.last))
            result.append(", ")

        if name.jr:
            result.append(" ".join(name.jr))
            result.append(", ")

        result.append(" ".join(name.first))

        full_name = "".join(result).removesuffix(", ").strip()
        return full_name
