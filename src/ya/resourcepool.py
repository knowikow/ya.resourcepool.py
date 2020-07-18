"""Implementation of the ResourcePool class."""
from __future__ import annotations

import threading
from collections import deque
from contextlib import contextmanager, suppress
from time import monotonic as now
from typing import (Any, Callable, Generator, Generic, Iterable, Optional,
                    Tuple, TypeVar, Union)
from weakref import finalize

__version__ = '0.0.0'
__all__ = 'ResourcePool ResourcePoolEmpty'.split()

R = TypeVar('R')


class ResourcePool(Generic[R]):
    """The resource pool."""
    __slots__ = '__pool __alloc __dealloc __lock __cond __gc_cond __min __max'.split(
    )

    def __init__(self: ResourcePool,
                 *,
                 alloc: Callable[[], R] = None,
                 dealloc: Callable[[R], Any] = None,
                 init: Iterable = [],
                 size: Union[int, Tuple[int, int]] = None) -> None:
        """Initialize the object."""
        def _max_size_exceeded() -> bool:
            return len(self.__pool) > self.__max

        def _gc() -> None:
            while self.__max is not None:
                self.__gc_cond.wait_for(_max_size_exceeded)

                with suppress(IndexError):
                    while len(self.__pool) > self.__min:
                        self.__pool.pop().finalize()

        self.__lock = threading.Lock()
        self.__cond = threading.Condition(self.__lock)
        self.__gc_cond = threading.Condition(self.__lock)
        self.__pool = deque()
        if alloc is None:
            self.__alloc = self.__wait_blocking
        else:
            self.__alloc = lambda _: alloc()
        self.__dealloc = dealloc or noop
        self.__pool.extendleft(
            ResourceWrapper(resource, self.__dealloc) for resource in init)

        try:
            self.__min, self.__max = size
        except TypeError:
            self.__min = self.__max = size
        threading.Thread(target=_gc, daemon=True).start()

    def pop(self: ResourcePool, timeout: float = None) -> R:
        """Get a resource from the pool.

        The returned resource will no longer be under the control of the pool. It is the
        responsibility of the client to either properly deallocate the resource or to return
        it into the pool using ``ResourcePool.push()``.
        """
        while True:
            try:
                with self.__lock:
                    wrapper = self.__pool.pop()
            except IndexError:
                return self.__alloc(timeout)
            else:
                with suppress(DeadResource):
                    return wrapper.pop()

    def push(self: ResourcePool, resource: R) -> None:
        """Return a resource into the pool."""
        wrapper = ResourceWrapper(resource, self.__dealloc)
        with self.__cond:
            self.__pool.appendleft(wrapper)
            self.__cond.notify()
        with self.__gc_cond:
            self.__gc_cond.notify()

    @contextmanager
    def __call__(self: ResourcePool, timeout: float = None) -> Generator:
        """Temporarily allocate a resource."""
        resource = self.pop(timeout)
        try:
            yield resource
        finally:
            self.push(resource)

    def __wait_blocking(self: ResourcePool, timeout: Optional[float]) -> R:
        def _nonempty() -> bool:
            return len(self.__pool) > 0

        if timeout is None:
            raise ResourcePoolEmpty
        elif timeout <= 0:
            timeout = None

        with self.__cond:
            while True:
                start = now()
                if not self.__cond.wait_for(_nonempty, timeout=timeout):
                    raise ResourcePoolEmpty

                wrapper = self.__pool.pop()
                try:
                    return wrapper.pop()
                except DeadResource:
                    timeout -= now() - start


class ResourceWrapper(Generic[R]):
    """A wrapper for a resource that is managed by the ResourceWrapper."""
    def __init__(self: ResourceWrapper, resource: R,
                 dealloc: Callable[[R], Any]) -> None:
        """Initialize the object."""
        self.finalize = finalize(self, dealloc, resource)

    def pop(self: ResourceWrapper) -> R:
        """Detach and return the wrapped resource."""
        try:
            _, _, args, _ = self.finalize.detach()
        except TypeError as ex:
            raise DeadResource from ex
        else:
            return args[0]


class DeadResource(Exception):
    """Exception that will be raised when trying to get dead resource."""


class ResourcePoolEmpty(Exception):
    """No more resources available."""


def noop(*args: Any, **kwds: Any) -> None:
    """A function that does nothing at all."""


# vim:et sw=4 ts=4
