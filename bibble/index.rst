.. ..  index.rst -*- mode: ReST -*-

.. _index:

======
Bibble
======


.. contents:: Contents

.. _intro:

Introduction
------------

Bibble is a library of extension middlewares for `bibtexparser`_,
to simplify processing of `bibtex`_ files.


Overview
--------

The main areas of the library are:

1. :ref:`Bidirectional Middlewares <bidi>`
2. :ref:`Modified Readers and Writers <io>`
3. Miscellaneous :ref:`middlewares <middlewares>`.

Usage
-----

.. code:: python
 
   import pathlib as pl
   import bibble as BM
   from bibble.io import Reader, JinjaWriter

   # Make a stack of middlewares for reading and writing:
   stack = BM.PairStack()
   # stack.add(...)
   # stack.add(read=[], write=[])
   
   # Make a reader and writer:
   reader = Reader(stack)
   writer = JinjaWriter(stack)

   # read a bibtex file:
   lib = reader.read(pl.Path("a/bib/file.bib"))
   
   # And write it out:
   writer.write(lib, file=pl.Path("an/output.bib"))

   
Repo and Issues
---------------

The repo for doot can be found `here <https://github.com/jgrey4296/bib-middleware>`_.

If you find a bug, bug me, unsurprisingly, on the `issue tracker <https://github.com/jgrey4296/bib-middleware/issues>`_.



.. _indices:

Indices and Tables
------------------


* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. .. Main Sidebar Toctree
.. toctree::
   :maxdepth: 3
   :glob:
   :hidden:

   middlewares
   model
   [a-z]*/index
   
   
   _docs/*
   genindex
   modindex
   API Reference <_docs/_autoapi/bibble/index>


.. .. Links

.. _bibtexparser: https://bibtexparser.readthedocs.io/en/main/

.. _bibtex: https://www.bibtex.com

