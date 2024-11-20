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
from collections import defaultdict
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match, Self,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

from bibtexparser.library import Library
from bibtexparser.middlewares import BlockMiddleware

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class BibMiddlewareLibrary(Library):
    """ A library with a key value store for extra info
    Also tracks the individual files used as source
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._kv_store    = defaultdict(set)
        self.source_files = set()

    def add_sublibrary(self, lib:Library, source=None) -> Self:
        """ Merge entries, kv_store and source files into this library
        will *overwrite* existing kv_store keys
        """
        if source:
            self.source_files.add(source)

        match lib:
            case BibMiddlewareLibrary():
                self.add(lib.entries)
                self.source_files.update(lib.source_files)
                for k,v in lib._kv_store.items():
                    self.store_meta_value(k, v)
            case Library():
                self.add(lib.entries)
            case _:
                raise TypeError("Bad update sublibrary")



    def store_meta_value(self, key:str|BlockMiddleware, value:Any):
        match key:
            case str():
                pass
            case BlockMiddleware():
                key = key.metadata_key()

        match value:
            case list() | set:
                self._kv_store[key].update(value)
            case _:
                self._kv_store[key] = value

    def get_meta_value(self, key) -> set|Any:
        match key:
            case str():
                return self._kv_store[key]
            case BlockMiddleware():
                return self._kv_store[key.metadata_key()]
