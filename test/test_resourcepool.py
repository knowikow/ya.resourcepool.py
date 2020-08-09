"""Tests for the resourcepool library."""
from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor
from time import monotonic as now
from time import sleep
from typing import Any
from unittest.mock import MagicMock, call

import pytest

from ya.resourcepool import ResourcePool, ResourcePoolEmpty  # noqa: I003


class R(int):
    """A dummy resource to be used in the tiests."""
    lock = threading.Lock()
    current = 0
    deallocated = []

    def __new__(cls: type, *args: Any, **kwds: Any) -> R:
        """Create the dummy."""
        with R.lock:
            instance = super().__new__(cls, R.current)
            R.current += 1
        return instance

    def __init__(self: R) -> None:
        """Initialize the dummy."""
        self.alive = True

    def close(self: R) -> None:
        """Close the resource."""
        self.alive = False
        R.deallocated.append(self)
        return self

    @classmethod
    def create(cls: type, n: int = 1) -> list:
        """Create a list of dummy objects."""
        return [R() for _ in range(n)]

    @staticmethod
    def set(n: int) -> None:
        """Set the current counter to a ne value."""
        with R.lock:
            R.current = n


@pytest.fixture(autouse=True)
def reset_dummy() -> None:
    """Reset the counter of the dummy resource class."""
    try:
        yield
    finally:
        R.set(0)
        R.deallocated.clear()


def test_no_resources() -> None:
    """Test exception raised when there are no resources available.

    Given:
        - a default-initialized resource pool
        - there are no resources currently available in the pool
        - and the pool has no way of creating a new
          resource (i. e., `alloc` was not given on construction)
    When:
        - client code attempts to get a resurce without giving
          the `timeout` argument
    Then:
        - an exception of type `ResourcePoolEmpty` will be raised
    """
    pool = ResourcePool()

    with pytest.raises(ResourcePoolEmpty):
        pool.pop()


def test_no_resources_with_timeout() -> None:
    """Test exception raised with a timeout when there are no resources available.

    Given:
        - a default-initialized resource pool
        - there are no resources currently available in the pool
        - and the pool has no way of creating a new
          resource (i. e., `alloc` was not given on construction)
    When:
        - client code attempts to get a resurce with a timeout
    Then:
        - an exception of type `ResourcePoolEmpty` will be raised
        - the exception will be raised after the timeout period
    """
    pool = ResourcePool()
    timeout = 1

    start = now()
    with pytest.raises(ResourcePoolEmpty):
        pool.pop(timeout=timeout)

    duration = now() - start
    assert duration == pytest.approx(timeout, abs=1e-2)


def test_no_resources_eternal_timeout() -> None:
    """Test behaviour with an infinite timeout when there are no resources available.

    Given:
        - a default-initialized resource pool
        - there are no resources currently available in the pool
        - and the pool has no way of creating a new
          resource (i. e., `alloc` was not given on construction)
    When:
        - client code attempts to get a resurce with an infinite timeout (=0)
    Then:
        - no exception will be raised
        - the `pop` method will block until a resource is made available
          by another thread
    """
    pool = ResourcePool()
    timeout = 1

    threading.Timer(timeout, lambda: pool.push(R())).start()

    start = now()
    with pool(timeout=0) as r:
        assert r == 0

    duration = now() - start
    assert duration == pytest.approx(timeout, abs=1e-2)


def test_limited_resources_with_timeout() -> None:
    """Test mltiple threads trying to allocate from a limited resource pool.

    Given:
        - a resource pool with al limited set of resources
    When:
        - multiple threads try to get a resurce with a timeout
        - and thread receiving the resource return them to the pool
          immediately, thus not triggering a timeout for other threads
    Then:
        - all threads will get a resource in time
    """
    def use(x: int) -> int:
        """Allocate a resource, ignore it, and return the given argument."""
        with pool(timeout=timeout):
            return x

    pool = ResourcePool(init=R.create(1), check=lambda r: r.alive)
    timeout = 2

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = executor.map(use, range(10))
        results = set(futures)

    assert len(results) == 10


def test_closed_resources_with_timeout() -> None:
    """Test multiple threads trying to allocate from a limited resource pool.

    Given:
        - a resource pool with al limited set of a single resource
        - the single resource is invalid
    When:
        - multiple threads try to get a resurce with a timeout
        - another thread pushes a valid resource
        - and thread receiving the resource return them to the pool
          immediately, thus not triggering a timeout for other threads
    Then:
        - all threads will get a resource in time
    """
    def use(x: int) -> int:
        """Allocate a resource, ignore it, and return the given argument."""
        with pool(timeout=timeout):
            sleep(sleeptime)
            return x

    def push(resource: R) -> None:
        """Push one more resource."""
        sleep(sleeptime)
        pool.push(resource)

    alive, dead = R.create(2)
    dead.close()
    pool = ResourcePool(init=[], check=lambda r: r.alive)
    timeout = 2
    sleeptime = 0.1

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = executor.map(use, range(10))
        executor.submit(push, dead)
        executor.submit(push, alive)
        results = set(futures)

    assert len(results) == 10


def test_closed_resources_with_timeout_exception() -> None:
    """Test multiple threads trying to allocate from a limited resource pool.

    Given:
        - a resource pool with al limited set of a single resource
        - the single resource is invalid
    When:
        - multiple threads try to get a resurce with a timeout
    Then:
        - an exception of type `ResourcePoolEmpty` will be raised
    """
    def use(x: int) -> int:
        """Allocate a resource, ignore it, and return the given argument."""
        with pool(timeout=timeout):
            sleep(sleeptime)
            return x

    def push(resource: R) -> None:
        """Push one more resource."""
        sleep(sleeptime)
        pool.push(resource)

    dead = R()
    dead.close()
    pool = ResourcePool(init=[], check=lambda r: r.alive)
    timeout = 2
    sleeptime = 0.1

    start = now()

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = executor.map(use, range(10))
        executor.submit(push, dead)
        with pytest.raises(ResourcePoolEmpty):
            set(futures)

    duration = now() - start
    assert duration == pytest.approx(timeout, abs=1e-2)


def test_init() -> None:
    """Test using an initial resource list.

    Given:
        - a resource pool with an initial list of resources
        - and the pool has no way of creating a new
          resource (i. e., `alloc` was not given on construction)
    When:
        - client code attempts to get multiple resurces
    Then:
        - the resources will be the ones from the original pool
    """
    init = R.create(10)

    pool = ResourcePool(init=init)

    for x in range(100):
        with pool() as r:
            assert r == 0


def test_minsize() -> None:
    """Test generation of initial values."""
    pool = ResourcePool(alloc=R, minsize=3)
    assert len(pool) == 3


def test_minsize_init() -> None:
    """Test generation of initial values."""
    pool = ResourcePool(init=[1, 2, 3], alloc=R, minsize=6)
    assert len(pool) == 6


def test_call_allocator() -> None:
    """Allocator is called without arguments.

    Given:
        - a resource pool with an `alloc` function, enabling
          creation of new resources
    When:
        - client code attempts to get a resurce
    Then:
        - the allocation method had been called
    """
    pool = ResourcePool(alloc=R)

    resource = pool.pop()

    assert resource == 0


def test_provide_additional_resource() -> None:
    """Resources are actually reused after returning."""
    allocate = MagicMock()
    allocate.side_effect = R.create(4)
    pool = ResourcePool(alloc=allocate)

    resources = [pool.pop() for _ in range(3)]

    R.set(100)
    pool.push(R())

    resources.append(pool.pop())
    resources.append(pool.pop())

    allocate.assert_has_calls([call(), call(), call(), call()])
    assert resources == [0, 1, 2, 100, 3]


def test_reuse() -> None:
    """Resources are actually reused after returning."""
    allocate = MagicMock()
    allocate.side_effect = [1, 2, 3, 4]
    pool = ResourcePool(alloc=allocate)

    resources = []
    for _ in range(3):
        with pool() as r:
            resources.append(r)

    pool.push(100)

    resources.append(pool.pop())
    for _ in range(2):
        with pool() as r:
            resources.append(r)

    allocate.assert_called_once()
    assert resources == [1, 1, 1, 100, 1, 1]


def test_max_size() -> None:
    """Check that resources are destroyed when the pool overflows.

    Given:
        - a resource pool initialized with a max poolsize and a dealloc function
    When:
        - more resources than the max poolsize are acquired
        - and the resources are all put back into the pool
    Then:
        - the surplus resources will be reset using the dealloc function
    """
    pool = ResourcePool(alloc=R, dealloc=R.close, maxsize=1)
    a, b = pool.pop(), pool.pop()
    pool.push(a)
    pool.push(b)

    sleep(1)  # wait for pool's gc thread
    assert len(R.deallocated) == 1
    assert a in R.deallocated
    assert not a.alive
    assert b.alive


def test_max_size_no_overflow() -> None:
    """Check that resources are not destroyed unless the pool overflows.

    Given:
        - a resource pool initialized with a max poolsize and a dealloc function
    When:
        - the maxsize amount of resources are allocated
        - and the resources are all put back into the pool
    Then:
        - no resources will be reset using the dealloc function
    """
    pool = ResourcePool(alloc=R, dealloc=R.close, minsize=0, maxsize=2)
    a, b = pool.pop(), pool.pop()
    pool.push(a)
    pool.push(b)

    sleep(1)  # wait for pool's gc thread
    assert len(R.deallocated) == 0
    assert a.alive
    assert b.alive


def test_minmax_size() -> None:
    """Check that resources are destroyed when the pool overflows.

    Given:
        - a resource pool initialized with a min and a max poolsize and a dealloc function
    When:
        - more resources than the max poolsize are acquired
        - and the resources are all put back into the pool
    Then:
        - the surplus resources will be reset using the dealloc function
    """
    pool = ResourcePool(alloc=R, dealloc=R.close, minsize=1, maxsize=2)
    a, b, c = pool.pop(), pool.pop(), pool.pop()
    pool.push(a)
    pool.push(b)
    pool.push(c)

    sleep(1)  # wait for pool's gc thread

    assert len(R.deallocated) == 2
    assert a in R.deallocated
    assert not a.alive
    assert b in R.deallocated
    assert not b.alive
    assert c.alive


def test_maxage() -> None:
    """Test maxage parameter."""
    size = 5
    pool = ResourcePool(alloc=now, maxage=1)

    resources = [pool.pop() for _ in range(size)]
    for r in resources:
        pool.push(r)

    assert len(pool) == size
    sleep(1.1)
    assert len(pool) == 0


def test_maxage_minsize() -> None:
    """Test maxage parameter with minimum size."""
    size = 5
    pool = ResourcePool(alloc=now, maxage=1, minsize=1)

    resources = [pool.pop() for _ in range(size)]
    assert len(pool) == 0

    for r in resources:
        sleep(0.1)
        pool.push(r)

    assert len(pool) == size
    sleep(2)
    assert len(pool) == 1
    expected = max(resources)
    actual = pool.pop()
    assert actual == expected


# vim:et sw=4 ts=4
