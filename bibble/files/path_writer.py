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
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble.util.error_raiser_m import ErrorRaiser_m
from bibble.util.field_matcher_m import FieldMatcher_m

# ##-- end 1st party imports

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

class PathWriter(ErrorRaiser_m, FieldMatcher_m, BlockMiddleware):
    """
      Relativize library paths back to strings
    """

    _field_whitelist = ["file"]

    @staticmethod
    def metadata_key():
        return "BM-path-writer"

    def __init__(self, lib_root:pl.Path=None, **kwargs):
        super().__init__(**kwargs)
        self._lib_root = lib_root

    def transform_entry(self, entry, library):
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field, entry):
        errors = []
        match field.value:
            case str():
                pass
            case pl.Path() as val if not val.exists():
                logging.warning("On Export file does not exist: %s", val)
            case pl.Path() as val:
                try:
                    as_str = val.relative_to(self._lib_root)
                    field.value = as_str
                except ValueError:
                    field.value = str(val)
                    errors.append(f"Failed to Relativize path (entry.key): val")

        return field, errors
