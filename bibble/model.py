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
from bibtexparser.model import Block
from jgdv import Maybe, Proto

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

@Proto(API.CustomWriter_p)
class MetaBlock(Block):
    """ A Metadata Block baseclass that does not get written out (typically),
    But can hold information about the library
    """

    def __init__(self, start_line:Maybe[int]=None, raw:Maybe[str]=None, parser_metadata:Maybe[dict[str,Any]]=None):
        super().__init__(start_line, raw, parser_metadata)

    def visit(self, writer) -> list[str]:
        return []
