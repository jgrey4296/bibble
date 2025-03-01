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

# from jgdv.files.tags import NameFile

class NameReader(ms.SplitNameParts):
    """ For use after stock "separatecoauthors",
    splits authors into nameparts
   """

    @staticmethod
    def metadata_key() -> str:
        return "BM-name-reader"

    def _transform_field_value(self, name) -> List[NameParts]:
        if not isinstance(name, list):
            raise ValueError(
                "Expected a list of strings, got {}. "
                "Make sure to use `SeparateCoAuthors` middleware"
                "before using `SplitNameParts` middleware".format(name)
            )
        result = []
        for n in name:
            wrapped = n.startswith("{") and n.endswith("}")
            result.append(parse_single_name_into_parts(n, strict=False))

        return result
