.. image:: https://github.com/knowikow/ya.resourcepool.py/workflows/build/badge.svg
   :target: https://github.com/knowikow/ya.resourcepool.py/workflows/build/badge.svg

=========================
Yet Another Resource Pool
=========================

A configurable resource pool.

All the code examples assume::

   >>> from ya.resourcepool import *


Simple use case::
================

::

   >>> class R:
   >>>     def __init__(self):
   >>>         self._alive = True
   >>>     def use(self):
   >>>         pass
   >>>     def close(self):
   >>>         self._alive = False
   >>>     def alive(self):
   >>>         return self._alive
   >>> pool = ResourcePool(R)
   >>> with pool() as obj:
   >>>     obj.use()


Points of variability
=====================

The ``ResourcePool`` class is highly configurable through multiple points of variability:

- allocation
- retention and deallocation
- allocation failure


Resource allocation policy
--------------------------

- ``fixed``: Allocate a fixed number of resources at construction time::

   >>> resources = [R() for _ in range(10)]
   >>> pool = ResourcePool(fixed(resources))
   >>> pool = ResourcePool(resources)  # short form of the above

- ``dynamic``: Dynamically allocate resources up to a maximum amount::

   >>> pool = ResourcePool(dynamic(R, 10))

- ``dynamic``, unlimited: Dynamically allocate an unlimited amount of resources::

   >>> pool = ResourcePool(dynamic(R))
   >>> pool = ResourcePool(R)  # short form of the above


Deallocation and retention policy
---------------------------------

The method for deallocating a resource is given as an argument to the retention policy, with ``close`` as the default.

- ``indefinite``: Keep all allocated resources for the active lifetime of the pool. This is the default, and it is also the only allowed policy for a fixed pool size. If the deallocation method is not ``close``, then this policy has to be given explicitly::

   >>> pool = ResourcePool(dynamic(R), indefinite(R.close))
   >>> pool = ResourcePool(R)  # short form of the above

- ``timed``: Deallocate resources when they have not been in use for a given amount of time in seconds::

   >>> pool = ResourcePool(R, timed(R.close, 60))  # Deallocate resources that have not been in use for 60 seconds

- ``sized``: Reduce the pool to a given fraction when it grows larger than a given size::

   >>> pool = ResourcePool(R, sized(R.close, 100, 3))  # reduce the pool size to one third when the pooled size exceeds 100 


Allocation failure
------------------

When using one of the allocation policies ``fixed`` or ``dynamic (limited)``, then allocation may fail. By default, this will raise an exception::

   >>> pool = ResourcePool([])  # empty fixed resource list
   >>> with pool() as r:
   >>>     pass
   Traceback (most recent call last):
       ...
   ResourcePoolExhausted: ...

This can be changed with the allocation failure policy:

- ``raising``: Raises an exception of type ``ResourcePoolExhausted``
- ``blocking``: This blocks an internal ``threading.Condition`` object that will be notified when a resource becomes available. This policy takes an optional timeout after which a ``ResourcePoolExhausted`` exception will be raised::

   >>> pool = ResourcePool([], blocking)
   >>> with pool() as r:
   >>>     pass  # this will block forever because there are no resources
   >>> pool = ResourcePool([], blocking(10))
   >>> with pool() as r:
   >>>     pass  # Timeout is 10 seconds
   Traceback (most recent call last):
       ...
   ResourcePoolExhausted: ...
