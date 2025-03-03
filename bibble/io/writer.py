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
from copy import deepcopy
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
from bibtexparser import model
from bibtexparser.middlewares.middleware import Middleware
from bibtexparser.model import MiddlewareErrorBlock
from bibtexparser.library import Library
from bibtexparser.writer import BibtexFormat

# ##-- end 3rd party imports

# ##-- 1st party imports
from bibble.model import MetaBlock

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class BibbleWriter:
    """ A Refactored bibtexparser writer
    Uses visitor pattern
    """

    def __init__(self, stack:list[Middleware], format:None|BibtexFormat=None):
        self._middlewares            = stack
        self._val_sep                = " = "
        self._parsing_failed_comment = "% WARNING Parsing failed for the following {n} lines."
        match format:
            case None:
                self._format                 = BibtexFormat()
                self._format.value_column    = 15
                self._format.indent          = " "
                self._format.block_separator = "\n"
                self._format.trailing_comma  = True
            case BibtexFormat():
                self._format                 = deepcopy(format)
            case _:
                raise TypeError("Bad BibtexFormat passed to writer", format)

        if not all([isinstance(x, Middleware) for x in self._middlewares]):
            raise TypeError("Bad middleware passed to Reader", stack)

    def write(self, library, *, file:None|pl.Path=None, append:None|list[Middleware]=None) -> str:
        """ Write the library to a string, and possbly a file """

        if self._format.value_column == "auto":
            self._format.value_column = _calculate_auto_value_align(library)

        transformed = self._run_middlewares(library, append=append)
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

    def _run_middlewares(self, library, append:None|list[Middleware]) -> Library:
        for middleware in self._middlewares:
            library = middleware.transform(library=library)

        match append:
            case [*xs]:
                for middlware in xs:
                    library = middleware.transform(library=library)
                else:
                    return library
            case _:
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
                pass
            case _:
                raise ValueError(f"Unknown block type: {type(block)}")

    def visit_entry(self, block:model.Entry) -> List[str]:
        res = ["@", block.entry_type, "{", block.key, ",\n"]
        field: Field
        for i, field in enumerate(block.fields):
            res.append(self._format.indent)
            res.append(field.key)
            res.append(self._align_string(field.key))
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
