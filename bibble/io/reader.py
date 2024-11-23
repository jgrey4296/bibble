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

from bibtexparser.library import Library
from bibtexparser.middlewares.middleware import Middleware
from bibtexparser.splitter import Splitter

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class BibbleReader:
    """ A Refactored bibtexparser reader"""

    def __init__(self, stack:list[Middleware], lib_base:None|type=None):
        self._middlewares     = stack
        self._lib_class : type = lib_base or Library
        if not all([isinstance(x, Middleware) for x in self._middlewares]):
            raise TypeError("Bad middleware passed to Reader", stack)
        if not issubclass(self._lib_class, Library):
            raise TypeError("Bad library base pased to reader", lib_base)


    def read(self, source:str|pl.Path, *, into:None|Library=None, append:None|list[Middleware]=None) -> None|Library:
        """ read source and make a new library.
        if given 'into' lib, add the newly read entries into that libray as well
        """
        match source:
            case str():
                pass
            case pl.Path():
                try:
                    source = source.read_text()
                except UnicodeDecodeError as err:
                    printer.error("Unicode Error in File: %s, Start: %s", loc, err.start)
                    return None

        basic       : Library   = self._read_into(self._lib_class(), source)
        transformed : Library   = self._run_middlewares(basic, append=append)
        match into:
            case Library():
                into.add(transformed.blocks)
                return transformed
            case _:
                return transformed

    def _read_into(self, lib:Library, source:str) -> Library:
        assert(isinstance(source, str))
        splitter       = Splitter(bibstr=source)
        library        = splitter.split(library=lib)
        return library


    def _run_middlewares(self, library, *, append:None|list[Middleware]=None) -> Library:
        for middleware in self._middlewares:
            library = middleware.transform(library=library)

        match append:
            case None | []:
                return library
            case [*xs]:
                for middleware in xs:
                    library = middleware.transform(library=library)
                else:
                    return library
