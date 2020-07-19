.. image:: https://github.com/knowikow/ya.resourcepool.py/workflows/tests/badge.svg
   :target: https://github.com/knowikow/ya.resourcepool.py/workflows/tests/badge.svg

=========================
Yet Another Resource Pool
=========================

A configurable resource pool. The ``ResourcePool`` class can allocate resources using a configurable function,
store them for later use, and also free them if the pool gets too large.

All the code examples assume::

   >>> from ya.resourcepool import *
   >>> import threading
   >>> 
   >>> class R(int):
   >>>     lock = threading.Lock()
   >>>     current = 0  # last generated number
   >>>     deallocated = []
   >>> 
   >>>     def __new__(cls, *args, **kwds):
   >>>         with R.lock:
   >>>             R.current += 1
   >>>             instance = super().__new__(cls, R.current)
   >>>         return instance
   >>> 
   >>>     def __init__(self: R) -> None:
   >>>         self.alive = True
   >>> 
   >>>     def close(self: R) -> None:
   >>>         self.alive = False
   >>>         R.deallocated.append(self)
   >>>         return self
   >>> 
   >>>     def use(self):
   >>>         print(f'Using resource {self}')
   >>>         return self


Usage examples
==============

The most basic example only configures the method of allocation of the resource and uses
``ResourcePool.__call__()`` to get a resource from the pool::

   >>> pool = ResourcePool(alloc=R)
   >>> with pool() as obj:
   >>>     obj.use()

This assumes that the resource can be simply garbage collected, and that an unlimited
amount can be allocated.

Note that ``ResourcePool.__call__()`` is supposed to be used as a context manager. If that is not needed,
the methods ``ResourcePool.pop()`` and ``ResourcePool.push()`` can be used::

   >>> pool = ResourcePool(alloc=R)
   >>> obj = pool.pop()
   >>> obj.use()
   >>> pool.push(obj)

Note that ``ResourcePool.pop()`` transfers ownership of the resource to the client code, and it is the client's
responsibility to either clean up the resource or to return it to the pool using ``ResourcePool.push()``.

The ``ResourcePool.push()`` method can also be used to add new resource to the pool::

   >>> pool = ResourcePool()  # no alloc argument
   >>> obj = R()              # create/allocate a resource
   >>> pool.push(obj)         # push without preceding pop

The ``ResourcePool.__call__()`` method is actually implemented in terms of ``pop``and ``push``.


Limited resource set
--------------------

If there is only a limited amount of resource instances available, a set can be provided with the `ìnit``argument::

   >>> resources = [R()]
   >>> pool = ResourcePool(init=resources)
   >>> with pool() as obj:
   >>>     obj.use()

In that case, no new resources will be allocated, and only the ones given in the initializer will be used.

By default, trying to get a resource from a limited pool will raise an exception of type ``ResourcePoolEmpty``
if there is no free resource available at the moment::

   >>> pool = ResourcePool(init=[])  # note the empty list
   >>> with pool() as obj:
   >>>     obj.use()
   Traceback (most recent call last):
      ...
   ya.resourcepool.ResourcePoolEmpty

Alternatively, a timeout in seconds can be given::

   >>> resources = [R()]
   >>> pool = ResourcePool([])  # empty list
   >>> with pool(timeout=10) as obj:
   >>>     obj.use()
   Traceback (most recent call last):
      ...
   ya.resourcepool.ResourcePoolEmpty

This will raise the exception only after the given timeout of ten seconds. Note that the timeout is a
floating point number, so fractions of seconds are possible. A timeout of zero or less will block forever
or until a resource becomes available.

The `ìnit``argument can be combined with the ``alloc`` argument::

   >>> resources = [R()]
   >>> pool = ResourcePool(init=resources, alloc=R)
   >>> with pool() as obj:
   >>>     obj.use()

This will use the initial resource list and only allocate new ones if the initial resources are exhausted.
