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

import pyisbn
import isbn_hyphenate
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

ISBN_STRIP_RE = re.compile(r"[\s-]")


class IsbnValidator(BlockMiddleware):
    """
      Convert file paths in bibliography to pl.Path's, expanding relative paths according to lib_root
    """

    @staticmethod
    def metadata_key():
        return "jg-isbn-validator"

    def transform_entry(self, entry, library):
        f_dict = entry.fields_dict
        if 'isbn' not in f_dict:
            return entry
        if not bool(f_dict['isbn'].value):
            return entry

        try:
            isbn = pyisbn.Isbn(ISBN_STRIP_RE.sub("", f_dict['isbn'].value))
            if not isbn.validate():
                raise pyisbn.IsbnError("validation fail")
        except pyisbn.IsbnError:
            printer.warning("ISBN validation fail: %s : %s", entry.key, f_dict['isbn'].value)
            entry.set_field(model.Field("invalid_isbn", f_dict['isbn'].value))
            entry.set_field(model.Field("isbn", ""))


        return entry

class IsbnWriter(BlockMiddleware):
    """
      Convert file paths in bibliography to pl.Path's, expanding relative paths according to lib_root
    """

    @staticmethod
    def metadata_key():
        return "jg-isbn-writer"

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
        except isbn_hyphenate.IsbnMalformedError:
            pass

        return entry

