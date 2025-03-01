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

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class NameWriter(ms.MergeNameParts):
    """ Converts NameParts -> str's """

    @staticmethod
    def metadata_key() -> str:
        return "BM-name-witer"

    def __init__(self):
        super().__init__(allow_inplace_modification=False)

    def _transform_field_value(self, name) -> List[str]:
        if not isinstance(name, list) and all(isinstance(n, NameParts) for n in name):
            raise ValueError("Expected a list of NameParts, got {}. ".format(name))

        return [self._merge_name(n) for n in name]

    def _merge_name(self, name):
        result = []
        if name.von:
            result.append(" ".join(name.von))
            result.append(" ")

        if name.last:
            result.append(" ".join(name.last))
            result.append(", ")

        if name.jr:
            result.append(" ".join(name.jr))
            result.append(", ")

        result.append(" ".join(name.first))

        full_name = "".join(result).removesuffix(", ").strip()
        return full_name
