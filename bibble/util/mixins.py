#!/usr/bin/env python3
"""

"""
# ruff: noqa:

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import atexit#  for @atexit.register
import collections
import contextlib
import datetime
import enum
import faulthandler
import functools as ftz
import hashlib
import itertools as itz
import logging as logmod
import pathlib as pl
import re
import time
import types
from copy import deepcopy
from uuid import UUID, uuid1
from weakref import ref

# ##-- end stdlib imports

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware, Middleware)
from bibtexparser.model import MiddlewareErrorBlock

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble import _interface as API

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
    from jgdv import Maybe, Either
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

# Vars:

# Body:

class MiddlewareValidator_m:
    """ For ensuring the middlewares of a reader/writer  are appropriate,
    by excluding certain middlewares.
    """

    def exclude_middlewares(self, proto:Protocol):
        if not issubclass(proto, Protocol):
            raise TypeError("Tried to validate middlewares with a non-protocol", proto)
        failures = []
        for middle in self._middlewares:
            # note: no 'not'.
            if isinstance(middle, proto):
                failures.append(middle)
            elif not isinstance(middle, Middleware):
                failures.append(middle)
        else:
            if bool(failures):
                raise TypeError("Bad middlewares", failures)

class ErrorRaiser_m:
    """ Mixin for easily combining middleware errors into a block"""

    def make_error_block(self, entry:API.Entry, errs:list[str]) -> MiddlewareErrorBlock:
        errors = [e for e in errs if e != ""]
        if not bool(errors):
            raise ValueError("No Errors to wrap")

        errors = bexp.PartialMiddlewareException(errors)
        return MiddlewareErrorBlock(block=entry, error=errors)

class FieldMatcher_m:
    """ Mixin to process fields if their key matchs a regex
    defaults are in the attrs _field_blacklist and _field_whitelist, _entry_whitelist
    Call set_field_matchers to extend.
    Call match_on_fields to start.
    Call maybe_skip_entry to compare the lowercase entry type to a whitelist
    Implement field_handler to use.

    match_on_fields calls entry.set_field on the field_handlers result
    """

    def set_field_matchers(self, white:list[str]=None, black:list[str]=None, keep_default=True) -> Self:
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

    def match_on_fields(self, entry: API.Entry, library: API.Library) -> Either[API.Entry, list[str]]:
        errors = []
        whitelist, blacklist = self._field_white_re, self._field_black_re
        for field in entry.fields:
            res = None
            match field:
                case model.Field(key=key) if whitelist.match(key) and not blacklist.match(key):
                    res, errs = self.field_handler(field, entry)
                    errors += errs

            match res:
                case model.Field():
                    entry.set_field(res)
                case [*xs]:
                    for x in xs:
                        entry.set_field(x)

        else:
            if bool(errors):
                return errors
            return entry

    def field_handler(self, field:API.Field, entry:API.Entry) -> API.FieldReturn:
        raise NotImplementedError("Implement the field handler")

class EntrySkipper_m:

    def set_entry_whitelist(self, whitelist:list[str]) -> None:
        self._entry_whitelist = whitelist

    def should_skip_entry(self, entry:API.Entry, library:API.Library) -> bool:
        return entry.entry_type.lower() not in getattr(self, "_entry_whitelist", [])
