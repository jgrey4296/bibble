#!/usr/bin/env python3
"""

"""
# mypy: disable-error-code="attr-defined"

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
from copy import deepcopy
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import jgdv
from jgdv import Proto, Mixin
from jgdv.debugging.timeblock_ctx import TimeBlock_ctx
from bibtexparser import model
from bibtexparser.model import MiddlewareErrorBlock

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble import _interface as API
from . import _interface as API_W
from bibble.util.mixins import MiddlewareValidator_m
from bibble.model import MetaBlock
from bibble.util import PairStack

from ._util import Runner_m
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

    from bibtexparser.library import Library
    from bibtexparser.writer import BibtexFormat

    type Middleware = API.Middleware_p | API.BidirectionalMiddleware_p
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class _VisitEntry_m:

    def make_header(self, library, file:None|pl.Path=None) -> list[str]:
        return []

    def make_footer(self, library, file:None|pl.Path=None) -> list[str]:
        return []

    def visit(self, block) -> list[str]:
        match block:
            case x if isinstance(x, API.CustomWriteBlock_p):
                assert(hasattr(x, "visit"))
                return x.visit(self)
            case MetaBlock():
                return []
            case model.Entry():
                return self.visit_entry(block)
            case model.String():
                return self.visit_string(block)
            case model.Preamble():
                return self.visit_preamble(block)
            case model.ExplicitComment():
                return self.visit_expl_comment(block)
            case model.ImplicitComment():
                return self.visit_impl_comment(block)
            case model.ParsingFailedBlock():
                return self.visit_failed_block(block)
            case MiddlewareErrorBlock():
                return []
            case _:
                raise ValueError(f"Unknown block type: {type(block)}")

class _Visitors_m:

    def visit_entry(self, block:model.Entry) -> list[str]:
        res = ["@", block.entry_type, "{", block.key, ",\n"]
        field: model.Field
        for i, field in enumerate(block.fields):
            res.append(self._align_key(field.key))
            res.append(field.value)
            if self.format.trailing_comma or i < len(block.fields) - 1:
                res.append(",")
                res.append("\n")
        else:
            res.append("}\n")
            return res

    def visit_string(self, block:model.String) -> list[str]:
        return [
            "@string{",
            block.key,
            self._value_sep,
            block.value,
            "}\n",
        ]

    def visit_preamble(self, block:model.Preamble) -> list[str]:
        return [f"@preamble{{{block.value}}}\n"]

    def visit_impl_comment(self, block:model.ImplicitComment) -> list[str]:
        # Note: No explicit escaping is done here - that should be done in middleware
        return [block.comment, "\n"]

    def visit_expl_comment(self, block:model.ExplicitComment) -> list[str]:
        return ["@comment{", block.comment, "}\n"]

    def visit_failed_block(self, block:model.ParsingFailedBlock) -> list[str]:
        format_line            = self.format.parsing_failed_comment
        lines                  = len(block.raw.splitlines())
        err                    = f"<{block.error.__class__.__name__}> : {block.error}"
        parsing_failed_comment = format_line.format(n=lines, err=err)
        return [parsing_failed_comment, "\n",
                block.raw, "\n",
                API_W.FAIL_END, "\n"]
    ##--|

@Proto(jgdv.protos.Visitor_p, API.Writer_p)
@Mixin(_VisitEntry_m, _Visitors_m, Runner_m, MiddlewareValidator_m)
class BibbleWriter:
    """ A Refactored bibtexparser writer
    Uses visitor pattern

    Note: visit method are responsible for new lines
    """
    _value_sep             : str
    _value_column          : Maybe[int]
    _middlewares           : list[Middleware]
    format                 : BibtexFormat

    def __init__(self, stack:PairStack|list[Middleware], *, format:Maybe[BibtexFormat]=None, logger:Maybe[Logger]=None):
        self._value_sep    = API_W.VAL_SEP
        self._value_column = None
        self._logger       = logger or logging
        match stack:
            case PairStack():
                self._middlewares = stack.write_stack()
            case list():
                self._middlewares = stack
            case x:
                raise TypeError(type(x))

        match format:
            case None:
                self.format = deepcopy(API_W.default_format())
            case BibtexFormat():
                self.format = deepcopy(format)
            case x:
                raise TypeError(type(x))

        self.exclude_middlewares(API.ReadTime_p)

    def write(self, library, *, file:None|pl.Path=None, append:Maybe[list[Middleware]]=None) -> str:
        """ Write the library to a string, and possbly a file
        # TODO write failure reports to a separate file
        """

        self._calculate_auto_value_align(library)

        with TimeBlock_ctx(logger=logging,
                           enter="--> Write Transforms: Start",
                           exit="<-- Write Transforms:",
                           level=logmod.INFO) as ctx:
            transformed = self._run_writewares(library, append=append)

        string_pieces : list[str] = []
        string_pieces += self.make_header(transformed, file)
        for i, block in enumerate(transformed.blocks):
            # Get string representation (as list of strings) of block
            string_block_pieces = self.visit(block)
            string_pieces.extend(string_block_pieces)
            # Separate Blocks
            if i < len(transformed.blocks) - 1:
                string_pieces.append(self.format.block_separator)
        else:
            string_pieces.extend(self.make_footer(transformed, file))
            result : str = "".join(str(x) for x in string_pieces)

        # Reset the value column:
        self._value_column = None
        match file:
            case pl.Path():
                file.write_text(result)
                return result
            case _:
                return result

    def _calculate_auto_value_align(self, library: Library) -> None:
        """
        Sets the separation between keys and the value separator.
        If its already set, does nothing.
        If the format specifies a value, uses that.
        Otherwise calulates it from the larges field key
        """
        if self._value_column is not None:
            return

        match self.format.value_column:
            case int() as x:
                self._value_column = x
            case _:
                max_key_len = 0
                for entry in library.entries:
                    for key in entry.fields_dict:
                        max_key_len = max(max_key_len, len(key))
                    ##--|
                else:
                    self._value_column = max_key_len + len(self._value_sep)

    def _align_key(self, key: str) -> str:
        """ take {key} and make {key}{padding}{sep},
        Padding is from '_calculate_auto_value_align', the largest key length.
        Sep is typically '='.

        eg: _align_key('blah') -> 'blah   = '
        """
        match (self.format.value_column - len(key) - len(self._value_sep)):
            case x if 0 <= x:
                return f"{self.format.indent}{key}{' '*x}{self._value_sep}"
            case x:
                return f"{self.format.indent}{key}{' '*x}{self._value_sep}"

