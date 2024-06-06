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

import bibtexparser as BTP
import bibtexparser.model as model
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
from bibtexparser.middlewares.names import parse_single_name_into_parts, NameParts

import sh
import doot
import doot.errors
from doot.structs import DootKey
from bib_middleware.base_writer import BaseWriter

exiftool = sh.exiftool
calibre  = sh.ebook_meta
qpdf     = sh.qpdf

class ApplyMetadata:
    """ Apply metadata to files mentioned in bibtex entries
      uses xmp-prism tags and some custom ones for pdfs,
      and epub standard.
      TODO: add to pdf bookmarks if subciting
      TODO: file existance validator
      """

    def __init__(self):
        pass

    @DootKey.kwrap.types("from", hint={"type_":BTP.Library})
    @DootKey.kwrap.paths("backup")
    def __call__(self, spec ,state, _lib, _backup):
        total                                       = len(_lib.entries)
        failures : list[tuple[str, pl.Path, Error]] = []
        for i, entry in enumerate(_lib.entries):
            printer.info("(%-4s/%-4s) Processing: %s", i, total, entry.key)
            match self._get_file(entry):
                case None:
                    pass
                case x if x.suffix == ".pdf" and not self._pdf_is_modifiable(x):
                    failures.append(("locked", x, None))
                    fail_l.warning("PDF is locked: %s", x)
                case x if self._metadata_matches_entry(x, entry):
                    fail_l.info("No Metadata Update Necessary: %s", x)
                case x if x.suffix == ".pdf":
                    try:
                        self._backup_original_metadata(_backup, x)
                        self._update_pdf_by_exiftool(x, entry)
                        self._pdf_validate(x)
                        self._pdf_finalize(x)
                    except doot.errors.DootActionError as err:
                        failures.append(("pdf_fail", x, err))
                        fail_l.warning("Pdf Update Failed: %s : %s", x, err)
                case x if x.suffix == ".epub":
                    try:
                        self._backup_original_metadata(_backup, x)
                        self._update_epub_by_calibre(x, entry)
                    except doot.errors.DootActionError as err:
                        failures.append(("epub_fail", x, err))
                        fail_l.warning("Epub Update failed: %s : %s", x, err)
                case x:
                    failures.append(("unknown", x, None))
                    fail_l.warning("Found a file that wasn't an epub or pdf: %s", x)

        return { "failures" : failures }

    def _get_file(self, entry) -> None|pl.Path:
        match entry.fields_dict.get("file", None):
            case None:
            return None
            case pl.Path() as path:
                return path
            case BTP.model.Field() as path if isinstance(path.value, pl.Path) :
                return path.value
            case _:
                raise doot.errors.DootActionError("Bad File Path Type", path)

    def _update_pdf_by_exiftool(self, path, entry) -> None:
        # exiftool -{tag}="{content}" {file}
        # Build args:
        args   = []
        fields = entry.fields_dict

        # XMP-bib:
        args += [f'-bibtex={entry.raw}']

        args += ['-Year={}'.format(fields['year'].value)]
        if 'isbn' in fields:
            args += ['-ISBN={}'.format(fields['isbn'].value)]

        # General
        match fields:
            case {"title": t, "subtitle": st}:
                args += ['-title={}: {}'.format(t.value, st.value)]
            case {"title": t}:
                args += ['-title={}'.format(t.value)]
            case {"short_parties": t}:
                args += ['-title={}'.format(t.value)]

        match fields:
            case {"author": a}:
                args += ['-author={}'.format(a.value)]
            case {"editor": a}:
                args += ['-author={}'.format(a.value)]

        if 'tags' in fields:
            args += ['-Keywords={}'.format(",".join(fields['tags'].value))]
        if 'edition' in fields:
            args += ['-xmp-prism:edition={}'.format(fields['edition'].value)]
        if 'publisher' in fields:
            args += ["-publisher={}".format(fields['publisher'].value)]
        if 'url' in fields:
            args += ["-xmp-prism:link={}".format(fields['url'].value)]
        if 'doi' in fields:
            args += ['-xmp-prism:DOI={}'.format(fields['doi'].value)]
        if 'institution' in fields:
            args += ['-xmp-prism:organization={}'.format(fields['institution'].value)]
        if 'issn' in fields:
            args += ['-xmp-prism:issn={}'.format(fields['issn'].value)]

        logging.debug("Pdf update args: %s : %s", path, args)
        # Call
        try:
            exiftool(*args, str(path))
        except sh.ErrorReturnCode as err:
            raise doot.errors.DootActionError("Exiftool update failed", err)


    def _update_epub_by_calibre(self, path, entry) -> None:
        fields = entry.fields_dict
        args = []

        match fields:
            case {"title":t}:
                title = t.value
            case {"short_parties":t}:
                title = t.value
        if 'subtitle' in fields:
            title += ": {}".format(fields['subtitle'].value)

        args += ['--title={}'.format(title)]

        match fields:
            case {"author":a}:
                args += ['--authors={}'.format(a.value)]
            case {"editor":a}:
                args += ['--authors={}'.format(a.value)]

        if 'publisher' in fields:
            args += ["--publisher={}".format(fields['publisher'].value)]
        if 'series' in fields:
            args += ["--series={}".format(fields['series'].value)]
        if 'number' in fields:
            args += ['--index={}'.format(fields['number'].value)]
        if 'volume' in fields:
            args += ['--index={}'.format(fields['volume'].value)]

        if 'isbn' in fields:
            args += ['--isbn={}'.format(fields['isbn'].value)]
        if 'doi' in fields:
            args += ['--identifier=doi:{}'.format(fields['doi'].value)]

        if 'tags' in fields:
        args += ['--tags={}'.format(",".join(fields['tags'].value))]
        if 'year' in fields:
        args += ['--date={}'.format(fields['year'].value)]

        args += ['--comments={}'.format(entry.raw)]

        logging.debug("Ebook update args: %s : %s", path, args)
        try:
            calibre(str(path), *args)
        except sh.ErrorReturnCode:
            raise doot.errors.DootActionError("Calibre Update Failed")



    def _pdf_is_modifiable(self, path) -> bool:
        """ Test the pdf for encryption or password locking """
        try:
            cmd1 = qpdf("--is-encrypted", str(path), _ok_code=(2))
            cmd2 = qpdf("--requires-password", str(path), _ok_code=(2))
        except sh.ErrorReturnCode as err:
            return False

        return True

    def _pdf_validate(self, path) -> None:
        # code 0 for fine,
        # writes to stderr for issues

        # TODO also use pdfinto
        try:
            qpdf("--check", str(path))
        except sh.ErrorReturnCode:
            raise doot.errors.DootActionError("PDF Failed Validation")


    def _pdf_finalize(self, path) -> None:
        """ run qpdf --linearize,
          and delete the pdf_original if it exists """
        assert(path.suffix == ".pdf")
        logging.debug("Finalizing Pdf: %s", path)
        original = str(path)
        copied   = path.with_stem(path.stem + "_cp")
        backup   = path.with_suffix(".pdf_original")
        if copied.exists():
            raise doot.errors.DootActionError("The temp copy for linearization shouldn't already exist", original)

        path.rename(copied)

        try:
            qpdf(str(copied), "--linearize", original)
        except sh.ErrorReturnCode:
            copied.rename(original)
            raise doot.errors.DootActionError("Linearization Failed")
        else:
            if backup.exists():
                backup.unlink()
            copied.unlink()

    def _backup_original_metadata(self, archive, path) -> None:
        try:
            result = json.loads(exiftool("-J", str(path)))[0]
        except sh.ErrorReturnCode:
            raise doot.errors.DootActionError("Couldn't retrieve metadata as json", path)

        with jsonlines.open(archive, mode='a') as f:
            f.write(result)

    def _metadata_matches_entry(self, path, entry) -> bool:
        try:
            result = json.loads(exiftool("-J", str(path)))[0]
        except sh.ErrorReturnCode:
            fail_l.warning("Couldn't match metadata", path)
            return False

        if 'Bibtex' not in result and 'Description' not in result:
            return False

        if result.get('Bibtex', None) == entry.raw:
            return True

        if result.get('Description', None) == entry.raw:
            return True

        return False
