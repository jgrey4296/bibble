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
# import more_itertools as mitz
# from boltons import
##-- end lib imports

##-- logging
logging = logmod.getLogger(__name__)
printer = logmod.getLogger("doot._printer")
##-- end logging

from selenium.webdriver import FirefoxOptions, FirefoxService, Firefox
from selenium.webdriver.common.print_page_options import PrintOptions
from waybackpy import WaybackMachineSaveAPI
import bibtexparser
import bibtexparser.model as model
from bibtexparser.middlewares.middleware import BlockMiddleware, LibraryMiddleware
import base64
import doot
import doot.errors
from doot.structs import DootKey
from doot.enums import ActionResponseEnum
from jgdv.files.tags.base import TagFile
from jgdv.files.bookmarks.collection import BookmarkCollection

FF_DRIVER          = "__$ff_driver"
READER_PREFIX      = "about:reader?url="
LOAD_TIMEOUT       = 2
WAYBACK_USER_AGENT = "Mozilla/5.0 (Windows NT 5.1; rv:40.0) Gecko/20100101 Firefox/40.0"

class OnlineHandler(BlockMiddleware):
    """
      if the entry is 'online', and it doesn't have a file associated with it,
      download it as a pdf and add it to the entry
    """

    @staticmethod
    def metadata_key():
        return "jg-online-handler"

    def __init__(self, target:pl.Path):
        super().__init__()
        self._target = target

    def transform_entry(self, entry, library):
        if entry.entry_type != "online":
            printer.info("Entry %s : Skipping non-online entry", entry.key)
            return entry

        fields = entry.fields_dict
        if "url" not in fields:
            printer.warning("Entry %s : no url found", entry.key)
            return entry

        if "file" in fields:
            printer.info("Entry %s : Already has file", entry.key)
            return entry

        # save the url
        url  = fields['url'].value
        dest = (self._target / entry.key).with_suffix(".pdf")
        printer.warning("Would be saving entry to: %s", dest)
        self.save_pdf(url, dest)
        # add it to the entry
        entry.set_field(model.Field("file", value=dest))

        return entry

    @staticmethod
    def setup_firefox() -> None:
        """ Setups a selenium driven, headless firefox to print to pdf """
        if hasattr(OnlineHandler, FF_DRIVER):
            return getattr(OnlineHandler, FF_DRIVER)

        printer.info("Setting up headless Firefox")
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
        setattr(OnlineHandler, FF_DRIVER, driver)
        return driver

    @staticmethod
    def close_firefox():
        if not hasattr(OnlineHandler, FF_DRIVER):
            return

        printer.info("Closing Firefox")
        getattr(OnlineHandler, FF_DRIVER).quit()

    def save_pdf(self, url, dest):
        """ prints a url to a pdf file using selenium """
        if not isinstance(dest, pl.Path):
            raise doot.errors.DootActionError("Destination to save pdf to is not a path", dest)

        if dest.suffix != ".pdf":
            raise doot.errors.DootActionError("Destination isn't a pdf", dest)

        if dest.exists():
            raise doot.errors.DootActionError("Destination already exists", dest)

        driver = OnlineHandler.setup_firefox()
        printer.info("Saving: %s", url)
        print_ops = PrintOptions()
        print_ops.page_range = "all"

        driver.get(READER_PREFIX + url)
        time.sleep(LOAD_TIMEOUT)
        pdf       = driver.print_page(print_options=print_ops)
        pdf_bytes = base64.b64decode(pdf)

        with open(dest, "wb") as f:
            f.write(pdf_bytes)



class WaybackHandler(BlockMiddleware):
    """ get and request wayback links, replacing the originals
      using waybackpy
      https://akamhy.github.io/waybackpy/
      """

    @staticmethod
    def metadata_key():
        return "jg-waybacker"

    def transform_entry(self, entry, library):
        if entry.entry_type != "online":
            printer.info("Entry %s : Skipping non-online entry", entry.key)
            return entry

        fields = entry.fields_dict
        if "url" not in fields:
            printer.warning("Entry %s : no url found", entry.key)
            return entry

        url = fields['url'].value
        if self.is_link_a_wayback(url):
            return entry

        if not self.is_link_active(url):
            printer.warning("Link is already dead: %s", entry.key)
            return entry

        match self.wayback_has_link(url) or self.request_wayback(url):
            case str():
                # update
                pass
            case None:
                pass

        return entry

    def is_link_active(self, url) -> bool:
        " test for the link on the open web "
        return False

    def is_link_a_wayback(self, url) -> bool:
        " see if the link is already a wayback url "
        return False

    def wayback_has_link(self, url) -> None|str:
        " get wayback's version, if it has it "
        return None

    def request_wayback(self, url) -> None|str:
        " ask wayback to archive a url, and get that new link back "
        save_api = WaybackMachineSaveAPI(url, WAYBACK_USER_AGENT)
        return save_api.save()
        # save_api.cached_save
        # save_api.timestamp()
