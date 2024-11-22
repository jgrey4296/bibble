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

import pyisbn
import isbn_hyphenate
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

ISBN_STRIP_RE = re.compile(r"[\s-]")

class IsbnValidator(BlockMiddleware):
    """
      Try to validate the entry's isbn number
    """

    @staticmethod
    def metadata_key():
        return "BM-isbn-validator"

    def transform_entry(self, entry, library):
        match entry.get("isbn"):
            case None:
                return entry
            case model.Field(value=str() as val) if bool(val):
                try:
                    isbn = pyisbn.Isbn(ISBN_STRIP_RE.sub("", val))
                    if not isbn.validate():
                        raise pyisbn.IsbnError("validation fail")
                except pyisbn.IsbnError:
                    logging.warning("ISBN validation fail: %s : %s", entry.key, val)
                    entry.set_field(model.Field("invalid_isbn", val))
                    entry.set_field(model.Field("isbn", ""))
            case model.Field(value=str() as val):
                del entry['isbn']

        return entry
