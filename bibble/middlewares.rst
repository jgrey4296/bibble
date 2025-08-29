.. -*- mode: ReST -*-

.. _middlewares:

===========
Middlewares
===========

.. contents:: Contents
   :local:



Failure
-------

These are for handling various failures in parsing and processing.
See :class:`~bibble.failure.duplicate_handler.DuplicateKeyHandler` and :class:`~bibble.failure.failure_handler.FailureHandler`.


Fields
------

The middlewares in this module transform fields in entries.

Specific fields transformed are titles/subtitles using :class:`~bibble.fields.title_reader.TitleCleaner`
and :class:`~bibble.fields.title_reader.TitleSplitter`,
and URLs using :class:`~bibble.fields.url_reader.CleanUrls` and :class:`~bibble.fields.url_reader.ExpandUrls`.

Meanwhile more generalised handlers are :class:`~bibble.fields.field_accumulator.FieldAccumulator`, :class:`~bibble.fields.field_sorter.FieldSorter`,
and :class:`~bibble.fields.field_substitutor.FieldSubstitutor`.


Files
-----

The files module handles files that are mentioned as part of entries.
:class:`~bibble.files.path_reader.PathReader` converts `file` fields into absolute ``Path``'s,
while :class:`~bibble.files.path_writer.PathWriter` makes them relative to defined library roots, and then converts them
to strings for writing into bibtex files.
:class:`~bibble.files.online.OnlineDownloader` takes mentioned urls of `online` entries and downloads pdf's of them,
adding the paths of those pdfs to the entry.


Latex
-----

This module provides :class:`~bibble.latex.reader.LatexReader` and :class:`~bibble.latex.writer.LatexWriter`,  which are refactored versions
of ``bibtexparser``'s originals. They provide latex decoding and encoding for entries.
(I prefer to write bibtex in straight unicode, and then encode as latex when needed).


Metadata
--------

This module handles various aspects of entry metadata. eg: Tags, Isbns, Key locking, Entry sorting,
and pdf/epub metadata writing.


People
------

This module provides refactored (from ``bibtexparser``) author/editor splitting/joining of 
people, and parts of names. It also, through :class:`~bibble.people.name_sub.NameSubstitutor`, allows for
keeping a master list of misspelled names and their correct spellings.


