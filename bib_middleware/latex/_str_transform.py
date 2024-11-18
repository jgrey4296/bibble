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

class _PyStringTransformerMiddleware(BlockMiddleware, abc.ABC):
    """Abstract utility class allowing to modify python-strings
    extracted from bibtexparser middlewares
    """

    @abc.abstractmethod
    def _transform_python_value_string(self, python_string: str) -> Tuple[str, str]:
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
    def transform_entry(self, entry: Entry, library: Library) -> Block:
        errors = []
        for field in entry.fields:
            if isinstance(field.value, str):
                field.value, e = self._transform_python_value_string(field.value)
                errors.append(e)
            elif isinstance(field.value, NameParts):
                field.value.first = self._transform_all_strings(field.value.first, errors)
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
            errors = PartialMiddlewareException(errors)
            return MiddlewareErrorBlock(block=entry, error=errors)
        else:
            return entry

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
