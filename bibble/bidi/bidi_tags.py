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

from jgdv import Proto, Mixin
import bibble._interface as API
from bibble.util.middlecore import IdenBidiMiddleware
from bibble.metadata import TagsReader, TagsWriter

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

    from bibtexparser import model, Library
    type Entry = model.Entry
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

# Vars:

# Body:

@Proto(API.AdaptiveMiddleware_p, API.BidirectionalMiddleware_p)
class BidiTags(IdenBidiMiddleware):
    """ A simple wrapper around TagsReader and TagsWriter,
    to make a bidirectional tags middleware
    """

    def __init__(self, *args, reader:Maybe[TagsReader]=None, writer:Maybe[TagsWriter]=None, **kwargs) -> None:
        kwargs.setdefault(API.ALLOW_INPLACE_MOD_K, False)
        super().__init__(*args, **kwargs)
        self._reader = reader or TagsReader()
        self._writer = writer or TagsWriter()

    def read_transform_Entry(self, entry:Entry, library:Library) -> list[Entry]:
        return self._reader.transform_Entry(entry, library)

    def write_transform_Entry(self, entry:Entry, library:Library) -> list[Entry]:
        return self._writer.transform_Entry(entry, library)
