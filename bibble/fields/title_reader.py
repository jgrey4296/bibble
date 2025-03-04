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
from bibble.util.middlecore import IdenBlockMiddleware
from . import _interface as FAPI

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

    type Entry = model.Entry
    from bibtexparser.library import Library

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

##--|
@Proto(ReadTime_p)
class TitleCleaner(IdenBlockMiddleware):
    """
      strip whitespace from the title, and (optional) subtitle
    """

    @staticmethod
    def metadata_key():
        return "BM-title-reader"

    def on_read(self):
        return True

    def transform_entry(self, entry, library):
        match entry.get(FAPI.TITLE_K):
            case None:
                self._logger.warning("Entry has no title: %s", entry.key)
            case model.Field(value=str() as value):
                entry.set_field(model.Field(FAPI.TITLE_K, value.strip()))
            case _:
                pass

        match entry.get(FAPI.SUBTITLE_K):
            case None:
                pass
            case model.Field(value=str() as value):
                entry.set_field(model.Field(FAPI.SUBTITLE_K, value.strip()))
            case _:
                pass


        return entry

@Proto(ReadTime_p)
class TitleSplitter(IdenBlockMiddleware):
    """
      Split Title Into Title and Subtitle, If Subtitle Doesn't Exist Yet

    strips whitespace as well
    """

    @staticmethod
    def metadata_key():
        return "BM-subtitle-reader"

    def on_read(self):
        return True

    def transform_entry(self, entry:Entry, library:Library):
        match entry.get(FAPI.TITLE_K), entry.get(FAPI.SUBTITLE_K):
            case None, _:
                self._logging.warning("Entry has no title: %s", entry.key)
            case model.Field(value=title), model.Field(value=subtitle):
                entry.set_field(model.Field(FAPI.TITLE_K, title.strip()))
                entry.set_field(model.Field(FAPI.SUBTITLE_K, subtitle.strip()))
                pass
            case model.Field(value=value), None if FAPI.TITLE_SEP in value:
                title, *rest = value.split(FAPI.TITLE_SEP)
                entry.set_field(model.Field(FAPI.TITLE_K, title.strip()))
                entry.set_field(model.Field(FAPI.SUBTITLE_K, " ".join(rest).strip()))
            case _:
                pass

        return entry
