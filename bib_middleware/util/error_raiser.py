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
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.model import MiddlewareErrorBlock
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class ErrorRaiser_m:
    """ Mixin for easily raising middleware errors """

    def maybe_error_block(self, entry:Entry, errs:list[str]) -> None|MiddlewareErrorBlock:
        errors = [e for e in errors if e != ""]
        if not bool(errors):
            return None

        errors = bexp.PartialMiddlewareException(errors)
        return MiddlewareErrorBlock(block=entry, error=errors)
