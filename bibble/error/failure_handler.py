#!/usr/bin/env python3
"""

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
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from jgdv import Proto
# ##-- end 3rd party imports

import bibble._interface as API
from bibble.util.middlecore import IdenLibraryMiddleware

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

    type Logger = logmod.Logger
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(API.ReadTime_p)
class FailureHandler(IdenLibraryMiddleware):
    """ Middleware to Filter failed blocks of a library,
    either to a logger output, or to a file
    Put at end of parse stack

    Will log out where the failed blocks start by line.
    """

    @staticmethod
    def metadata_key():
        return "BM-failure-handler"

    def __init__(self, **kwargs):
        file_target = kwargs.pop("file", None)
        super().__init__(**kwargs)
        match file_target:
            case None:
                self._file_target = None
            case str() as x:
                self._file_target = pl.Path(x)
            case pl.Path() as x:
                self._file_target = x

    def on_read(self):
        return True

    def transform(self, library):
        self.write_failures_to_file(library)
        total = len(library.failed_blocks)
        for i, block in enumerate(library.failed_blocks):
            match block:
                case model.ParsingFailedBlock():
                    self._logger.info(f"({i}/{total}) Bad Block: : %s", block.start_line)
                case x:
                    raise TypeError(type(x))

        return library

    def write_failures_to_file(self, library) -> None:
        if self._file_target is None:
            return
        if not bool(library.failed_blocks):
            return

        total = len(library.failed_blocks)
        with self._file_target.open("w") as f:
            for i, b in enumerate(library.failed_blocks):
                f.write("\n--------------------\n")
                f.write(f"- ({i}/{total}) : {b.start_line}\n")
                f.write(f"{b.error}")
                f.write("\n--------------------\n")
                f.write(b.raw)
