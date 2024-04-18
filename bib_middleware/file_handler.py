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

from jgdv.files.tags.name import NameFile
from bib_middleware.base_writer import BaseWriter


# TODO: add metadata to pdf/epubs
# TODO: add to pdf bookmarks if subciting
# TODO: file existance validator

class PdfMetadataWriter(BaseWriter):

    def transform_entry(self, entry):
        # If no pdf file associated, return

        # else add bib info

        return entry

class EpubMetadataWriter(BaseWriter):

    def transform_entry(self, entry):
        # If no epub file associated, return

        # else add bib info

        return entry
