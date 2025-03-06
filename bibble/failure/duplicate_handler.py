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

import bibble._interface as API
from . import _interface as MAPI
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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--|

@Proto(API.ReadTime_p)
class DuplicateFinder(IdenLibraryMiddleware):

    def on_read(self):
        return True

    def transform(self, libary:Library) -> Library:
        keys = set()
        for entry in library.entries:
            if entry.key in keys:
                # duplicate
                pass
            else:
                keys.add(entry.key)
        else:
            return library


@Proto(API.ReadTime_p)
class DuplicateKeyHandler(IdenLibraryMiddleware):
    """ take duplicate entries and edit their key to be unique """

    def on_read(self):
        return True

    def transform(self, library:Library):
        count = 0
        for failed in library.failed_blocks:
            match failed:
                case model.DuplicateBlockKeyBlock():
                    count        += 1
                    uuid          = uuid1().hex
                    duplicate     = failed.ignore_error_block
                    original      = duplicate.key
                    duplicate.key = f"{duplicate.key}_dup_{uuid}"
                    library.add(duplicate)
                    library.remove(failed)
                    self.logger().warning("Duplicate Key found: %s -> %s", original, duplicate.key)
                case _:
                    pass
        else:
            self.logger().info("Adjusted %s duplicate blocks", count)
            return library
