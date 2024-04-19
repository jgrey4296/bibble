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

class CleanUrls(BlockMiddleware):
    """ Strip unnecessary doi and dblp prefixes from urls  """

    @staticmethod
    def metadata_key():
        return "jg-clean-urls"

    def transform_entry(self, entry, library):
        fields_dict = entry.fields_dict
        if "doi" in fields_dict:
            clean = fields_dict['doi'].value.removeprefix("https://doi.org/")
            fields_dict['doi'] = model.Field("doi", clean)

        if "url" in fields_dict:
            url = fields_dict['url'].value
            if url.startswith("db/"):
                joined                   = "".join(["https://dblp.org/", url])
                fields_dict['biburl']    = model.Field("biburl", joined)
                fields_dict['bibsource'] = model.Field('bibsource', "dblp computer science bibliography, https://dblp.org")
                del fields_dict['url']

        if "ee" in fields_dict:
            url = fields_dict['ee'].value
            del fields_dict['ee']
            fields_dict['url'] = model.Field("url", url)

        entry.fields = list(fields_dict.values())
        return entry
