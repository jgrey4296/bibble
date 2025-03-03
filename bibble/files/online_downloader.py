#!/usr/bin/env python3
"""

See EOF for license/metadata/notes as applicable
"""

# Imports:
from __future__ import annotations

# ##-- stdlib imports
import base64
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
from bibtexparser.middlewares.middleware import (BlockMiddleware,
                                                 LibraryMiddleware)
from jgdv import Proto, Mixin
from jgdv.files.bookmarks import BookmarkCollection
from jgdv.files.tags import TagFile
from selenium.webdriver import Firefox, FirefoxOptions, FirefoxService
from selenium.webdriver.common.print_page_options import PrintOptions
from waybackpy import WaybackMachineSaveAPI

# ##-- end 3rd party imports

# ##-- 1st party imports
import bibble._interface as API
from bibble.util.field_matcher_m import FieldMatcher_m

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

FF_DRIVER          : Final[str] = "__$ff_driver"
READER_PREFIX      : Final[str] = "about:reader?url="
LOAD_TIMEOUT       : Final[int] = 2
WAYBACK_USER_AGENT : Final[str] = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"

##--|

class FirefoxController:

    @staticmethod
    def setup() -> None:
        """ Setups a selenium driven, headless firefox to print to pdf """
        if hasattr(OnlineDownloader, FF_DRIVER):
            return getattr(OnlineDownloader, FF_DRIVER)

        logging.info("Setting up headless Firefox")
        options = FirefoxOptions()
        # options.add_argument("--start-maximized")
        options.add_argument("--headless")
        # options.binary_location = "/usr/bin/firefox"
        # options.binary_location = "/snap/bin/geckodriver"
        options.set_preference("print.always_print_silent", True)
        options.set_preference("print.printer_Mozilla_Save_to_PDF.print_to_file", True)
        options.set_preference("print_printer", "Mozilla Save to PDF")
        options.set_preference("print.printer_Mozilla_Save_to_PDF.use_simplify_page", True)
        options.set_preference("print.printer_Mozilla_Save_to_PDF.print_page_delay", 50)
        service                  = FirefoxService(executable_path="/snap/bin/geckodriver")
        driver                   = Firefox(options=options, service=service)
        driver.set_page_load_timeout(LOAD_TIMEOUT)
        setattr(OnlineDownloader, FF_DRIVER, driver)
        return driver

    @staticmethod
    def close():
        if not hasattr(OnlineDownloader, FF_DRIVER):
            return

        logging.info("Closing Firefox")
        getattr(OnlineDownloader, FF_DRIVER).quit()

##--|

@Mixin(FieldMatcher_m)
class OnlineDownloader(BlockMiddleware):
    """
      if the entry is 'online', and it doesn't have a file associated with it,
      download it as a pdf and add it to the entry
    """
    _entry_whitelist    : ClassVar[list[str]] = ["online", "blog"]
    _target_dir         : pl.Path
    _target_entry_types : list[str]

    @staticmethod
    def metadata_key():
        return "BM-online-handler"

    def __init__(self, target:pl.Path, *e_types:str, logger:Maybe[logmod.Logger]=None, **kwargs):
        super().__init__(**kwargs)
        self._target_dir         = target
        self._target_entry_types = list(e_types or OnlineDownloader._entry_whitelist)
        self._logger             = logger or logging

    def transform_entry(self, entry, library):
        if self.should_skip_entry(entry, library):
            return entry

        match entry.get("url"), entry.get("file"):
            case _, pl.Path()|str():
                self._logger.info("Entry %s : Already has file", entry.key)
                return entry
            case None, _:
                self._logger.warning("Entry %s : no url found", entry.key)
                return entry
            case model.Field(value=url), None:
                safe_key = entry.key.replace(":","_")
                dest     = (self._target_dir / safe_key).with_suffix(".pdf")
                self.save_pdf(url, dest)
                # add it to the entry
                entry.set_field(model.Field("file", value=dest))

        return entry

    def save_pdf(self, url, dest):
        """ prints a url to a pdf file using selenium """
        if not isinstance(dest, pl.Path):
            raise FileNotFoundError("Destination to save pdf to is not a path", dest)

        if dest.suffix != ".pdf":
            raise FileNotFoundError("Destination isn't a pdf", dest)

        if dest.exists():
            logging.info("Destination already exists: %s", dest)
            return

        driver = FirefoxController.setup()
        logging.info("Saving: %s", url)
        print_ops = PrintOptions()
        print_ops.page_range = "all"

        driver.get(READER_PREFIX + url)
        time.sleep(LOAD_TIMEOUT)
        pdf       = driver.print_page(print_options=print_ops)
        pdf_bytes = base64.b64decode(pdf)

        if not bool(pdf_bytes):
            self._logger.warning("No Bytes were downloaded")
            return

        logging.info("Saving to: %s", dest)
        with dest.open("wb") as f:
            f.write(pdf_bytes)
