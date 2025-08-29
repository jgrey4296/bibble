.. -*- mode: ReST -*-

.. _model:

================
Model Extensions
================

.. contents:: Contents
   :local:


To ease certain transforms, bibble adds :class:`~bibble.model.MetaBlock` and
:class:`~bibble.model.FailedBlock`.

Metablock is a non-printing block that is inserted into a library.
This is mainly because default ``bibtexparser`` middlewares create new ``Library`` objects,
which means you can't subclass ``Library`` to add metadata there. A ``Metablock`` is just a ``Block``, so it can be copied to new libraries easily.
