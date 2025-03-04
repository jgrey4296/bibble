#!/usr/bin/env python3
"""

"""
from __future__ import annotations

import logging as logmod
import pathlib as pl
from typing import (Any, Callable, ClassVar, Generic, Iterable, Iterator,
                    Mapping, Match, MutableMapping, Sequence, Tuple, TypeAlias,
                    TypeVar, cast)
import warnings

import pytest

from bibble.people.name_sub import NameSubstitutor
from bibtexparser import model
from jgdv.files.tags import SubstitutionFile

logging = logmod.root

class Test:

    @pytest.fixture(scope="function")
    def subber(self):
        subs = SubstitutionFile(norm_replace=" ", sep=" % ")
        subs.update("blah % 1 % bloo")
        subs.update("von braun, Ernst % 1 % von Braun, Ernst")
        return NameSubstitutor(subs=subs)

    @pytest.fixture(scope="function")
    def entry(self):
        return model.Entry("book", "test", [])

    def test_sanity(self, subber, entry):
        assert(True is True)
        assert("blah" in subber._subs)

    def test_no_value(self, subber, entry):
        entry.set_field(model.Field("author", []))
        result = subber.transform_entry(entry, None)
        assert(result is entry)
        assert(result.get("author").value == [])


    def test_no_sub(self, subber, entry):
        entry.set_field(model.Field("author", ["bob"]))
        result = subber.transform_entry(entry, None)
        assert(result is entry)
        assert(result.get("author").value == ["bob"])


    def test_simple_sub(self, subber, entry):
        entry.set_field(model.Field("author", ["blah"]))
        result = subber.transform_entry(entry, None)
        assert(result is entry)
        assert(result.get("author").value == ["bloo"])


    def test_selected_sub(self, subber, entry):
        entry.set_field(model.Field("author", ["jill", "blah", "bob"]))
        result = subber.transform_entry(entry, None)
        assert(result is entry)
        assert(result.get("author").value == ["jill", "bloo", "bob"])


    def test_name_format_sub(self, subber, entry):
        entry.set_field(model.Field("author", ["von braun, Ernst"]))
        result = subber.transform_entry(entry, None)
        assert(result is entry)
        assert(result.get("author").value == ["von Braun, Ernst"])
