.. image:: https://github.com/knowikow/ya.resourcepool.py/workflows/build/badge.svg
   :target: https://github.com/knowikow/ya.resourcepool.py/workflows/build/badge.svg

=========================
Yet Another Resource Pool
=========================

A configurable resource pool.

All the code examples assume::

   >>> from ya.resourcepool import *


Simple use case:
================

   >>> class R:
   >>>     def use(self)
   >>>         pass
   >>> pool = ResourcePool(R)
   >>> with pool.get() as obj:
   >>>     obj.use()


Points of variability
=====================

The ``ResourcePool`` class is highly configurable through multiple points of variability:

- allocation
- deallocation
- resource retention


Resource allocation policy
--------------------------

- ``fixed``: Allocate a fixed number of resources at construction time
- ``dynamic``: Dynamically allocate resources up to a maximum amount
- ``unlimited``: Dynamically allocate an unlimited amount of resources


Resource deallocation method
----------------------------

A function to deallocate resources.


Retention policy
----------------

- ``indefinite``:
- ``timed``:
- ``max_pooled``: 
