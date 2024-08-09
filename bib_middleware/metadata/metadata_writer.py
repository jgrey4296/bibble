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
import json
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

# ##-- 3rd party imports
import jsonlines
import bibtexparser as BTP
import more_itertools as mitz
import sh
from bibtexparser import model
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from bibtexparser.middlewares.names import (NameParts,
                                            parse_single_name_into_parts)

# ##-- end 3rd party imports

# ##-- 1st party imports
from bib_middleware.util.base_writer import BaseWriter

# ##-- end 1st party imports

##-- logging
logging = logmod.getLogger(__name__)
fail_l  = logging.getChild("_failures")
##-- end logging

exiftool = sh.exiftool
calibre  = sh.ebook_meta
qpdf     = sh.qpdf
pdfinfo  = sh.pdfinfo

class _EntryFileGetter_m:

    def _get_file(self, entry) -> None|pl.Path:
        match entry.fields_dict.get("file", None):
            case None:
                return None
            case pl.Path() as path:
                return path
            case BTP.model.Field() as path if isinstance(path.value, pl.Path) :
                return path.value
            case _:
                raise TypeError("Bad File Path Type", path)

class _Metadata_Check_m:
    """A mixin for checking the metadata fof files"""

    def backup_original_metadata(self, path) -> None:
        """
        If self._backup is set, backup the files metadata as jsonlines there
        """
        match self._backup:
            case pl.Path():
                pass
            case _:
                return

        try:
            result = json.loads(exiftool("-J", str(path)))[0]
        except sh.ErrorReturnCode:
            raise ValueError("Couldn't retrieve metadata as json", path) from None

        with jsonlines.open(self._backup, mode='a') as f:
            f.write(result)

    def metadata_matches_entry(self, path, entry) -> bool:
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

class _Pdf_Update_m:
    """A Mixin for pdf specific metadata manipulation"""

    def update_pdf_by_exiftool(self, path, entry) -> None:
        # exiftool -{tag}="{content}" {file}
        # Build args:
        args   = []
        exiftool_args = self._entry_to_exiftool_args(entry)

        logging.debug("Pdf update args: %s : %s", path, args)
        # Call
        try:
            exiftool(*args, str(path))
        except sh.ErrorReturnCode as err:
            raise ChildProcessError("Exiftool update failed", err) from None

    def pdf_is_modifiable(self, path) -> bool:
        """ Test the pdf for encryption or password locking """
        try:
            cmd1 = qpdf("--is-encrypted", str(path), _ok_code=(2))
            cmd2 = qpdf("--requires-password", str(path), _ok_code=(2))
        except sh.ErrorReturnCode as err:
            return False

        return True

    def pdf_validate(self, path) -> None:
        # code 0 for fine,
        # writes to stderr for issues
        try:
            qpdf("--check", str(path))
        except sh.ErrorReturnCode:
            raise ChildProcessError("PDF Failed Validation") from None

    def pdf_finalize(self, path) -> None:
        """ run qpdf --linearize,
          and delete the pdf_original if it exists
        """
        assert(path.suffix == ".pdf")
        logging.debug("Finalizing Pdf: %s", path)
        original = str(path)
        copied   = path.with_stem(path.stem + "_cp")
        backup   = path.with_suffix(".pdf_original")
        if copied.exists():
            raise FileExistsError("The temp copy for linearization shouldn't already exist", original)

        path.rename(copied)

        try:
            qpdf(str(copied), "--linearize", original)
        except sh.ErrorReturnCode:
            copied.rename(original)
            raise ChildProcessError("Linearization Failed") from None
        else:
            if backup.exists():
                backup.unlink()
            copied.unlink()

    def _entry_to_exiftool_args(self, entry) -> list:
        """
        Extract and format the entry as exiftool args
        """
        fields = entry.fields_dict
        args   = []

        # XMP-bib:
        # The custom full bibtex entry
        args += [f'-bibtex={entry.raw}']

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

        args += ['-Year={}'.format(fields['year'].value)]

        if 'tags' in fields:
            args += ['-Keywords={}'.format(",".join(fields['tags'].value))]
        if 'isbn' in fields:
            args += ['-ISBN={}'.format(fields['isbn'].value)]
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

        return args

class _Epub_Update_m:
    """A Mixin for epub-specific metadata manipulation"""

    def update_epub_by_calibre(self, path, entry) -> None:
        args = self.entry_to_calibre_args(entry)

        logging.debug("Ebook update args: %s : %s", path, args)
        try:
            calibre(str(path), *args)
        except sh.ErrorReturnCode:
            raise ChildProcessError("Calibre Update Failed") from None

    def entry_to_calibre_args(self, entry) -> list:
        fields = entry.fields_dict
        args = []
        title = None

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

        return args

class MetadataApplicator(_Pdf_Update_m, _Epub_Update_m, _EntryFileGetter_m, _Metadata_Check_m, LibraryMiddleware):
    """ Apply metadata to files mentioned in bibtex entries
      uses xmp-prism tags and some custom ones for pdfs,
      and epub standard.
      """

    @staticmethod
    def metadata_key():
        return "MetadataApplicator"

    def __init__(self, backup:None|pl.Path=None):
        super().__init__()
        self._backup   = backup
        self._failures = []

    def transform(self, library:BTP.Library) -> BTP.Library:
        total = len(library.entries)
        logging.info("Appling Metadata to library")
        for i, entry in enumerate(library.entries):
            self.transform_entry(entry, library)

        return library

    def transform_entry(self, entry,  library) -> Any:
        # TODO add a 'meta_update' status field to the entry for [locked,failed]
        match self._get_file(entry):
            case None:
                pass
            case x if not x.exists():
                update = BTP.model.Field("orphaned", "True")
                entry.set_field(update)
            case x if x.suffix == ".pdf" and not self.pdf_is_modifiable(x):
                update = BTP.model.Field("pdf_locked", "True")
                entry.set_field(update)
                self._failures.append(("locked", x, None))
                fail_l.warning("PDF is locked: %s", x)
            case x if self.metadata_matches_entry(x, entry):
                fail_l.info("No Metadata Update Necessary: %s", x)
            case x if x.suffix == ".pdf":
                try:
                    self.backup_original_metadata(x)
                    self.update_pdf_by_exiftool(x, entry)
                    self.pdf_validate(x)
                    self.pdf_finalize(x)
                except (ValueError, ChildProcessError, FileExistsError) as err:
                    self._failures.append(("pdf_fail", x, err))
                    fail_l.warning("Pdf Update Failed: %s : %s", x, err)
            case x if x.suffix == ".epub":
                try:
                    self.backup_original_metadata(x)
                    self.update_epub_by_calibre(x, entry)
                except (ValueError, ChildProcessError) as err:
                    self._failures.append(("epub_fail", x, err))
                    fail_l.warning("Epub Update failed: %s : %s", x, err)
            case x:
                self._failures.append(("unknown", x, None))
                fail_l.warning("Found a file that wasn't an epub or pdf: %s", x)

        return entry


class FileCheck(_Pdf_Update_m, _EntryFileGetter_m, LibraryMiddleware):
    """
      Annotate entries with 'pdf_locked' if the pdf can't be modified,
      "orphan_file" if the pdf or epub does not exist
    """

    @staticmethod
    def metadata_key():
        return "PdfLockCheck"


    def transform(self, library:BTP.Library) -> BTP.Library:
        total = len(library.entries)
        logging.info("Checking library files")
        for i, entry in enumerate(library.entries):
            self.transform_entry(entry, library)

        return library

    def transform_entry(self, entry, library) -> Any:
        match self._get_file(entry):
            case None:
                return
            case x if not x.exists():
                update = BTP.model.Field("orphaned", "True")
                entry.set_field(update)
            case x if x.suffix == ".pdf" and not self.pdf_is_modifiable(x):
                update = BTP.model.Field("pdf_locked", "True")
                entry.set_field(update)
