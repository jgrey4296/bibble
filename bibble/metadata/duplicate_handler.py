#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

##-- builtin imports
from __future__ import annotations

# import abc
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
# from copy import deepcopy
# from dataclasses import InitVar, dataclass, field
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generic,
                    Iterable, Iterator, Mapping, Match, MutableMapping,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

KEY_CLEAN_RE = re.compile(r"[/:{}]")
KEY_SUB_CHAR = "_"

class DuplicateHandler(LibraryMiddleware):
    """ take duplciate entries and mark them as such """

    @staticmethod
    def metadata_key():
        return "BM-duplicate-handler"

    def transform(self, library):
        for block in library.failed_blocks:
            match block:
                case model.DuplicateBlockKeyBlock():
                    uuid = uuid1().hex
                    duplicate = block.ignore_error_block
                    original = duplicate.key
                    duplicate.key = f"{duplicate.key}_dup_{uuid}"
                    logging.warning("Duplicate Key found: %s -> %s", original, duplicate.key)
                    library.add(duplicate)
                    library.remove(block)
                case _:
                    raw = ""
                    if block._raw:
                        raw = block._raw[:20]
                    logging.warning("Bad Block: : %s : %s", block.start_line, raw)

        return library
