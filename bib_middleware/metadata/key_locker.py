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

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

KEY_CLEAN_RE  : Final[re.Pattern] = re.compile(r"[/:{}]")
KEY_SUFFIX_RE : Final[re.Pattern] = re.compile("_+$")
KEY_SUB_CHAR  : Final[str]        = "_"
LOCK_CHAR     : Final[str]        = "_"

class LockCrossrefKeys(BlockMiddleware):
    """ Ensure key/crossref consistency by:
    removing unwanted chars in the key,
    'locking' the key by forcing the key suffix to be a single underscore
    doing the same process to crossref fields.

    locked keys are ignored
    """

    @staticmethod
    def metadata_key():
        return "BM-lock-crossrefs"

    def __init__(self, regex:str|re.Pattern, sub:str, **kwargs):
        super().__init__(**kwargs)
        self._regex     : re.Pattern = re.compile(regex or KEY_CLEAN_RE)
        self._sub       : str        = sub or KEY_SUB_CHAR
        self._lock_char : str        = LOCK_CHAR
        self._bad_lock  : str        = f"{LOCK_CHAR}{LOCK_CHAR}"

    def transform_entry(self, entry, library):
        entry.key = self.clean_key(entry.key)

        match entry.get("crossref"):
            case None:
                pass
            case model.Field(value=value):
                entry.set_field(model.Field("crossref", self.clean_key(value)))

        return entry

    def clean_key(self, key:str) -> str:
        if key.endswith(self._lock_char) and not key.endswith(self._bad_lock):
            return key

        clean_key = self._regex.sub(self._sub, key)
        clean_key = KEY_SUFFIX_RE.sub("", key)
        return f"{clean_key}{self._lock_char}"
