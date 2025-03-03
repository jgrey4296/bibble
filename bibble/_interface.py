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
from bibtexparser.library import Library

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
    from jgdv import Maybe, Either
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
type FieldReturn = tuple[list[model.Field], list[str]]
type Field       = model.Field
type Block       = model.Block
type Entry       = model.Entry
type FailList    = list[str]
# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
ALLOW_INPLACE_MOD_K : Final[str] = "allow_inplace_modification"
KEEP_MATH_K         : Final[str] = "keep_math"
ENCLOSE_URLS_K      : Final[str] = "enclose_urls"
##--|
## Bibtexparser protcols

@runtime_checkable
class BlockMiddleware_p(Protocol):

    def transform(self, library:Library) -> Library:
        pass

    def transform_block(self, block:Block, library:Library) -> Maybe[Block|list[Block]]:
        pass

    def transform_entry(self, entry:Entry, library:Library) -> Maybe[Block|list[Block]]:
        pass

    def transform_string(self, string:model.String, library:Library) -> Maybe[Block|list[Block]]:
        pass

    def transform_preamble(self, preamble:model.Preamble, library:Library) -> Maybe[Block|list[Block]]:
        pass

    def transform_explicit_comment(self, comment:model.ExplicitComment, library:Library) -> Maybe[Block|list[Block]]:
        pass

    def transform_implicit_comment(self, comment:model.ImplicitComment, library:Library) -> Maybe[Block|list[Block]]:
        pass

@runtime_checkable
class LibraryMiddleware_p(Protocol):

    def transform(self, library:Library) -> Library:
        pass

##--|

@runtime_checkable
class ReadTime_p(Protocol):
    """ Protocol for signifying a middleware is for use on parsing bibtex to data """

    def on_read(self) -> bool:
        pass

@runtime_checkable
class WriteTime_p(Protocol):
    """ Protocol for signifying middleware is for use on writing data to bibtex """

    def on_write(self) -> bool:
        pass

@runtime_checkable
class ErrorRaiser_p(Protocol):

    def make_error_block(self, entry:Entry, errs:list[str]) -> MiddlewareErrorBlock:
        pass

@runtime_checkable
class EntrySkipper_p(Protocol):
    """ A whitelist based test for middlewares """

    def set_entry_whitelist(self, whitelist:list[str]) -> None:
        pass

    def should_skip_entry(self, entry, library) -> bool:
        pass

@runtime_checkable
class FieldMatcher_p(Protocol):
    """ The protocol util.FieldMatcher_m relies on """

    def set_field_matchers(self, white:list[str]=None, black:list[str]=None, keep_default=True) -> Self:
        pass

    def match_on_fields(self, entry: Entry, library: Library) -> Either[Entry, FailList]:
        pass

    def field_h(self, field:Field, entry:Entry) -> FieldReturn:
        pass
