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

from bibble.util.error_raiser_m import ErrorRaiser_m
from bibble.util.field_matcher_m import FieldMatcher_m

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class CleanUrls(ErrorRaiser_m, FieldMatcher_m, BlockMiddleware):
    """ Strip unnecessary doi and dblp prefixes from urls  """

    _field_whiteist = ["doi", "url", "ee"]

    @staticmethod
    def metadata_key():
        return "BM-clean-urls"

    def transform_entry(self, entry, library):
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field, entry):
        fields = []
        match field.value:
            case str() as value if value.startswith("https://doi.org") and (name == "doi" or "doi" not in entry):
                clean = value.removeprefix("https://doi.org/")
                fields.append(model.Field("doi", clean))
            case str() as value if value.startswith("db/") and "bibsource" not in entry:
                url = "".join(["https://dblp.org/", url])
                fields.append(model.Field("biburl", url))
                fields.append(model.Field("bibsource", "dblp computer science bibliography, https://dblp.org"))
            case str() as value if field.key == "ee" and "url" not in entry:
                fields.append(model.Field("url", value))
                fields.append(model.Field("ee", ""))

        return entry
