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
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import NameParts
from bibtexparser import model

# ##-- end 3rd party imports

# ##-- types
# isort: off
import abc
import collections.abc
from typing import TYPE_CHECKING, cast, assert_type, assert_never
from typing import Generic, NewType
# Protocols:
from typing import Protocol, runtime_checkable
# Typing Decorators:
from typing import no_type_check, final, override, overload

if TYPE_CHECKING:
    from jgdv import Maybe, Either, Result
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

    type String  = model.String
    type StrLike = str|NameParts|list|set|String
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging
OBRACE : Final[str] = "{"
CBRACE : Final[str] = "}"

##--|
class StringTransform_m:
    """ Mixin for handling transform of strings
    refactored from bibtexparser middlewares.

    Implement _transform_raw_str,
    and call transform_string_like
    """

    def _transform_all_strings(self, vals:list[str]) -> Result[list[str], ValueError]:
        """Called for every python (value, not key) string found on Entry and String blocks
        Errors are modified in place.
        """
        res  = []
        errs = []
        for s in vals:
            match self._transform_raw_str(s):
                case ValueError() as x:
                    errs += x.args
                case str() as x:
                    res.append(x)
        else:
            if bool(errs):
                return ValueError(*errs)

            return res


    def _transform_nameparts(self, value:NameParts) -> Result[NameParts, ValueError]:

        val.first = self._transform_all_strings(val.first, errors)
        val.last  = self._transform_all_strings(val.last,  errors)
        val.von   = self._transform_all_strings(val.von,   errors)
        val.jr    = self._transform_all_strings(val.jr,    errors)

    def transform_strlike(self, value:StrLike) -> Result[StrLike,ValueError]:
        """
        Transform str likes: str,s
        """
        match val:
            case model.String(value=str() as sval):
                match self.transform_strlike(sval):
                    case ValueError() as err:
                        res = err
                    case str() as x:
                        val.value = x
                        res = val
            case str() as x if x.startswith(OBRACE) and x.endswith(CBRACE):
                match self._transform_braced_str(val[1:-1]):
                    case ValueError() as err:
                        res = err
                    case str() as x:
                        res = "".join([OBRACE, x, CBRACE])
            case str():
                res = self._transform_raw_str(field.value)
            case NameParts() as np:
                res = self._transform_nameparts(np)
            case list() as vals:
                res = []
                errs = []
                for x in vals:
                    match self.transform_strlike(x):
                        case ValueError() as err:
                            errs += err.args
                        case str() as x:
                            res.append(x)
                else:
                    if bool(errs):
                        res = ValueError(*errs)
            case set() as vals:
                res = []
                errs = []
                for x in vals:
                    match self.transform_strlike(x):
                        case ValueError() as err:
                            errs += err.args
                        case str() as x:
                            res.append(x)
                else:
                    if bool(errs):
                        res = ValueError(*errs)
                    else:
                        res = set(res)
            case x:
                logging.info(
                    f" [{self.metadata_key()}] Cannot python-str transform: {val}"
                    f" with value type {type(x)}"
                )
                res = x

        return res

