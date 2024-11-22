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
from typing import (TYPE_CHECKING, Any, Callable, ClassVar, Final, Generator,
                    Generic, Iterable, Iterator, Mapping, Match,
                    MutableMapping, Protocol, Sequence, Tuple, TypeAlias,
                    TypeGuard, TypeVar, cast, final, overload,
                    runtime_checkable)
from uuid import UUID, uuid1

# ##-- end stdlib imports

from bibtexparser.model import Block

##-- logging
logging = logmod.getLogger(__name__)
##-- end logging


class MetaBlock(Block):
    """ A Metadata Block baseclass that does not get written out (typically),
    But can hold information about the library
    """


    def __init__(self, start_line:None|int=None, raw:None|str=None, parser_metadata:None|dict[str,Any]=None):
        super().__init__(start_line, raw, parser_metadata)


class CustomWriterBlock(Block):
    """ A Block that controls how it is written """

    def visit(self, writer:BibbleWriter) -> list[str]:
        raise NotImplementedError()
