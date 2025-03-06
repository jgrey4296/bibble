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

    type UniMiddleware = API.LibraryMiddleware_p
    type BiMiddleware  = API.BidirectionalMiddleware_p
    type Middleware    = UniMiddleware | BiMiddleware

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

    def add(self, *, read:Maybe[UniMiddleware]=None, write:Maybe[UniMiddleware]=None) -> None:
        if read is not None:
            self._read_time.append(read)
        if write is not None:
            self._write_time.append(write)

    def add_pair(self, mid:BidirectionalMiddleware_p):
        pass

    def read_stack() -> list[Middleware]:
        return self._read_time[:]

    def write_stack() -> list[Middleware]:
        return self._write_time[:]
