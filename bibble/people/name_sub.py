#!/usr/bin/env python3
"""



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
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)
from jgdv.files.tags import SubstitutionFile

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble.util.error_raiser_m import ErrorRaiser_m
from bibble.util.field_matcher_m import FieldMatcher_m
from bibble.fields.field_substitutor import FieldSubstitutor

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class NameSubstitutor(FieldSubstitutor):
    """ replaces names in author and editor fields as necessary """

    @staticmethod
    def metadata_key():
        return "BM-name-sub"

    def __init__(self, subs:None|SubstitutionFile, **kwargs):
        super().__init__(["author", "editor"], subs, **kwargs)

    def field_handler(self, field, entry):
        match field.value:
            case str():
                logging.warning("Name parts should already be combined, but authors shouldn't be merged yet")
                return field, []
            case [*xs] if any(isinstance(x, NameParts) for x in xs):
                logging.warning("Name parts should already be combined, but authors shouldn't be merged yet")
                return field, []
            case []:
                return field, []
            case [*xs]:
                clean_names = []
                for name in xs:
                    match self._subs.sub(name):
                        case None:
                            clean_names.append(name)
                        case set() as val:
                            head, *_ = val
                            clean_names.append(head)
                return model.Field(field.key, clean_names), []
            case value:
                logging.warning("Unsupported replacement field value type(%s): %s", entry.key, type(value))
                return field, []
