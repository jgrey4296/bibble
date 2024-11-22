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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from bibtexparser.model import Library
from bibtexparser.middlewares import Middleware
from bibtexparser.splitter import Splitter

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class BibMiddlewareReader:
    """ A Refactored bibtexparser reader"""

    def __init__(self, stack:list[Middleware], lib_base:type=Library):
        self._middlewares     = stack
        self._lib_class : type = lib_base

    def read(self, source:str|pl.Path) -> Library:
        """ read source into a library """
        match source:
            case str():
                pass
            case pl.Path():
                source = source.read_text()

        return self.read_into(self._lib_class(), source)

    def read_into(self, lib:Library, source:str) -> Library:
        assert(isinstance(source, str))
        splitter       = Splitter(bibstr=source)
        library        = splitter.split(library=lib)
        transformed    = self._run_middlewares(library)
        return transformed


    def _run_middlewares(self, library) -> Library:
        for middlware in self._middlewares:
            library = middleware.transform(library=library)

        return library
