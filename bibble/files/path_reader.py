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


import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts
from bibble.util.field_matcher_m import FieldMatcher_m
from bibble.util.error_raiser_m import ErrorRaiser_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class PathReader(FieldMatcher_m, BlockMiddleware):
    """
      Convert file paths in bibliography to pl.Path's, expanding relative paths according to lib_root
    """

    _field_whitelist = ["file"]

    @staticmethod
    def metadata_key():
        return "BM-path-reader"

    def __init__(self, lib_root:pl.Path=None, **kwargs):
        super().__init__(**kwargs)
        self._lib_root                   = lib_root

    def transform_entry(self, entry, library):
        entry, errors = self.match_on_fields(entry, library)
        return entry

    def field_handler(self, field, entry):
        base = pl.Path(field.value)
        match base.parts[0]:
            case "/":
                field.value = base
            case "~":
                field.value = base.expanduser().absolute()
            case _:
                field.value = self._lib_root / base

        if not field.value.exists():
            logging.warning("On Import file does not exist: %s", field.value)

        return field, []
