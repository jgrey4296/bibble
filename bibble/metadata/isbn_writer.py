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

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
import isbn_hyphenate
import pyisbn
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)
from jgdv import Proto

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API

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

##--|

# isort: on
# ##-- end types

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

ISBN_STRIP_RE               = re.compile(r"[\s-]")
ISBN_K         : Final[str] = "isbn"
INVALID_ISBN_K : Final[str] = "invalid_isbn"
##--|

@Proto(API.WriteTime_p)
class IsbnWriter(BlockMiddleware):
    """
      format the isbn for writing
    """

    @staticmethod
    def metadata_key():
        return "BM-isbn-writer"

    def on_write(self):
        return True

    def transform_entry(self, entry, library):
        f_dict = entry.fields_dict
        if ISBN_K not in f_dict:
            return entry
        if INVALID_ISBN_K in f_dict:
            return entry
        if not bool(f_dict[ISBN_K].value):
            return entry

        try:
            isbn = isbn_hyphenate.hyphenate(f_dict[ISBN_K].value)
            entry.set_field(model.Field(ISBN_K, isbn))
        except isbn_hyphenate.IsbnError as err:
            logging.warning("Writing ISBN failed: %s : %s", f_dict[ISBN_K].value, err)
            pass

        return entry
