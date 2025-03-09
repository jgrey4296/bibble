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

import bibble._interface as API

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

    type UniMiddleware   = API.UniMiddleware
    type BidiMiddleware  = API.BidiMiddleware
    type Middleware      = API.Middleware

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

class PairStack:
    """ A pair of middleware stacks,
    allowing reader/writer pairs to be added at the same time
    """
    _read_time  : list[Middleware]
    _write_time : list[Middleware]

    def __init__(self):
        self._read_time  = []
        self._write_time = []

    def add(self, *, read:Maybe[list|Middleware]=None, write:Maybe[list|Middleware]=None) -> Self:
        """
        Add middlewares to the read/write stacks.
        """
        match read:
            case None | []:
                pass
            case [*xs]:
                for x in xs:
                    self.add(read=x)
            case API.LibraryMiddleware_p():
                self._read_time.append(read)
            case x:
                raise TypeError(type(x))

        match write:
            case None | []:
                pass
            case [*xs]:
                for x in xs:
                    self.add(write=x)
            case API.LibraryMiddleware_p():
                self._write_time.append(write)

        return self

    def add_pairs(self, *mids:BidiMiddleware) -> Self:
        """
        Add bidirectional middlewares to both the read and write stacks
        """
        for mid in mids:
            match mid:
                case API.BidirectionalMiddleware_p():
                    self._read_time.append(mid)
                    self._write_time.append(mid)
                case x:
                    raise TypeError(type(x))

        else:
            return self

    def read_stack(self) -> list[Middleware]:
        """ Return the read stack """
        return self._read_time[:]

    def write_stack(self) -> list[Middleware]:
        """ Return the write stack """
        return self._write_time[:]
