#!/usr/bin/env python3
"""

"""

from __future__ import annotations

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

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.library import Library
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)
from jgdv.files.tags import SubstitutionFile

# ##-- end 3rd party imports

# ##-- 1st party imports
from bib_middleware.util.base_writer import BaseWriter
from bib_middleware.util.error_raiser import ErrorRaiser_m
from bib_middleware.util.field_matcher import FieldMatcher_m
from bib_middleware.library import BibMiddlewareLibrary
from bib_middleware.model import MetaBlock
# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class FieldAccumulator(ErrorRaiser_m, FieldMatcher_m, BlockMiddleware):
    """ Create a set of all the values in a library of a field """

    class AccumulationBlock(MetaBlock):

        def __init__(self, name, data):
            super().__init__()
            self._name = name
            self._data = data


    @staticmethod
    def metadata_key():
        return "BM-field-accum"

    def __init__(self, name, fields:str|list[str], **kwargs):
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

        transformed.add(AccumulationBlock(self._attr_target, self._collection))
        return transformed

    def transform_entry(self, entry, library):
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field, entry):
        match field.value:
            case str() as value:
                self._collection.add(value)
            case list() | set() as value:
                self._collection.update(value)

        return field, []
