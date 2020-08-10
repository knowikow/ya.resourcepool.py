"""Implementation of the ResourcePool class."""
from __future__ import annotations

import threading
from collections import deque
from contextlib import contextmanager, suppress
from time import monotonic as now
from typing import (Any, Callable, Generator, Generic, Iterable, Optional,
                    TypeVar)
from weakref import finalize

__version__ = '0.1.1'
__all__ = 'ResourcePool ResourcePoolEmpty'.split()

R = TypeVar('R')  # pragma: no mutate


class ResourcePool(Generic[R]):
    """The resource pool."""
    __slots__ = (
        '__pool',
        '__alloc',
        '__check',
        '__dealloc',
        '__lock',
        '__cond',
        '__min',
        '__max',
        '__maxage',
    )

    def __init__(self: ResourcePool,
                 *,
                 alloc: Callable[[], R] = None,
                 dealloc: Callable[[R], Any] = None,
                 check: Callable[[R], bool] = None,
                 init: Optional[Iterable] = None,
                 minsize: Optional[int] = None,
                 maxsize: Optional[int] = None,
                 maxage: Optional[float] = None) -> None:
        """Initialize the object."""
        self.__lock = threading.Lock()
        self.__cond = threading.Condition(self.__lock)
        self.__pool = deque()
        if alloc is None:
            self.__alloc = self.__wait_blocking
        else:
            self.__alloc = lambda _: alloc()
        self.__check = check or true
        self.__dealloc = dealloc or noop

        if not init:
            init = []

        if alloc and minsize:
            while len(init) < minsize:
                init.append(alloc())
        self.__pool.extendleft(
            finalize(self.__pool, self.__dealloc, resource)
            for resource in init)

        self.__maxage = maxage
        self.__max = maxsize
        if minsize is None:
            minsize = maxsize
        self.__min = minsize

        if self.__max is not None:
            threading.Thread(target=self.__gc, daemon=True).start()

    def pop(self: ResourcePool, timeout: Optional[float] = None) -> R:
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
                    return self.__detach(wrapper)

    def push(self: ResourcePool, resource: R) -> None:
        """Return a resource into the pool."""
        wrapper = finalize(self.__pool, self.__dealloc, resource)
        with self.__cond:
            self.__pool.append(wrapper)
            if self.__maxage:
                threading.Timer(self.__maxage, self.__drop,
                                (wrapper, )).start()
            self.__cond.notify_all()

    @contextmanager
    def __call__(self: ResourcePool, timeout: float = None) -> Generator:
        """Temporarily allocate a resource."""
        resource = self.pop(timeout)
        try:
            yield resource
        finally:
            self.push(resource)

    def __len__(self: ResourcePool) -> int:
        """Get the number of currently pooled resources."""
        return len(self.__pool)

    def __wait_blocking(self: ResourcePool, timeout: Optional[float]) -> R:
        def _nonempty() -> bool:
            return len(self.__pool) > 0

        if timeout is None:
            raise ResourcePoolEmpty
        elif timeout <= 0:
            timeoutend = None
            timeout = None
        else:
            timeoutend = now() + timeout

        while True:
            with suppress(TypeError):
                timeout = timeoutend - now()

            with self.__cond:
                if not self.__cond.wait_for(_nonempty, timeout=timeout):
                    raise ResourcePoolEmpty

                wrapper = self.__pool.pop()
                with suppress(DeadResource):
                    obj = self.__detach(wrapper)
                    return obj

    def __gc(self: ResourcePool) -> None:
        def _max_size_exceeded() -> bool:
            return len(self.__pool) > self.__max

        while True:
            with self.__cond:
                self.__cond.wait_for(_max_size_exceeded)
                while len(self.__pool) > self.__min:
                    wrapper = self.__pool.popleft()
                    wrapper()

    def __detach(self: ResourcePool, wrapper: finalize) -> R:
        """Detach and return the wrapped resource."""
        try:
            _, _, args, _ = wrapper.detach()
        except TypeError as ex:
            raise DeadResource from ex
        else:
            resource = args[0]
            if not self.__check(resource):
                raise DeadResource

            return resource

    def __drop(self: ResourcePool, wrapper: finalize) -> None:
        """Remove and dstroy the given object."""
        with suppress(ValueError), self.__lock:
            if self.__min is None or len(self) > self.__min:
                self.__pool.remove(wrapper)
                wrapper()


class DeadResource(Exception):
    """Exception that will be raised when trying to get dead resource."""


class ResourcePoolEmpty(Exception):
    """No more resources available."""


def noop(*args: Any, **kwds: Any) -> None:
    """A function that does nothing at all."""


def true(*args: Any, **kwds: Any) -> bool:
    """A function only returns True."""
    return True


# vim:et sw=4 ts=4
