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
from uuid import UUID, uuid1

# ##-- end stdlib imports

from bibtexparser import model
from bibtexparser.library import Library
from bibble.io.writer import BibbleWriter

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

    type Block = model.Block
##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class RstWriter(BibbleWriter):
    """ Write bibtex entries as Rst """

    # These need to match the BibEntryDirective of the sphinx domain
    _entry      : ClassVar[str]       = ".. bibtex:entry:: {}"
    _entry_args : ClassVar[list[str]] = ["title","author", "editor", "year", "tags",
                                         "journal", "booktitle", "within",
                                         "platform", "publisher", "institution",
                                         "series", "url", "doi", "isbn", "edition",
                                         "crossref"
                                         ]
    _indent     : ClassVar[str]       = " "*3

    def _title_add(self, block:Block) -> list[str]:
        match block.get('title', None):
            case model.Field(value=str() as title):
                pass
            case _:
                raise KeyError("no title", block.key)

        match block.get("subtitle", None):
            case model.Field(value=str() as subtitle):
                return [f"{self._indent}:title: {title}: {subtitle}"]
            case _:
                return [f"{self._indent}:title: {title}"]

    def _must_add(self, block:Block, field:str) -> list[str]:
        match block.get(field, None):
            case model.Field(value=val):
                return [f"{self._indent}:{block.key}: {val}"]
            case _:
                raise KeyError('Entry missing required field', block.key, field)

    def _can_add(self, block:Block, *keys:str) -> list[str]:
        result = []
        for key in keys:
            match block.get(key, None):
                case None:
                    continue
                case model.Field(value=val):
                    result.append(f"{self._indent}:{key}: {val}")
        else:
            return result

    def visit_entry(self, block:Block) -> list[str]:
        result = [self._entry.format(block.key)]
        match block.entry_type:
            case "case" | "legal" | "judicial" | "law":
                return []
            case "standard" | "online" | "blog" | "dataset":
                return []
            case "tweet" | "thread":
                return []
            case _:
                self._title_add(block)
                self._must_add("tags")
                self._can_add("author", "editor", "year", "series")
                self._can_add("journal", "booktitle", "doi", "url", "isbn", "publisher")
                self._can_add("incollection", "institution")
                # TODO volume, number, pages, chapter

        result += ["", "", "..",
                    f"{self._indent} Fields:",
                    "{} {}".format(self._indent, ", ".join(self._fields.keys())), "",
                    f"{self._indent} Object Keys:",
                    "{} {}".format(self._indent,
                                    ", ".join([x for x in dir(block) if "__" not in x]))
                    ]

        return result

    def visit_header(self, library:Library, file:Maybe[pl.Path]=None) -> list[str]:
        match file:
            case None:
                title = "A Bibtex File"
            case pl.Path():
                title = file.stem

        lines = [".. -*- mode: ReST -*-",
                 f".. _{title}:", "",
                 "="*len(title), title, "="*len(title), "",
                 ".. contents:: Entries:",
                 "   :class: bib_entries",
                 "   :local:", "",
                 "For the raw bibtex, see `the file`_.", "",
                 f".. _`the file`: https://github.com/jgrey4296/bibliography/blob/main/main/{title}.bib", "", "",
                 ]
        return lines
