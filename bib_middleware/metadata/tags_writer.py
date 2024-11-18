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

from jgdv.files.tags import SubstitutionFile
from bib_middleware.util.base_writer import BaseWriter

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class TagsWriter(BaseWriter):
    """
      Reduce tag set to a string.
      Pass in to_keywords=True to convert tags -> keywords for bibtex2html
    """

    @staticmethod
    def metadata_key():
        return "BM-tags-writer"

    def __init__(self, to_keywords=False, **kwargs):
        super().__init__(**kwargs)
        self._to_keywords = to_keywords

    def transform_entry(self, entry, library):
        match entry.get("tags"):
            case None:
                logging.warning("Entry has No Tags on write: %s", entry.key)
                entry.set_field(model.Field("tags", ""))
            case model.Field(value=val) if not bool(val):
                logging.warning("Entry has No Tags on write: %s", entry.key)
                entry.set_field(model.Field("tags", ""))
            case model.Field(value=set() as vals):
                entry.set_field(model.Field("tags", ",".join(sorted(vals))))


        if self._to_keywords:
            entry.set_field(model.Field("keywords", entry.get("tags").value))

        return entry

