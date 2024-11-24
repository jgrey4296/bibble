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


class FieldSubstitutor(ErrorRaiser_m, FieldMatcher_m, BlockMiddleware):
    """
      For a given field(s), and a given jgdv.SubstitutionFile,
    replace the field value as necessary in each entry.

    If force_single_value is True, only the first replacement will be used,
    others will be discarded

    """

    @staticmethod
    def metadata_key():
        return "BM-field-sub"

    def __init__(self, fields:str|list[str], subs:None|SubstitutionFile, force_single_value:bool=False, **kwargs):
        super().__init__(**kwargs)
        match fields:
            case str() as x:
                self._target_fields = [x]
            case list():
                self._target_fields = fields

        self._subs               = subs
        self._force_single_value = force_single_value
        self.set_field_matchers(white=self._target_fields)

    def transform_entry(self, entry, library):
        if self._subs is None or not bool(self._subs):
            return entry

        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field, entry):
        match field.value:
            case str() as value if self._force_single_value:
                head, *_ = list(self._subs.sub(value))
                return model.Field(field.key, head), []
            case str() as value:
                subs = list(self._subs.sub(value))
                return model.Field(field.key, subs), []
            case list() | set() as value:
                result = self._subs.sub_many(*value)
                return model.Field(field.key, result), []
            case value:
                logging.warning("Unsupported replacement field value type(%s): %s", entry.key, type(value))
                return field, []
