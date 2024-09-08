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

##-- lib imports
import more_itertools as mitz
##-- end lib imports


import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SubTitleReader(BlockMiddleware):
    """
      split title into title and subtitle, if subtitle doesn't exist yet
    """

    @staticmethod
    def metadata_key():
        return "BM-subtitle-reader"

    def __init__(self):
        super().__init__(True, True)

    def transform_entry(self, entry, library):
        f_dict = entry.fields_dict
        if "subtitle" in f_dict:
            return entry
        if 'title' not in f_dict:
            return entry

        if ":" not in f_dict['title'].value:
            return entry

        parts = f_dict['title'].value.split(":")
        entry.set_field(model.Field("title", parts[0]))
        entry.set_field(model.Field("subtitle", ": ".join(parts[1:])))

        return entry
