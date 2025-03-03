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
from random import choices
from uuid import UUID, uuid1

# ##-- end stdlib imports

# ##-- 3rd party imports
import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)

# ##-- end 3rd party imports

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

class SelectN(LibraryMiddleware):
    """ Select N random entries """

    @staticmethod
    def metadata_key():
        return "BM-select-n"

    def __init__(self, count=1):
        super().__init__()
        self._count = count

    def transform(self, library):
        entries = library.entries
        chosen = choices(entries, k=self._count)

        library.entries = chosen
        return library

class SelectEntries(LibraryMiddleware):
    """ Select entries of a particular type """

    @staticmethod
    def metadata_key():
        return "BM-select-type"

    def __init__(self, target="article"):
        super().__init__()
        self._entry_target = target.lower()

    def transform(self, library):
        chosen = [x for x in library.entries if x.entry_type.lower() == self._entry_target]
        library.entries = chosen
        return library

class SelectTags(LibraryMiddleware):
    """ Select entries of with a particular tag """

    @staticmethod
    def metadata_key():
        return "BM-select-tag"

    def __init__(self, targets=None):
        super().__init__()
        self._targets = set(targets or [])

    def transform(self, library):
        chosen = [x for x in library.entries if bool(x.fields_dict['tags'].value & self._targets)]

        library.entries = chosen
        return library

class SelectAuthor(LibraryMiddleware):

    @staticmethod
    def metadata_key():
        return "BM-select-author"

    def __init__(self, targets=None):
        super().__init__()
        self._targets = set(targets or [])

    def transform(self, library):
        raise NotImplementedError()
