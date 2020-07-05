.. image:: https://github.com/knowikow/ya.dotdict.py/workflows/build/badge.svg
   :target: https://github.com/knowikow/ya.dotdict.py/workflows/build/badge.svg

===================
Yet Another DotDict
===================

A Python library providing attribute access for dictionaries.
The library provides these classes:

- ``ya.dotdict.DotDict`` as a replacement for ``dict`` and ``collections.defaultdict``
- ``ya.dotdict.DotDictMixin``: a mixin class that can be used to add attribute-style access to any dict-like class.
  ``ya.dotdict.DotDict`` is implemented in terms of this mixin class

All the code examples assume::

   >>> from ya.dotdict import *

Simple use case: access dictionary items as attributes
======================================================

``DotDict`` can be used as a replacement for ``dict``::

   >>> d = DotDict()
   >>> d['spam'] = 'eggs'
   >>> d.spam
   'eggs'
   >>> d.spam = 100
   >>> d['spam']
   100

Deleting attributes also works as expected::

   >>> del d.spam
   >>> d.spam
   Traceback (most recent call last):
      ...
   AttributeError: spam


Create default values (like ``collections.defaultdict``)
========================================================

``DotDict`` can be used as a replacement for ``defaultict``::

   >>> d = DotDict(lambda: 'eggs')
   >>> d.spam
   'eggs'
   >>> d.spam = 100
   >>> d['spam']
   100
   >>> d._default_factory = lambda: 'foo'
   >>> d.bar
   'foo'

If the default value factory takes an argument, then the key is passed to it::

   >>> d._default_factory = lambda key: [key, 1000]
   >>> d.foo
   ['foo', 1000]


If the default value factory takes more than one argument, a TypeError will be raised::

   >>> d._default_factory = lambda x, y: [x, y]
   Traceback (most recent call last):
      ...
   TypeError: defult_factory can only take zero or one argument

``DotDictMixin``
================

A mixin class to provide attribute access to dict-like classes. ``DotDict`` is implemented using ``DotDictMixin`` like this::

   class DictClass(DotDictMixin, dict): pass

