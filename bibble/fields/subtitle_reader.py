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

        return entry
