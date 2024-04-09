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

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

class LatexReader(ms.LatexDecodingMiddleware):
    """ Latex-Encodes all strings in the library, except urls, files, doi's and crossrefs """

    _skip_fields = ["url", "file", "doi", "crossref"]

    @staticmethod
    def metadata_key() -> str:
        return "jg-latex-reader"

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        errors = []
        for field in entry.fields:
            if any(x in field.key for x in self._skip_fields):
                continue
            if isinstance(field.value, str):
                field.value, e = self._transform_python_value_string(field.value)
                errors.append(e)
            elif isinstance(field.value, ms.NameParts):
                field.value.first = self._transform_all_strings(
                    field.value.first, errors
                )
                field.value.last = self._transform_all_strings(field.value.last, errors)
                field.value.von = self._transform_all_strings(field.value.von, errors)
                field.value.jr = self._transform_all_strings(field.value.jr, errors)
            else:
                logging.info(
                    f" [{self.metadata_key()}] Cannot python-str transform field {field.key}"
                    f" with value type {type(field.value)}"
                )

        errors = [e for e in errors if e != ""]
        if len(errors) > 0:
            errors = ms.PartialMiddlewareException(errors)
            return ms.MiddlewareErrorBlock(block=entry, error=errors)
        else:
            return entry

class LatexWriter(ms.LatexEncodingMiddleware):
    """ Latex-Encodes all strings in the library except urls, files, dois and crossrefs """

    _skip_fields = ["url", "file", "doi", "crossref"]

    @staticmethod
    def metadata_key() -> str:
        return "jg-latex-writer"

    def __init__(self, **kwargs):
        super().__init__(**kwargs, allow_inplace_modification=False)

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        errors = []
        for field in entry.fields:
            if any(x in field.key for x in self._skip_fields):
                continue
            match field.value:
                case str() as val if val.startswith("{"):
                    value, e = self._transform_python_value_string(val[1:-1])
                    errors.append(e)
                    field.value = "".join(["{", value,"}"])
                case str() as val:
                    field.value, e = self._transform_python_value_string(val)
                    errors.append(e)
                case ms.NameParts() as val:
                    field.value.first = self._transform_all_strings(val.first, errors)
                    field.value.last  = self._transform_all_strings(field.value.last, errors)
                    field.value.von   = self._transform_all_strings(field.value.von, errors)
                    field.value.jr    = self._transform_all_strings(field.value.jr, errors)
                case _:
                    logging.info(
                        f" [{self.metadata_key()}] Cannot python-str transform field {field.key}"
                        f" with value type {type(field.value)}"
                    )

        errors = [e for e in errors if e != ""]
        if len(errors) > 0:
            errors = ms.PartialMiddlewareException(errors)
            return ms.MiddlewareErrorBlock(block=entry, error=errors)
        else:
            return entry
