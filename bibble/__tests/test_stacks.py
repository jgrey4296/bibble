#!/usr/bin/env python3
"""

"""
# ruff: noqa: ANN201, ARG001, ANN001, ARG002, ANN202

# Imports
from __future__ import annotations

# ##-- stdlib imports
import logging as logmod
import pathlib as pl
import warnings
# ##-- end stdlib imports

# ##-- 3rd party imports
import pytest
# ##-- end 3rd party imports

import bibble as BM
import bibtexparser as BTP
import doot
import doot.errors
from bibtexparser import middlewares as ms
from doot.structs import DKey, DKeyed, TaskSpec
from bibble.util import PairStack

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
# from dataclasses import InitVar, dataclass, field
# from pydantic import BaseModel, Field, model_validator, field_validator, ValidationError

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

# Vars:
sort_firsts = ["title", "author", "editor", "year", "tags", "booktitle", "journal", "volume", "number", "edition", "edition_year", "publisher"]
sort_lasts  = ["isbn", "doi", "url", "file", "crossref"]
sub_fields  = ["publisher", "journal", "series", "institution"]
# Body:

def build_new_stack(spec, state, _meta:set, _namesubs:Maybe, _tagsubs:Maybe, _othersubs:Maybe, _libroot:pl.Path) -> PairStack:
    """ Build a new PairStack of middlewares, with optional and required elements
    Because of how pairstack works, to see the parse stack, read from top to bottom.
    To see the write transforms, read from bottom to top.
    """
    stack = PairStack()
    # Very first/last middlewares:
    stack.add(read=[BM.failure.DuplicateKeyHandler(),
                    ],
              write=[BM.failure.FailureHandler(),
                     BM.metadata.ApplyMetadata() if "apply" in _meta else None,
                     ])
    # Add bidirectional transforms
    stack.add(BM.bidi.BraceWrapper(),
              BM.bidi.BidiLatex() if "latex" in _meta else None,
              BM.bidi.BidiPaths(lib_root=_libroot),
              BM.bidi.BidiNames(),
              BM.bidi.BidiIsbn(),
              BM.bidi.BidiTags(),
              None,
              read=[
                  BM.metadata.KeyLocker(),
                  BM.fields.TitleSplitter()
              ],
              write=[
                  BM.fields.FieldSorter(sort_firsts, sort_lasts) if "fsort" in _meta else None,
                  BM.metadata.EntrySorter() if "esort" in _meta else None,
              ])

    if "count" in _meta:
        # Accumulate various fields
        stack.add(write=[
            BM.fields.FieldAccumulator("all-tags",     ["tags"]),
            BM.fields.FieldAccumulator("all-pubs",     ["publisher"]),
            BM.fields.FieldAccumulator("all-series",   ["series"]),
            BM.fields.FieldAccumulator("all-journals", ["journal"]),
            BM.fields.FieldAccumulator("all-people",   ["author", "editor"]),
        ])

    if "subs" in _meta:
        stack.add(write=[
            # NameSubs need to merge with BidiNames
            # BM.people.NameSubstitutor(_namesubs) if _namesubs is not None else None,
            BM.fields.FieldSubstitutor("tags", subs=_tagsubs) if _tagsubs is not None else None,
            BM.fields.FieldSubstitutor(sub_fields, subs=_othersubs, force_single_value=True) if _othersubs is not None else None,
        ])

    if "check" in _meta:
        stack.add(write=[BM.metadata.FileCheck()])

    return stack


##--|

class TestFullStack:

    def test_sanity(self):
        assert(True is not False) # noqa: PLR0133
