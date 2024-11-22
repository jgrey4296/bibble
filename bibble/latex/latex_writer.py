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
                    Iterable, Iterator, Mapping, Match, MutableMapping, Self,
                    Protocol, Sequence, Tuple, TypeAlias, TypeGuard, TypeVar,
                    cast, final, overload, runtime_checkable, Generator)
from uuid import UUID, uuid1

##-- end builtin imports

##-- lib imports
import more_itertools as mitz
##-- end lib imports

import bibtexparser
import bibtexparser.model as model
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.model import MiddlewareErrorBlock
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from pylatexenc.latexencode import UnicodeToLatexConversionRule, RULE_REGEX, UnicodeToLatexEncoder

from bibble.util.str_transform import StringTransform_m
from bibble.util.field_matcher import FieldMatcher_m
from bibble.util.error_raiser import ErrorRaiser_m

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
URL_RULE  : Final[UnicodeToLatexConversionRule] = UnicodeToLatexConversionRule(rule_type=RULE_REGEX, rule=[(re.compile(r"(https?://\S*\.\S*)"), r"\\url{\1}"), (re.compile(r"(www.\S*\.\S*)"), r"\\url{\1}")])
MATH_RULE : Final[UnicodeToLatexConversionRule] = UnicodeToLatexConversionRule(rule_type=RULE_REGEX, rule=[(re.compile(r"(?<!\\)(\$.*[^\\]\$)"), r"\1")])

class LatexWriter(FieldMatcher_m, StringTransform_m, BlockMiddleware):
    """ Unicode->Latex Transform.
    all strings in the library except urls, files, dois and crossrefs
    see https://pylatexenc.readthedocs.io/en/latest/latexencode/

    to customize the conversion rules, use pylatexenc.latexencode
    and call rebuild_encoder with them

    """

    _field_blacklist = ["url", "file", "doi", "crossref"]

    @staticmethod
    def metadata_key() -> str:
        return "BM-latex-writer"

    @staticmethod
    def build_encoder(*, rules:None|list[UnicodeToLatexConversionRule]=None, **kwargs) -> UnicodeToLatexEncoder:
        rules = (rules or DEFAULT_ENCODING_RULES)[:]
        rules.append("defaults")
        logging.debug("Building Latex Encoder: %s", rules)
        return UnicodeToLatexEncoder(conversion_rules=rules, **kwargs)

    def __init__(self, **kwargs):
        kwargs['allow_inplace_modification'] = kwargs.get('allow_inplace_modification', False)
        super().__init__(**kwargs)
        self._total_rules = DEFAULT_ENCODING_RULES[:]
        if kwargs.get('keep_math', True):
            self._total_rules.append(MATH_RULE)

        if kwargs.get('enclose_urls', False):
            self._total_rules.append(URL_RULE)
        self._total_options = {}
        self.rebuild_encoder()


    def rebuild_encoder(self, *, rules:list[UnicodeToLatexConversionRule]=None, **kwargs):
        """ Accumulates rules and rebuilds the encoder """
        self._total_rules += (rules or [])
        self._total_options.update(kwargs)
        rules = self._total_rules[:]

        self._encoder = LatexWriter.build_encoder(rules=rules, **self._total_options)

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

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
