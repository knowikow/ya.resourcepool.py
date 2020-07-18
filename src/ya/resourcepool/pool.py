"""Implementation of the ResourcePool class."""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from functools import singledispatch
from queue import SimpleQueue
from typing import Any, Generator, Iterable, Union

from .allocation import AllocationPolicy
from .failure import FailurePolicy
from .retention import RetentionPolicy

PolicyT = Union[Iterable, AllocationPolicy, RetentionPolicy, FailurePolicy]


class ResourcePool:
    """The resource pool."""
    __slots__ = 'policies'.split()

    def __init__(self: ResourcePool, *args: PolicyT) -> None:
        """Initialize the resource pool."""
        self.policies = Policies()
        for arg in args:
            set_policy(arg, self.policies)

    @contextmanager
    def __call__(self: ResourcePool) -> Generator:
        """Temporarily allocate a resource."""
        try:
            yield
        finally:
            pass


@dataclass
class Policies:
    """Class for storing a collection of policies."""
    queue: SimpleQueue = None
    allocation: AllocationPolicy = None
    retention: RetentionPolicy = None
    fail: FailurePolicy = None


@singledispatch
def set_policy(arg: Iterable[Any], policies: Policies) -> None:
    """Set the given iterable as the init value on the given container."""


@set_policy.register
def set_alloc_policy(arg: AllocationPolicy, policies: Policies) -> None:
    """Set the given allocation policy on the given container."""


@set_policy.register
def set_retention_policy(arg: RetentionPolicy, policies: Policies) -> None:
    """Set the given retention policy on the given container."""


@set_policy.register
def set_failure_policy(arg: FailurePolicy, policies: Policies) -> None:
    """Set the given failure policy on the given container."""


# vim:et sw=4 ts=4
