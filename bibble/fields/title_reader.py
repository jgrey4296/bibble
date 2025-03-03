#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
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

# ##-- 3rd party imports
from jgdv import Proto
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)

# ##-- end 3rd party imports

from bibble._interface import ReadTime_p

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(ReadTime_p)
class TitleReader(BlockMiddleware):
    """
      strip whitespace from the title
    """

    @staticmethod
    def metadata_key():
        return "BM-title-reader"

    def __init__(self):
        super().__init__(True, True)

    def on_parse(self):
        return True

    def transform_entry(self, entry, library):
        match entry.get("title"):
            case None:
                logging.warning("Entry has no title: %s", entry.key)
            case model.Field(value=str() as value):
                entry.set_field(model.Field("title", value.strip()))
            case _:
                pass

        return entry

@Proto(ReadTime_p)
class SubTitleReader(BlockMiddleware):
    """
      Split Title Into Title and Subtitle, If Subtitle Doesn't Exist Yet
    """

    @staticmethod
    def metadata_key():
        return "BM-subtitle-reader"

    def __init__(self):
        super().__init__(True, True)

    def on_read(self):
        return True

    def transform_entry(self, entry, library):
        match entry.get("title"), entry.get("subtitle"):
            case None, _:
                logging.warning("Entry has no title: %s", entry.key)
            case model.Field(value=title), model.Field(value=subtitle):
                entry.set_field(model.Field("title", title.strip()))
                entry.set_field(model.Field("subtitle", subtitle.strip()))
                pass
            case model.Field(value=value), None if ":" in value:
                title, *rest = value.split(":")
                entry.set_field(model.Field("title", title.strip()))
                entry.set_field(model.Field("subtitle", " ".join(rest).strip()))
            case _:
                pass

        return entry
