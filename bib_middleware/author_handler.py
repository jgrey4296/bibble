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

##-- logging
logging = logmod.getLogger(__name__)
printer = logmod.getLogger("doot._printer")
##-- end logging

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from dootle.tags.structs import NameFile

class NameReader(ms.SplitNameParts):

    @staticmethod
    def metadata_key() -> str:
        return "jg-split_name_parts"

    def _transform_field_value(self, name) -> List[NameParts]:
        if not isinstance(name, list):
            raise ValueError(
                "Expected a list of strings, got {}. "
                "Make sure to use `SeparateCoAuthors` middleware"
                "before using `SplitNameParts` middleware".format(name)
            )
        result = []
        for n in name:
            wrapped = n.startswith("{") and n.endswith("}")
            result.append(parse_single_name_into_parts(n, strict=False))

        return result

class NameWriter(ms.MergeNameParts):
    """Middleware to merge a persons name parts (first, von, last, jr) into a single string.

    Name fields (e.g. author, editor, translator) are expected to be lists of NameParts.
    """
    _all_names = NameFile()

    # docstr-coverage: inherited

    @staticmethod
    def metadata_key() -> str:
        return "dootle_merge_name_parts"

    @staticmethod
    def names_to_str():
        return str(MergeLastNameFirstName._all_names)

    def _transform_field_value(self, name) -> List[str]:
        if not isinstance(name, list) and all(isinstance(n, NameParts) for n in name):
            raise ValueError("Expected a list of NameParts, got {}. ".format(name))

        return [self._merge_name(n) for n in name]

    def _merge_name(self, name):
        result = []

        if name.von:
            result.append(" ".join(name.von))
            result.append(" ")

        if name.last:
            result.append(" ".join(name.last))
            result.append(", ")

        if name.jr:
            result.append(" ".join(name.jr))
            result.append(", ")

        result.append(" ".join(name.first))

        full_name = "".join(result).removesuffix(", ")
        MergeLastNameFirstName._all_names.update(full_name)
        return full_name


class MergeMultipleAuthorsEditors(BlockMiddleware):
    """ Merge multiple fields of the same name """

    def metadata_key(self):
        return str(self.__class__.__name__)

    def transform_entry(self, entry, library):
        fields  = []
        authors = []
        editors = []
        for x in entry.fields:
            match x.key.lower():
                case "author":
                    authors.append(x.value)
                case "editor":
                    editors.append(x.value)
                case _:
                    fields.append(x)

        if bool(authors):
            joined_authors = " and ".join(authors)
            if skip_re.search(joined_authors):
                return None
            fields.append(BTP.model.Field("author", joined_authors))
        if bool(editors):
            fields.append(BTP.model.Field("editor", " and ".join(editors)))


        entry.fields = fields
        return entry
