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
from jgdv import Proto, Mixin
import bibtexparser
import bibtexparser.model as model
from bibtexparser.library import Library
from bibtexparser import exceptions as bexp
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware, LibraryMiddleware)
from bibtexparser.model import MiddlewareErrorBlock
from pylatexenc.latex2text import (LatexNodes2Text, MacroTextSpec,
                                   get_default_latex_context_db)

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from bibble.util.mixins import ErrorRaiser_m, FieldMatcher_m
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

    type Entry = model.Entry
    type Block = model.Block
    type Field = model.Field
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

DEFAULT_DECODE_RULES : Final[dict] = {
    "BM-reader-simplify-urls" : MacroTextSpec("url", simplify_repl="%s"),
}

##--|

@Proto(API.ReadTime_p)
@Mixin(ErrorRaiser_m, FieldMatcher_m, StringTransform_m)
class LatexReader(BlockMiddleware):
    """ Latex->unicode transform.
    all strings in the library, except urls, files, doi's and crossrefs
    """

    _field_blacklist : ClassVar[list[str]] = ["url", "file", "doi", "crossref"]

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

    def on_read(self):
        return True

    def rebuild_decoder(self, *, rules:dict=None, **kwargs) -> None:
        self._total_rules.update(rules or {})
        self._total_options.update(kwargs)
        self._decoder = LatexReader.build_decoder(rules=self._total_rules, **self._total_options)

    def transform_entry(self, entry: Entry, library: Library) -> Block:
        match self.match_on_fields(entry, library):
            case model.Entry() as x:
                return x
            case list() as errs:
                return [entry, self.make_error_block(entry, errs)]

    def field_handler(self, field:Field, entry) -> tuple[Field, list[str]]:
        cleaned, errs = self.transform_string_like(field.value)
        new_field = model.Field(key=field.key, value=cleaned)
        return new_field, errs

    def _test_string(self, text:str) -> str:
        """ utility to test decoding """
        return self._decoder.latex_to_text(text)

    def _transform_python_value_string(self, python_string: str) -> tuple[str, str]:
        """Transforms a python string to a latex string

        Returns:
            Tuple[str, str]: The transformed string and a possible error message
        """
        try:
            return self._decoder.latex_to_text(python_string), ""
        except Exception as e:
            return python_string, str(e)
