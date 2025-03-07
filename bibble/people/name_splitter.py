#!/usr/bin/env python3
"""


"""
# ruff: noqa:

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
import collections
import contextlib
import hashlib
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref
import atexit # for @atexit.register
import faulthandler
# ##-- end stdlib imports

from bibtexparser import model
from jgdv import Proto, Mixin
from bibble.util.middlecore import IdenBlockMiddleware
import bibble._interface as API
from bibble.util.name_parts import NameParts
from bibble.mixins import FieldMatcher_m

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

    type Field = model.Field
    type Entry = model.Entry
    from bibtexparser.library import Library

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

@Proto(API.ReadTime_p)
@Mixin(FieldMatcher_m)
class SplitNames(IdenBlockMiddleware):
    """
    Refactored bibtexparser middleware to split grouped names of people into parts
    """
    _whitelist = ("author", "editor", "translator")

    @classmethod
    def metadata_key(cls) -> str:
        return "bibble-split-names"

    def __init__(self, *, fields:Maybe[list[str]]=None, **kwargs):
        super().__init__(**kwargs)
        self.set_field_matchers(white=fields or SplitNames._whitelist, black=[])

    def transform_Entry(self, entry, library) -> list[Block]:
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return [x]
            case Exception() as err:
                return [entry, self.make_error_block(entry, err)]
            case x:
                raise TypeError(type(x))
            
    def field_h(self, field:Field, entry:Entry) -> Result[list[Field], Exception]:
        raise NotImplementedError()
