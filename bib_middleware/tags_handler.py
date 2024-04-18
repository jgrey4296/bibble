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

##-- logging
logging = logmod.getLogger(__name__)
printer = logmod.getLogger("doot._printer")
##-- end logging

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from jgdv.files.tags.base import TagFile
from bib_middleware.base_writer import BaseWriter


class TagsReader(BlockMiddleware):
    """
      Read Tag strings, split them into a set, and keep track of all mentioned tags
      By default the classvar _all_tags is cleared on init, pass clear=False to not
    """
    _all_tags : TagFile = TagFile()

    @staticmethod
    def metadata_key():
        return "jg-tags-reader"

    @staticmethod
    def tags_to_str():
        return str(TagsReader._all_tags)

    def __init__(self, clear=True):
        super().__init__(True, True)
        if clear:
            TagsReader._all_tags = TagFile()

    def transform_entry(self, entry, library):
        for field in entry.fields:
            if field.key == "tags":
                field.value = set(field.value.split(","))
                TagsReader._all_tags.update(field.value)

        return entry

class TagsWriter(BaseWriter):
    """
      Reduce tag set to a string
    """

    @staticmethod
    def metadata_key():
        return "jg-tags-writer"

    def transform_entry(self, entry, library):
        for field in entry.fields:
            if field.key == "tags":
                field.value = ",".join(sorted(field.value))

        return entry
