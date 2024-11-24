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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)
from jgdv.files.tags import SubstitutionFile

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble.util.error_raiser_m import ErrorRaiser_m
from bibble.util.field_matcher_m import FieldMatcher_m

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class FieldSorter(ErrorRaiser_m, FieldMatcher_m, BlockMiddleware):
    """ Sort the entries of a field
    firsts are exact matches that go at the front.
    lasts are a list of patterns to match on
    """

    _first_defaults = []
    _last_defaults  = []

    @staticmethod
    def metadata_key():
        return "BM-field-sorter"

    def __init__(self, first:list[str], last:[str], **kwargs):
        super().__init__(**kwargs)
        self._firsts   = first or self._first_defaults
        self._lasts    = last or self._last_defaults
        self._stem_re  = re.compile("^[a-zA-Z_]+")

    def field_sort_key(self, field:model.Field):
        match self._stem_re.match(field.key):
            case None:
                key = field.key
            case x:
                key = x[0]

        try:
            return (self._lasts.index(key), field.key)
        except ValueError:
            return key

    def transform_entry(self, entry, library):
        # Get the firsts in order if they exist
        firsts = [y for x in self._firsts if (y:=entry.get(x,None)) is not None]
        rest, lasts = [], []
        for field in entry.fields:
            match self._stem_re.match(field.key):
                case None:
                    key = field.key
                case x:
                    key = x[0]
            if key in self._firsts:
                continue
            if key not in self._lasts:
                rest.append(field)
            else:
                lasts.append(field)

        # Sort the lasts
        rest  = sorted(rest, key=self.field_sort_key)
        lasts = sorted(lasts, key=self.field_sort_key)
        entry.fields = firsts + rest + lasts
        return entry
