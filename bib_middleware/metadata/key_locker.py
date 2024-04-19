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

KEY_CLEAN_RE = re.compile(r"[/:{}]")
KEY_SUB_CHAR = "_"

class LockCrossrefKeys(BlockMiddleware):
    """ ensure crossref consistency by appending _ to keys and removing chars i don't like"""

    @staticmethod
    def metadata_key():
        return "jg-lock-crossrefs"

    def transform_entry(self, entry, library):
        clean_key = KEY_CLEAN_RE.sub(KEY_SUB_CHAR, entry.key)
        entry.key = f"{clean_key}_"
        if "crossref" in entry.fields_dict:
            orig = entry.fields_dict['crossref'].value
            clean_ref = KEY_CLEAN_RE.sub(KEY_SUB_CHAR, orig)
            entry.set_field(model.Field("crossref", f"{clean_ref}_"))

        return entry

