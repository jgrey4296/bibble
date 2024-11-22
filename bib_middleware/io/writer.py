#!/usr/bin/env python3
"""

"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import datetime
from copy import deepcopy
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

from bibtexparser import model
from bibtexparser.model import Library
from bibtexparser.middlewares import Middleware
from bibtexparser.writer import BibtexFormat
from bib_middleware.model import MetaBlock

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class BibMiddlewareWriter:
    """ A Refactored bibtexparser writer
    Uses visitor pattern
    """

    def __init__(self, stack:list[Middleware], format:BibtexFormat):
        self._middlewares            = stack
        self._format                 = deepcopy(format)
        self._val_sep                = " = "
        self._parsing_failed_comment = "% WARNING Parsing failed for the following {n} lines."

    def write(self, library, *, file:None|pl.Path=None) -> str:
        """ Write the library to a string, and possbly a file """

        if self._format.value_column == "auto":
            self._format.value_column = _calculate_auto_value_align(library)

        transformed = self._run_middlewares(library)
        string_pieces = []

        string_pieces.extend(self.visit_header(transformed, file))

        for i, block in enumerate(transformed.blocks):
            # Get string representation (as list of strings) of block
            string_block_pieces = self.visit_block(block)
            string_pieces.extend(string_block_pieces)
            # Separate Blocks
            if i < len(transformed.blocks) - 1:
                string_pieces.append(self._format.block_separator)

        string_pieces.extend(self.visit_footer(transformed, file))

        result = "".join(string_pieces)

        match file:
            case pl.Path():
                file.write_text(result)
            case _:
                pass

        return result

    def _calculate_auto_value_align(self, library: Library) -> int:
        max_key_len = 0
        for entry in library.entries:
            for key in entry.fields_dict:
                max_key_len = max(max_key_len, len(key))
        return max_key_len + len(self._val_sep)

    def _align_string(self, key: str) -> str:
        """The spaces which have to be added after the ` = `."""
        length = self._format.value_column - len(key) - len(self._val_sep)
        return "" if length <= 0 else " " * length

    def _run_middlewares(self, library) -> Library:
        for middlware in self._middlewares:
            library = middleware.transform(library=library)

        return library

    def visit_header(self, library, file:None|pl.Path=None) -> list[str]:
        return []

    def visit_footer(self, library, file:None|pl.Path=None) -> list[str]:
        return []

    def visit_block(self, block) -> List[str]:
        match block:
            case x if hasattr(x, "visit"):
                return x.visit(self)
            case MetaBlock():
                pass
            case model.Entry():
                return self.treat_entry(block)
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
            case _:
                raise ValueError(f"Unknown block type: {type(block)}")

    def visit_entry(self, block:model.Entry) -> List[str]:
        res = ["@", block.entry_type, "{", block.key, ",\n"]
        field: Field
        for i, field in enumerate(block.fields):
            res.append(self._format.indent)
            res.append(field.key)
            res.append(_align_string(self._format, field.key))
            res.append(self._val_sep)
            res.append(field.value)
            if self._format.trailing_comma or i < len(block.fields) - 1:
                res.append(",")
            res.append("\n")
        res.append("}\n")
        return res

    def visit_string(self, block:model.String) -> List[str]:
        return [
            "@string{",
            block.key,
            self._val_sep,
            block.value,
            "}\n",
        ]

    def visit_preamble(self, block:model.Preamble) -> List[str]:
        return [f"@preamble{{{block.value}}}\n"]

    def visit_impl_comment(self, block:model.ImplicitComment) -> List[str]:
        # Note: No explicit escaping is done here - that should be done in middleware
        return [block.comment, "\n"]

    def visit_expl_comment(self, block:model.ExplicitComment) -> List[str]:
        return ["@comment{", block.comment, "}\n"]

    def visit_failed_block(self, block:model.ParsingFailedBlock) -> List[str]:
        lines = len(block.raw.splitlines())
        parsing_failed_comment = self._parsing_failed_comment.format(n=lines)
        return [parsing_failed_comment, "\n", block.raw, "\n"]
