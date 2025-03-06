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
from bibtexparser import middlewares as ms
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from jgdv import Mixin, Proto

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from . import _interface as MAPI
from bibble.util.middlecore import IdenBlockMiddleware
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
class LockCrossrefKeys(IdenBlockMiddleware):
    """ Ensure key/crossref consistency by:
    removing unwanted chars in the key,
    'locking' the key by forcing the key suffix to be a single underscore
    doing the same process to crossref fields.

    locked keys are ignored
    """

    def __init__(self, regex:str|re.Pattern, sub:str, **kwargs):
        super().__init__(**kwargs)
        self._regex     : re.Pattern = re.compile(regex or MAPI.KEY_CLEAN_RE)
        self._sub       : str        = sub or MAPI.KEY_SUB_CHAR
        self._lock_char : str        = MAPI.LOCK_CHAR
        self._bad_lock  : str        = f"{MAPI.LOCK_CHAR}{MAPI.LOCK_CHAR}"

    def on_read(self):
        return True

    def transform_entry(self, entry, library):
        entry.key = self.clean_key(entry.key)
        match entry.get(MAPI.CROSSREF_K):
            case None:
                pass
            case model.Field(value=value):
                entry.set_field(model.Field(MAPI.CROSSREF_K, self.clean_key(value)))

        return entry

    def clean_key(self, key:str) -> str:
        """ Convert the entry key to a canonical form """
        if key.endswith(self._lock_char) and not key.endswith(self._bad_lock):
            return key

        clean_key = self._regex.sub(self._sub, key)
        clean_key = MAPI.KEY_SUFFIX_RE.sub("", key)
        return f"{clean_key}{self._lock_char}"
