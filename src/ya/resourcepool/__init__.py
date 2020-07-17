"""Public API for ya.resourcepool."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import singledispatch
from typing import Any, Callable, Generator, Iterable, Optional, Union

__version__ = '0.0.0'


PolicyT = Union[Iterable, 'AllocationPolicy', 'RetentionPolicy', 'FailPolicy']


class ResourcePool:
    """The resource pool."""
    __slots__ = 'policies'.split()

    def __init__(self: ResourcePool, *args: PolicyT) -> None:
        """Initialize the resource pool."""
        self.policies = Policies()
        for arg in args:
            _policy(arg, self.policies)

    @contextmanager
    def __call__(self: ResourcePool) -> Generator:
        """Temporarily allocate a resource."""
        try:
            yield
        finally:
            pass


class AllocationPolicy:
    """Base class for allocation policies."""


def dynamic(ctor: Callable[[], Any], max_: Optional[int] = None) -> AllocationPolicy:
    """Create an instance of a dynamic allocation poliy."""


def fixed(resources: Iterable) -> AllocationPolicy:
    """Create an instance of a fixed allocation poliy."""


class RetentionPolicy:
    """Base class for retention policies."""


class FailPolicy:
    """Base class for fail policies."""


class ResourcePoolExhausted(RuntimeError):
    """Exception class to be raised when resource allocation fails."""


@dataclass
class Policies:
    """Class for storing a collection of policies."""
    allocation: AllocationPolicy = None
    retention: RetentionPolicy = None
    fail: FailPolicy = None


@singledispatch
def _policy(arg: Any, policies: Policies) -> None:
    raise NotImplementedError(f'Not a valid policy: {arg}')


@_policy.register
def _alloc_policy(arg: AllocationPolicy, policies: Policies) -> None:
    pass


@_policy.register
def _iterable(arg: Iterable, policies: Policies) -> None:
    _policy(fixed(arg), policies)

# vim:et sw=4 ts=4
