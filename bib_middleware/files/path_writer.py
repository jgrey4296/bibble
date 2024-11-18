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
from bib_middleware.util.base_writer import BaseWriter
from bib_middleware.util.field_matcher import FieldMatcher_m
from bib_middleware.util.error_raiser import ErrorRaiser_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class PathWriter(ErrorRaiser_m, FieldMatcher_m, BaseWriter):
    """
      Relativize library paths back to strings
    """

    _field_whitelist = ["file"]

    @staticmethod
    def metadata_key():
        return "BM-path-writer"

    def __init__(self, lib_root:pl.Path=None, **kwargs):
        super().__init__(**kwargs)
        self._lib_root = lib_root

    def transform_entry(self, entry, library):
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field, entry):
        errors = []
        match field.value:
            case str():
                pass
            case pl.Path() as val if not val.exists():
                logging.warning("On Export file does not exist: %s", val)
            case pl.Path() as val:
                try:
                    as_str = val.relative_to(self._lib_root)
                    field.value = as_str
                except ValueError:
                    field.value = str(val)
                    errors.append(f"Failed to Relativize path (%s): %s ", entry.key, val)

        return field, errors
