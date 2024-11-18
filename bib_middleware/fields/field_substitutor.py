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

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from jgdv.files.tags import SubstitutionFile
from bib_middleware.util.base_writer import BaseWriter
from bib_middleware.util.field_matcher import FieldMatcher_m
from bib_middleware.util.error_raiser import ErrorRaiser_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class FieldSubstitutor(ErrorRaiser_m, FieldMatcher_m, BaseWriter):
    """
      For a given field(s), and a given jgdv.SubstitutionFile,
    replace the field value as necessary in each entry.

    If force_single_value is True, only the first replacement will be used,
    others will be discarded

    """

    @staticmethod
    def metadata_key():
        return "BM-field-sub"

    def __init__(self, field:str, subs:SubstitutionFile, force_single_value:bool=False, **kwargs):
        super().__init__(**kwargs)
        self._target_field       = field
        self._subs               = subs
        self._force_single_value = force_single_value


    def transform_entry(self, entry, library):
        entry, errors = self.match_on_field(entry, library)
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
