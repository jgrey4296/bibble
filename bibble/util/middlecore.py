#!/usr/bin/env python3
"""
Refactored core middleware classes from bibtexparser

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

import tqdm
import bibble._interface as API
from bibtexparser.library import Library
from bibtexparser import model

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

    type Block           = model.Block
    type Entry           = model.Entry
    type String          = model.String
    type Preamble        = model.Preamble
    type ExplicitComment = model.ExplicitComment
    type ImplicitComment = model.ImplicitComment
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class _BaseMiddleware:
    """
    The base middleware.
    has a metadata key,
    stores allow_inplace and allow_parallel
    and can have an injected logger.

    Any extra init kwargs are stored in _extra
    """
    allow_inplace : bool
    allow_parallel : bool

    @classmethod
    def metadata_key(cls) -> str:
        """Identifier of the middleware.
        This key is used to identify the middleware in a blocks metadata.
        """
        return cls.__name__

    def __init__(self, **kwargs):
        """

        """
        self.allow_inplace  = kwargs.pop(API.ALLOW_INPLACE_MOD_K, True)
        self.allow_parallel = kwargs.pop(API.ALLOW_PARALLEL_K, False)
        self._logger        = kwargs.pop(API.LOGGER_K, logging)
        self._extra         = kwargs

class IdenLibraryMiddleware(_BaseMiddleware):
    """ Identity Library Middleware, does nothing """

    def transform(self, library:Library) -> Library:
        match library:
            case Library() if self.allow_inplace:
                return library
            case Library():
                return deepcopy(library)

class IdenBlockMiddleware(_BaseMiddleware):
    """ Identity Block Middleware, does nothing
    If passed 'tqdm'=True uses tqdm around the block level loop
    """

    def transform(self, library:Library) -> Library:
        match self._extra:
            case {"tqdm":True}:
                iterator = tqdm(enumerate(library.blocks))
            case _:
                iterator = enumerate(library.blocks)

        blocks = []
        for i,b in iterator:
            match self.transform_block(b, library):
                case []:
                     blocks.append(b)
                case [*xs]:
                    blocks += xs
                case x:
                    raise TypeError(type(x), i, b)
        else:
            if self.allow_inplace:
                library.blocks = blocks
                return library
            else:
                return Library(blocks=blocks)

    def transform_block(self, block:Block, library:Library) -> list[Block]:
        return [block]

    def transform_entry(self, entry:Entry, library:Library) -> list[Block]:
        return [entry]

    def transform_string(self, string:String, library:Library) -> list[Block]:
        return [string]

    def transform_preamble(self, preamble:Preamble, library:Library) -> list[Block]:
        return [preamble]

    def transform_explicit_comment(self, comment:ExplicitComment, library:Library) -> list[Block]:
        return [comment]

    def transform_implicit_comment(self, comment:ImplicitComment, library:Library) -> list[Block]:
        return [comment]
