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

##-- lib imports
import more_itertools as mitz
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
printer = logmod.getLogger("doot._printer")
##-- end logging

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

class DuplicateHandler(LibraryMiddleware):

    @staticmethod
    def metadata_key():
        return "jg-duplicate-handler"

    def transform(self, library):
        for block in library.failed_blocks:
            match block:
                case model.DuplicateBlockKeyBlock():
                    uuid = uuid1().hex
                    duplicate = block.ignore_error_block
                    duplicate.key = f"{duplicate.key}_{uuid}"
                    library.add(duplicate)
                    library.remove(block)
                case _:
                    printer.warning("Bad Block: : %s", block.start_line)

        return library


class LockCrossrefKeys(BlockMiddleware):
    """ ensure crossref consistency by appending _ to keys and removing chars i don't like"""

    def metadata_key(self):
        return str(self.__class__.__name__)

    def transform_entry(self, entry, library):
        clean_key = KEY_CLEAN_RE.sub(KEY_SUB_CHAR, entry.key)
        entry.key = f"{clean_key}_"
        if "crossref" in entry.fields_dict:
            orig = entry.fields_dict['crossref'].value
            clean_ref = KEY_CLEAN_RE.sub(KEY_SUB_CHAR, orig)
            entry.set_field(BTP.model.Field("crossref", f"{clean_ref}_"))

        return entry
