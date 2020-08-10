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
   ...     lock = threading.Lock()
   ...     current = 0  # last generated number
   ...     deallocated = []
   ...
   ...     def __new__(cls, *args, **kwds):
   ...         with R.lock:
   ...             R.current += 1
   ...             instance = super().__new__(cls, R.current)
   ...         return instance
   ...
   ...     def __init__(self):
   ...         self.alive = True
   ...
   ...     def close(self):
   ...         self.alive = False
   ...         R.deallocated.append(self)
   ...         return self
   ...
   ...     def use(self):
   ...         print(f'Using resource {self}')
   ...         return self


Usage examples
==============

The most basic example only configures the method of allocation of the resource and uses
``ResourcePool.__call__()`` to get a resource from the pool::

   >>> pool = ResourcePool(alloc=R)
   >>> with pool() as obj:
   ...     obj.use()
   Using resource ...

This assumes that the resource can be simply garbage collected, and that an unlimited
amount can be allocated.

Note that ``ResourcePool.__call__()`` is supposed to be used as a context manager. If that is not needed,
the methods ``ResourcePool.pop()`` and ``ResourcePool.push()`` can be used::

   >>> pool = ResourcePool(alloc=R)
   >>> obj = pool.pop()
   >>> obj.use()
   Using resource ...
   >>> pool.push(obj)

Note that ``ResourcePool.pop()`` transfers ownership of the resource to the client code, and it is the client's
responsibility to either clean up the resource or to return it to the pool using ``ResourcePool.push()``.

The ``ResourcePool.push()`` method can also be used to add new resource to the pool::

   >>> pool = ResourcePool()  # no alloc argument
   >>> obj = R()              # create/allocate a resource
   >>> pool.push(obj)         # push without preceding pop

The ``ResourcePool.__call__()`` method is actually implemented in terms of ``pop`` and ``push``.


Limited resource sets
---------------------

If there is only a limited amount of resource instances available, a set can be provided with the ``init`` argument::

   >>> resources = [R()]
   >>> pool = ResourcePool(init=resources)
   >>> with pool() as obj:
   ...     obj.use()
   Using resource ...

In that case, no new resources will be allocated, and only the ones given in the initializer will be used.

By default, trying to get a resource from a limited pool will raise an exception of type ``ResourcePoolEmpty``
if there is no free resource available at the moment::

   >>> pool = ResourcePool(init=[])  # note the empty list
   >>> with pool() as obj:
   ...     obj.use()
   Traceback (most recent call last):
      ...
   ya.resourcepool.ResourcePoolEmpty

Alternatively, a timeout in seconds can be given::

   >>> pool = ResourcePool()  # an empty list is actually the default for init
   >>> with pool(timeout=5) as obj:
   ...     obj.use()
   Traceback (most recent call last):
      ...
   ya.resourcepool.ResourcePoolEmpty

This will raise the exception only after the given timeout of five seconds. Note that the timeout is a
floating point number, so fractions of seconds are possible. A timeout of zero or less will block forever
or until a resource becomes available.

The ``init`` argument can be combined with the ``alloc`` argument::

   >>> resources = [R()]
   >>> pool = ResourcePool(init=resources, alloc=R)
   >>> with pool() as obj:
   ...     obj.use()
   Using resource ...

This will use the initial resource list and only allocate new ones if the initial resources are exhausted.


Resource deallocation
---------------------

Resources will usually have to be deallocated at some point. The function to do this can be
given with the ``dealloc`` initializer argument::

   >>> pool = ResourcePool(alloc=R, dealloc=R.close)
   >>> with pool() as obj:
   ...     obj.use()
   Using resource ...

This will call ``R.close()`` when the pool gets garbage collected for all resources currently managed by the pool.


Resource retention policy
-------------------------

Surplus resources can be deallocated by giveng the ``maxsize`` argument to the pool initializer::

   >>> pool = ResourcePool(alloc=R, maxsize=100)

When a ``maxsize`` argument was given, and the pool size exceeds that number after returning a
resource to the pool, all the surplus will be deallocated. This process will also use the optional ``dealloc``
argument, or will just remove it from the pool and have it garbage collected.

There is an additional argument ``minsize`` to control the amount of resources that will be deallocated
in the overflow case::

   >>> pool = ResourcePool(alloc=R, maxsize=100, minsize=50)

This will reduce the pool size to 50 by deallocating surplus resources when the size exceeds 100 after
a ``push`` operation.

An additional argument ``maxage`` can be used to set the maximum time a resource shall be kept in the
pool. The ``minsize`` argument can be used to guarantee a minimal set of pooled resources,
regardless of age.


Resource alive check
--------------------

It is possible to check the status of any pooled resources before returning them from ``pop``. This
can be configured using the ``check`` argument::

   >>> pool = ResourcePool(alloc=R, check=lambda resource: resource.alive)
   >>> with pool() as obj:
   ...     obj.use()
   Using resource ...

The object given in ``check`` must be a callable that takes a resource instance and returns a truthy
value. It will be called for a result value candidate of ``pop`` before it is returned, and if the
result is convertible to ``False``, then the resource is considered dead and will be discarded
without calling any ``dealloc`` procedure. ``pop`` will then continue trying to get a valid resource.


Shooting yourself in the foot
=============================

It is possible to block a thread indefinitely by having an empty fixed-size pool and using a timeout of 0::

   >>> pool = ResourcePool()
   >>>
   >>> def allocate(pool):
   ...     pool.push(R())
   >>>
   >>> threading.Timer(5, allocate, (pool,)).start()
   >>>
   >>> with pool(timeout=0) as obj:
   ...     obj.use()
   Using resource ...

This code would block forever without the ``Timer`` thread that adds a new object to the pool after 5 seconds.
