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
    from jgdv import Maybe, Either, Result
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|
type StringBlock  = model.String
type Field        = model.Field
type Block        = model.Block
type Entry        = model.Entry
type FailedBlock  = model.ParsingFailedBlock
type ErrorBlock   = model.MiddlewareErrorBlock
type CommentBlock = model.ExplicitComment | model.ImplicitComment

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:
ALLOW_INPLACE_MOD_K : Final[str] = "allow_inplace_modification"
ALLOW_PARALLEL_K    : Final[str] = "allow_parallel_execution"
LOGGER_K            : Final[str] = "logger"
KEEP_MATH_K         : Final[str] = "keep_math"
ENCLOSE_URLS_K      : Final[str] = "enclose_urls"
##--|
## Enums / Flags

class Capability_f(enum.Flag):
    """ A Flag for where middlewares can be in the read/write stack """

    insist_front = enum.auto()
    insist_end   = enum.auto()
    read_time    = enum.auto()
    write_time   = enum.auto()
    validate     = enum.auto()
    transform    = enum.auto()
    report       = enum.auto()

##--|
## Bibtexparser protcols

@runtime_checkable
class Library_p(Protocol):

    def add(self, blocks:list[Block], fail_on_duplicate_key: bool = False) -> None:
        pass

    def remove(self, blocks:list[Block]) -> None:
        pass

    def replace(self, old_block:Block, new_block:Block, fail_on_duplicate_key:bool=True) -> None:
        pass

    def blocks(self) -> list[Block]:
        pass

    def failed_blocks(self) -> list[FailedBlock]:
        pass

    def strings(self) -> list[StringBlock]:
        pass

    def strings_dict(self) -> dict[str, StringBlock]:
        pass

    def entries(self) -> list[Entry]:
        pass

    def entries_dict(self) -> dict[str, Entry]:
        pass

    def preambles(self) -> list[Preamble]:
        pass

    def comments(self) -> list[CommentBlock]:
        pass

@runtime_checkable
class BlockMiddleware_p(Protocol):

    def transform(self, library:Library) -> Library:
        pass

    def transform_block(self, block:Block, library:Library) -> list[Block]:
        pass

    def transform_entry(self, entry:Entry, library:Library) -> list[Block]:
        pass

    def transform_string(self, string:model.StringBlock, library:Library) -> list[Block]:
        pass

    def transform_preamble(self, preamble:model.Preamble, library:Library) -> list[Block]:
        pass

    def transform_explicit_comment(self, comment:model.ExplicitComment, library:Library) -> list[Block]:
        pass

    def transform_implicit_comment(self, comment:model.ImplicitComment, library:Library) -> list[Block]:
        pass

@runtime_checkable
class LibraryMiddleware_p(Protocol):

    def transform(self, library:Library) -> Library:
        pass

##--| New Middleware protocols:

@runtime_checkable
class BidirectionalMiddleware_p(Protocol):

    def read_transform(self, library:Library) -> Library:
        pass

    def write_transform(self, library:Library) -> Library:
        pass

@runtime_checkable
class AdaptiveMiddleware_p(Protocol):
    """ Middleware that looks up defined transforms using the type name,
    by mro.
    """

    def get_transforms_for(self, block:Block) -> list[Callable[[Block, Library], list[Block]]]:
        pass

    def transform(self, library:Library) -> Library:
        pass

##--| IO Protocols

@runtime_checkable
class Reader_p(Protocol):

    def read(self, source:str|pl.Path, *, into:Maybe[Library]=None, append:Maybe[list[Middleware]]=None) -> Maybe[Library]:
        pass

@runtime_checkable
class Writer_p(Protocol):

    def write(self, library:Library, *, file:Maybe[pl.Path]=None, append:Maybe[list[BlockMiddleware_p|LibraryMiddleware_p]]=None) -> str:
        pass

##--| Middleware protocols

@runtime_checkable
class CustomWriter_p(Protocol):

    def visit(self, writer:BibbleWriter_p) -> list[str]:
        pass

@runtime_checkable
class MiddlewareDir_p(Protocol):
    """ For Querying whether a middleware is for using at read or write time. """

    def on_read(self) -> bool:
        pass

    def on_write(self) -> bool:
        pass

@runtime_checkable
class ReadTime_p(Protocol):
    """ Protocol for signifying a middleware is for use on parsing bibtex to data
    TODO merge this into middlewaredir_p
    """

    def on_read(self) -> bool:
        pass

@runtime_checkable
class WriteTime_p(Protocol):
    """ Protocol for signifying middleware is for use on writing data to bibtex
    TODO merge this into middlewaredir_p
    """

    def on_write(self) -> bool:
        pass

@runtime_checkable
class EntrySkipper_p(Protocol):
    """ A whitelist based test for middlewares """

    def set_entry_skiplist(self, whitelist:list[str]) -> None:
        pass

    def should_skip_entry(self, entry:Entry, library:Library) -> bool:
        pass

@runtime_checkable
class FieldMatcher_p(Protocol):
    """ The protocol util.FieldMatcher_m relies on

    A Middleware with the FieldMatcher_m mixin will call the implemented field_h
    on each field that matches in an entry.
    """

    def set_field_matchers(self, *, white:list[str], black:list[str]) -> Self:
        pass

    def match_on_fields(self, entry: Entry, library: Library) -> Result[Entry, Exception]:
        pass

    def field_h(self, field:Field, entry:Entry) -> Result[list[Field], Exception]:
        pass

@runtime_checkable
class StrTransformer_p(Protocol):
    """ Describes the StringTransform_m """

    def _transform_raw_str(self, python_string:str) -> Result[str, Exception]:
        pass
