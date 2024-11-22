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

from pylatexenc.latex2text import LatexNodes2Text, MacroTextSpec, get_default_latex_context_db

from bibble.util.str_transform import StringTransform_m
from bibble.util.field_matcher import FieldMatcher_m
from bibble.util.error_raiser import ErrorRaiser_m
##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

DEFAULT_DECODE_RULES : Final[dict] = {
    "BM-reader-simplify-urls" : MacroTextSpec("url", simplify_repl="%s"),
}

class LatexReader(ErrorRaiser_m, FieldMatcher_m, StringTransform_m, BlockMiddleware):
    """ Latex->unicode transform.
    all strings in the library, except urls, files, doi's and crossrefs
    """

    _field_blacklist = ["url", "file", "doi", "crossref"]

    @staticmethod
    def metadata_key() -> str:
        return "BM-latex-reader"

    @staticmethod
    def build_decoder(*, rules:None|dict=None, **kwargs) -> LatexNodes2Text:
        context_db = get_default_latex_context_db()
        rules         = rules or DEFAULT_DECODE_RULES.copy()
        logging.debug("Building Latex Decoder: %s", rules)
        for x, y in rules.items():
            match y:
                case list() if all(isinstance(y2, MacroTextSpec) for y2 in y):
                    context_db.add_context_category(x, prepend=True, macros=y)
                case MacroTextSpec():
                     context_db.add_context_category(x, prepend=True, macros=[y])
                case _:
                    raise TypeError("Bad Decode Rules Specified", y)

        return LatexNodes2Text(latex_context=context_db, **kwargs)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._total_rules = DEFAULT_DECODE_RULES
        self._total_options = {
            "keep_braced_groups" : kwargs.get('keep_braced_groups', False),
            "math_mode"          : kwargs.get('math_mode', 'text'),
        }
        self.rebuild_decoder()


    def rebuild_decoder(self, *, rules:dict=None, **kwargs):
        self._total_rules.update(rules or {})
        self._total_options.update(kwargs)
        self._decoder = LatexReader.build_decoder(rules=self._total_rules, **self._total_options)

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        entry, errors = self.match_on_fields(entry, library)
        match self.maybe_error_block(entry, errors):
            case None:
                return entry
            case errblock:
                return errblock

    def field_handler(self, field:model.Field, entry) -> tuple[model.Field, list[str]]:
        cleaned, errs = self.transform_string_like(field.value)
        new_field = model.Field(key=field.key, value=cleaned)
        return new_field, errs


    def _test_string(self, text) -> str:
        """ utility to test decoding """
        return self._decoder.latex_to_text(text)

    def _transform_python_value_string(self, python_string: str) -> Tuple[str, str]:
        """Transforms a python string to a latex string

        Returns:
            Tuple[str, str]: The transformed string and a possible error message
        """
        try:
            return self._decoder.latex_to_text(python_string), ""
        except Exception as e:
            return python_string, str(e)
