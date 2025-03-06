#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
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
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from jgdv import Mixin, Proto

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from . import _interface as API_N
from bibble.util.name_parts import NameParts
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

##--|

@Proto(API.ReadTime_p)
class NameReader(ms.SplitNameParts):
    """ For use after stock "separatecoauthors",
    splits authors into nameparts
   """

    def on_read(self):
        return True

    def _transform_field_value(self, name) -> list[NameParts]:
        if not isinstance(name, list):
            raise ValueError(
                "Expected a list of strings, got {}. "
                "Make sure to use `SeparateCoAuthors` middleware"
                "before using `SplitNameParts` middleware".format(name)
            )
        result = []
        for n in name:
            wrapped = n.startswith(API_N.OBRACE) and n.endswith(API_N.CBRACE)
            result.append(parse_single_name_into_parts(n, strict=False))
        else:
            return result
