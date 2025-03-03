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
from jgdv import Mixin
from bibtexparser.library import Library
from bibtexparser.middlewares.middleware import Middleware
from bibtexparser.splitter import Splitter

# ##-- end 3rd party imports

from bibble import _interface as API
from bibble.util.mixins import MiddlewareValidator_m

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
    from jgdv import Maybe
    from typing import Final
    from typing import ClassVar, Any, LiteralString
    from typing import Never, Self, Literal
    from typing import TypeGuard
    from collections.abc import Iterable, Iterator, Callable, Generator
    from collections.abc import Sequence, Mapping, MutableMapping, Hashable

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Mixin(MiddlewareValidator_m)
class BibbleReader:
    """ A Refactored bibtexparser reader"""
    _middlewares : list[Middleware]
    _lib_class   : type[Library]

    def __init__(self, stack:list[Middleware], lib_base:Maybe[type]=None):
        self._middlewares      = stack
        self._lib_class : type = lib_base or Library

        self.exclude_middlewares(API.ReadTime_p)
        if not issubclass(self._lib_class, Library):
            raise TypeError("Bad library base pased to reader", lib_base)

    def read(self, source:str|pl.Path, *, into:Maybe[Library]=None, append:Maybe[list[Middleware]]=None) -> Maybe[Library]:
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
                    logging.exception("Unicode Error in File: %s, Start: %s", source, err.start)
                    return None
            case x:
                raise TypeError(type(x))

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

    def _run_middlewares(self, library:Library, *, append:Maybe[list[Middleware]]=None) -> Library:
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
