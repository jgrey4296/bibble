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
from jgdv import Proto, Mixin
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.library import Library
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)
from jgdv.files.tags import SubstitutionFile

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble.model import MetaBlock
from bibble.util.error_raiser_m import ErrorRaiser_m
from bibble.util.field_matcher_m import FieldMatcher_m
from bibble import _interface as API
from . import _interface as AccumPI

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(API.FieldMatcher_p)
@Mixin(ErrorRaiser_m, FieldMatcher_m)
class FieldAccumulator(BlockMiddleware):
    """ Create a set of all the values of a field, of all entries, in a library.

    'name' : the name of the accumulation block to store result in
    'fields' : the fields to accumulate values of.

    Fields can be individual values, or lists/sets of values

    """

    @staticmethod
    def metadata_key():
        return "BM-field-accum"

    def __init__(self, name:str, fields:str|list[str], **kwargs):
        super().__init__(**kwargs)
        self._attr_target = name
        match fields:
            case str() as x:
                self._target_fields = [x]
            case list():
                self._target_fields = fields

        self.set_field_matchers(white=self._target_fields)
        self._collection = set()

    def transform(self, library:Library):
        transformed : Library = super().transform(library)
        transformed.add(AccumPI.AccumulationBlock(self._attr_target, self._collection))
        return transformed

    def transform_entry(self, entry, library):
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return x
            case list() as errs:
                return [entry, self.make_error_block(entry, errs)]
            case x:
                raise TypeError(type(x))

    def field_h(self, field, entry):
        match field.value:
            case str() as value:
                self._collection.add(value)
            case list() | set() as value:
                self._collection.update(value)

        return field, []
