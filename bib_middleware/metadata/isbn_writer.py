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
from bib_middleware.util.base_writer import BaseWriter

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

ISBN_STRIP_RE = re.compile(r"[\s-]")

class IsbnWriter(BaseWriter):
    """
      format the isbn for writing
    """

    @staticmethod
    def metadata_key():
        return "BM-isbn-writer"

    def __init__(self):
        super().__init__()

    def transform_entry(self, entry, library):
        f_dict = entry.fields_dict
        if 'isbn' not in f_dict:
            return entry
        if "invalid_isbn" in f_dict:
            return entry
        if not bool(f_dict['isbn'].value):
            return entry

        try:
            isbn = isbn_hyphenate.hyphenate(f_dict['isbn'].value)
            entry.set_field(model.Field("isbn", isbn))
        except isbn_hyphenate.IsbnError as err:
            printer.warning("Writing ISBN failed: %s : %s", f_dict['isbn'].value, err)
            pass

        return entry
