#!/usr/bin/env python3
"""

"""

from __future__ import annotations

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

import bibtexparser
import bibtexparser.model as model
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

from jgdv import Proto, Mixin
from jgdv.files.tags import TagFile

import bibble._interface as API

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging

@Proto(API.ReadTime_p)
class TagsReader(BlockMiddleware):
    """
      Read Tag strings, split them into a set, and keep track of all mentioned tags
      By default the classvar _all_tags is cleared on init, pass clear=False to not
    """
    _all_tags : TagFile = TagFile()

    @staticmethod
    def metadata_key():
        return "BM-tags-reader"

    @staticmethod
    def tags_to_str():
        return str(TagsReader._all_tags)

    def __init__(self, clear=True):
        super().__init__(True, True)
        if clear:
            TagsReader._all_tags = TagFile()

    def on_read(self):
        return True

    def transform_entry(self, entry, library):
        match entry.get("tags"):
            case None:
                logging.warning("Entry has no Tags on parse: %s", entry.key)
                entry.set_field(model.Field("tags", set()))
            case model.Field(value=val) if not bool(val):
                logging.warning("Entry has no Tags on parse: %s", entry.key)
                entry.set_field(model.Field("tags", set()))
            case model.Field(value=str() as val):
                as_set = set(val.split(","))
                entry.set_field(model.Field("tags", as_set))
                TagsReader._all_tags.update(as_set)

        return entry
