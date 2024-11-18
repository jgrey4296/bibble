#!/usr/bin/env python3
"""



"""

from __future__ import annotations

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
                    Generic, Iterable, Iterator, Mapping, Match, Self,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

import bibtexparser
import bibtexparser.model as model
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.model import MiddlewareErrorBlock
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class FieldMatcher_m:
    """ Mixin to process fields if their key matchs a regex
    defaults are in the attrs _field_blacklist and _field_whitelist, _entry_whitelist
    Call set_field_matchers to extend.
    Call match_on_fields to start.
    Call maybe_skip_entry to compare the lowercase entry type to a whitelist
    Implement field_handler to use.

    match_on_fields calls entry.set_field on the field_handlers result
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_field_matchers([],[])

    def set_field_matchers(self, white:list[str], black:list[str], keep_default=True) -> Self:
        """ sets the blacklist and whitelist regex's
        returns self to help in building parse stacks
        """
        match keep_default, getattr(self, "_field_blacklist", []):
            case _, [] if not bool(black):
                self._field_black_re = re.compile("^$")
            case _, []:
                self._field_black_re = re.compile("|".join(list(black)))
            case False, _:
                self._field_black_re = re.compile("|".join(list(black)))
            case True, [*xs] as defs:
                self._field_black_re = re.compile("|".join(list(black) + defs))

        match keep_default, getattr(self, "_field_whitelist", []):
            case _, [] if not bool(white):
                self._field_white_re = re.compile(".")
            case _, []:
                self._field_white_re = re.compile("|".join(list(white)))
            case False, _:
                self._field_white_re = re.compile("|".join(list(white)))
            case True, [*xs] as defs:
                self._field_white_re = re.compile("|".join(list(white) + defs))

        return self


    def match_on_fields(self, entry: Entry, library: Library) -> tuple[Entry, list[str]]:
        errors = []
        whitelist, blacklist = self._field_white_re, self._field_black_re
        for field in entry.fields:
            res = None
            match field:
                case model.Field(key=key) if blacklist.match(key):
                    continue
                case model.Field(key=key) if whitelist.match(key):
                    res, errs = self.field_handler(field, entry)
                    errors += errs

            match res:
                case model.Field():
                    entry.set_field(res)
                case [*xs]:
                    for x in xs:
                        entry.set_field(x)

        else:
            return entry, errors


    def field_handler(self, field:model.Field, entry:Entry) -> tuple[model.Field|list[model.Field], list[str]]:
        raise NotImplementedError("Implement the field handler")

    def should_skip_entry(self, entry, library) -> bool:
        return entry.entry_type.lower() not in getattr(self, "_entry_whitelist", [])
