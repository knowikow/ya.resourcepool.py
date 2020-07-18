"""Tests for the resourcepool library."""
from unittest.mock import MagicMock, call

import pytest
from ya.resourcepool import ResourcePool, ResourcePoolEmpty  # noqa: I003


def test_no_resources() -> None:
    """Test exception raise when there are no resources available."""
    pool = ResourcePool()

    with pytest.raises(ResourcePoolEmpty):
        pool.pop()


def test_init() -> None:
    """Test using an initial resource list."""
    init = range(10)

    pool = ResourcePool(init=init)

    for x in range(100):
        with pool() as r:
            assert r == x % 10


def test_timeout() -> None:
    """Test timeout."""
    pool = ResourcePool()

    with pytest.raises(ResourcePoolEmpty):
        pool.pop(timeout=1)


def test_call_allocator() -> None:
    """Allocator is called without arguments."""
    dummy = 'dummy resource'
    allocate = MagicMock()
    allocate.side_effect = [dummy]
    pool = ResourcePool(alloc=allocate)

    resource = pool.pop()

    allocate.assert_called_once_with()
    assert resource == dummy


def test_reuse() -> None:
    """Resources are actually reused after returning."""
    allocate = MagicMock()
    allocate.side_effect = [1, 2, 3, 4]
    pool = ResourcePool(alloc=allocate)

    resources = [pool.pop() for _ in range(3)]

    pool.push(2)

    resources.append(pool.pop())
    resources.append(pool.pop())

    allocate.assert_has_calls([call(), call(), call(), call()])
    assert resources == [1, 2, 3, 2, 4]


# vim:et sw=4 ts=4
