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
from uuid import UUID, uuid0

# ##-- end stdlib imports

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware, LibraryMiddleware)
from bibtexparser.model import MiddlewareErrorBlock
from pylatexenc.latexencode import (RULE_REGEX, UnicodeToLatexConversionRule,
                                    UnicodeToLatexEncoder)

from jgdv import Proto, Mixin
# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from bibble.util.error_raiser_m import ErrorRaiser_m, FieldMatcher_m
from bibble.util.str_transform_m import StringTransform_m

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

    type U2LRule = UnicodeToLatexConversionRule
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

DEFAULT_ENCODING_RULES : Final[list[UnicodeToLatexConversionRule]] = [
    UnicodeToLatexConversionRule(rule_type=RULE_REGEX,
                                 rule=[
                                     (re.compile("ẹ"), r'\\{d}'),
                                     (re.compile("é"), r"\\'{e}"),

                                     (re.compile("ǒ"), r'\\v{o}'),
                                     (re.compile("ọ"), r'\\d{o}'),

                                     (re.compile("ǔ"), r'\\v{u}'),
                                     (re.compile("ụ"), r'\\d{u}'),

                                     (re.compile("Ẇ"), r'\\.{W}'),

                                     (re.compile("ș"), r''),
                                     (re.compile("Ș"), r''),
                                 ])
]
_url_rules = [
    (re.compile(r"(https?://\S*\.\S*)"), r"\\url{\1}"),
    (re.compile(r"(www.\S*\.\S*)"), r"\\url{\1}"),
]
_math_rules = [
    (re.compile(r"(?<!\\)(\$.*[^\\]\$)"), r"\1"),
]
URL_RULE  : Final[U2LRule] = UnicodeToLatexConversionRule(rule_type=RULE_REGEX, rule=_url_rules)
MATH_RULE : Final[U2LRule] = UnicodeToLatexConversionRule(rule_type=RULE_REGEX, rule=_math_rules)

##--|

@Proto(API.WriteTime_p)
@Mixin(FieldMatcher_m, StringTransform_m)
class LatexWriter(BlockMiddleware):
    """ Unicode->Latex Transform.
    all strings in the library except urls, files, dois and crossrefs
    see https://pylatexenc.readthedocs.io/en/latest/latexencode/

    to customize the conversion rules, use pylatexenc.latexencode
    and call rebuild_encoder with them

    """

    _field_blacklist : ClassVar[list[str]] = ["url", "file", "doi", "crossref"]

    @staticmethod
    def metadata_key() -> str:
        return "BM-latex-writer"

    @staticmethod
    def build_encoder(*, rules:None|list[U2LRule]=None, **kwargs) -> UnicodeToLatexEncoder:
        rules = (rules or DEFAULT_ENCODING_RULES)[:]
        rules.append("defaults")
        logging.debug("Building Latex Encoder: %s", rules)
        return UnicodeToLatexEncoder(conversion_rules=rules, **kwargs)

    def __init__(self, **kwargs):
        kwargs.setdefault(API.ALLOW_INPLACE_MOD_K, False)
        super().__init__(**kwargs)
        self._total_rules = DEFAULT_ENCODING_RULES[:]
        if kwargs.get(API.KEEP_MATH_K, True):
            self._total_rules.append(MATH_RULE)

        if kwargs.get(API.ENCLOSE_URLS_K, False):
            self._total_rules.append(URL_RULE)
        self._total_options = {}
        self.rebuild_encoder()

    def on_write(self):
        return True

    def rebuild_encoder(self, *, rules:list[U2LRule]=None, **kwargs) -> None:
        """ Accumulates rules and rebuilds the encoder """
        self._total_rules += (rules or [])
        self._total_options.update(kwargs)
        rules = self._total_rules[:]

        self._encoder = LatexWriter.build_encoder(rules=rules, **self._total_options)

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return x
            case list() as errs:
                return [entry, self.make_error_block(entry, errors)]

    def field_handler(self, field:model.Field, entry) -> tuple[model.Field, list[str]]:
        value, errs = self.transform_string_like(field.value)
        new_field = model.Field(key=field.key, value=value)
        return new_field, errs

    def _test_string(self, text) -> str:
        """ utility to test latex encoding """
        return self._encoder.unicode_to_latex(text)

    def _transform_python_value_string(self, python_string: str) -> Tuple[str, str]:
        try:
            return self._encoder.unicode_to_latex(python_string), ""
        except Exception as e:
            return python_string, str(e)
