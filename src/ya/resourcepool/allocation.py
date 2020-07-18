"""Implementation of the allocation policies."""
from typing import Any, Callable, Iterable, Optional


class AllocationPolicy:
    """Base class for allocation policies."""


def dynamic(ctor: Callable[[], Any],
            max_: Optional[int] = None) -> AllocationPolicy:
    """Create an instance of a dynamic allocation poliy."""


def fixed(resources: Iterable) -> AllocationPolicy:
    """Create an instance of a fixed allocation poliy."""


# vim:et sw=4 ts=4
