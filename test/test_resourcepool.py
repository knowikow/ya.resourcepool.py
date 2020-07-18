"""Tests for the resourcepool library."""
from unittest.mock import MagicMock

import pytest
from ya.resourcepool import ResourcePool, ResourcePoolEmpty  # noqa: I003


def test_nothing() -> None:
    """Just a dummy test."""


def test_no_resources() -> None:
    """Test exception raise when there are no resources available."""
    pool = ResourcePool()

    with pytest.raises(ResourcePoolEmpty):
        pool.pop()


def test_call_allocator() -> None:
    """Allocator is called without arguments."""
    allocate = MagicMock()
    pool = ResourcePool(alloc=allocate)

    pool.pop()

    allocate.assert_called_once_with()


# vim:et sw=4 ts=4
