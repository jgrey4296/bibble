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
##-- end logging

import bib_middleware as BM

def build_parse_stack(spec, state):
    """ Build a default parse stack """
    read_mids = [
        BM.DuplicateHandler(),
        ms.ResolveStringReferencesMiddleware(True),
        ms.RemoveEnclosingMiddleware(True),
        BM.LatexReader(True, keep_braced_groups=True, keep_math_mode=True),
        BM.PathReader(lib_root=doot.locs["{lib-root}"]),
        BM.TagsReader(),
        ms.SeparateCoAuthors(True),
        BM.NameReader(True),
        BM.TitleReader(True)
    ]
    return {spec.kwargs.update_ : read_mids}

def build_write_stack(spec, state):
    """ build a default write stack """
    write_mids = [
        BM.NameWriter(True),
        ms.MergeCoAuthors(True),
        BM.LatexWriter(keep_math=True, enclose_urls=False),
        BM.TagsWriter(),
        BM.PathsWriter(lib_root=doot.locs["{lib-root}"]),
        ms.AddEnclosingMiddleware(allow_inplace_modification=True, default_enclosing="{", reuse_previous_enclosing=False, enclose_integers=True),
    ]
    return {spec.kwargs.update_ : write_mids}
