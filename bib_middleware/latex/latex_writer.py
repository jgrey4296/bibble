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
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.model import MiddlewareErrorBlock
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from pylatexenc.latexencode import UnicodeToLatexConversionRule, RULE_REGEX, UnicodeToLatexEncoder

from bib_middleware.latex._str_transform import _PyStringTransformerMiddleware

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

class LatexWriter(_PyStringTransformerMiddleware):
    """ Unicode->Latex Transform.
    all strings in the library except urls, files, dois and crossrefs
    see https://pylatexenc.readthedocs.io/en/latest/latexencode/

    to customize the conversion rules, use pylatexenc.latexencode
    and call rebuild_encoder with them

    """

    _skip_fields = ["url", "file", "doi", "crossref"]

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
        errors = []
        for field in entry.fields:
            if any(x in field.key for x in self._skip_fields):
                continue
            match field.value:
                case str() as val if val.startswith("{"):
                    value, e = self._transform_python_value_string(val[1:-1])
                    errors.append(e)
                    field.value = "".join(["{", value,"}"])
                case str() as val:
                    field.value, e = self._transform_python_value_string(val)
                    errors.append(e)
                case ms.NameParts() as val:
                    field.value.first = self._transform_all_strings(val.first, errors)
                    field.value.last  = self._transform_all_strings(field.value.last, errors)
                    field.value.von   = self._transform_all_strings(field.value.von, errors)
                    field.value.jr    = self._transform_all_strings(field.value.jr, errors)
                case _:
                    logging.info(
                        f" [{self.metadata_key()}] Cannot python-str transform field {field.key}"
                        f" with value type {type(field.value)}"
                    )

        errors = [e for e in errors if e != ""]
        if len(errors) > 0:
            errors = bexp.PartialMiddlewareException(errors)
            return MiddlewareErrorBlock(block=entry, error=errors)
        else:
            return entry

    def _test_string(self, text) -> str:
        return self._encoder.unicode_to_latex(text)

    def _transform_python_value_string(self, python_string: str) -> Tuple[str, str]:
        try:
            return self._encoder.unicode_to_latex(python_string), ""
        except Exception as e:
            return python_string, str(e)
