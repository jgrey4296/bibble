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

from jgdv.files.tags import TagFile

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TagsReader(BlockMiddleware):
    """
      Read Tag strings, split them into a set, and keep track of all mentioned tags
      By default the classvar _all_tags is cleared on init, pass clear=False to not
    """
    _all_tags : TagFile = TagFile()

    @staticmethod
    def metadata_key():
        return "BM-tags-reader"

    @staticmethod
    def tags_to_str():
        return str(TagsReader._all_tags)

    def __init__(self, clear=True):
        super().__init__(True, True)
        if clear:
            TagsReader._all_tags = TagFile()

    def transform_entry(self, entry, library):
        match entry.get("tags"):
            case None:
                logging.warning("Entry has no Tags on parse: %s", entry.key)
                entry.set_field(model.Field("tags", set()))
            case model.Field(value=val) if not bool(val):
                logging.warning("Entry has no Tags on parse: %s", entry.key)
                entry.set_field(model.Field("tags", set()))
            case model.Field(value=str() as val):
                as_set = set(val.split(","))
                entry.set_field(model.Field("tags", as_set))
                TagsReader._all_tags.update(as_set)

        return entry
