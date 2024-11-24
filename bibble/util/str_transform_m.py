#!/usr/bin/env python3
"""


See EOF for license/metadata/notes as applicable
"""

from __future__ import annotations

import abc
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

from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class StringTransform_m:
    """ Mixin for handling transform of strings
    extracted from bibtexparser middlewares.

    Implement _transform_python_value_string,
    and call transform_string_like
    """

    def _transform_python_value_string(self, python_string:str) -> Tuple[str, str]:
        """Called for every python (value, not key) string found on Entry and String blocks.

        Returns:
            - The transformed string, if the transformation was successful
            - An error message, if any, or an empty string
        """
        raise NotImplementedError("called abstract method")

    # docstr-coverage: inherited
    def _transform_all_strings(self, list_of_strings: List[str], errors: List[str]) -> List[str]:
        """Called for every python (value, not key) string found on Entry and String blocks"""
        res = []
        for s in list_of_strings:
            r, e = self._transform_python_value_string(s)
            res.append(r)
            errors.append(e)
        return res

    # docstr-coverage: inherited
    def transform_string_like(self, value:str|NameParts|list|set) -> tuple[Any,list[str]]:
        errors = []
        match val:
            case str() if val.startswith("{"):
                val, e = self._transform_python_value_string(val[1:-1])
                val = "".join(["{", value,"}"])
                errors.append(e)
            case str():
                val, e = self._transform_python_value_string(field.value)
                errors.append(e)
            case NameParts():
                val.first = self._transform_all_strings(val.first, errors)
                val.last  = self._transform_all_strings(val.last,  errors)
                val.von   = self._transform_all_strings(val.von,   errors)
                val.jr    = self._transform_all_strings(val.jr,    errors)
            case _:
                pass

        errors = [e for e in errors if e != ""]
        return val, errors

    # docstr-coverage: inherited
    def transform_string(self, string: String, library: "Library") -> Block:
        if isinstance(string.value, str):
            string.value = self._transform_python_value_string(string.value)
        else:
            logging.info(
                f" [{self.metadata_key()}] Cannot python-str transform string {string.key}"
                f" with value type {type(string.value)}"
            )
        return string
