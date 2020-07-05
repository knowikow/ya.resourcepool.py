"""Implementation for dotdict"""
import inspect


__version__ = '1.0.2'


class DotDictMixin:
    """A mixin class for providing attribute access to dict-like classes."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as ex:
            raise AttributeError(name) from ex

    def __setattr__(self, name, value):
        if name in super().__dir__():
            super().__setattr__(name, value)
        else:
            self[name] = value

    def __delattr__(self, name):
        try:
            super().__delattr__(name)
        except AttributeError:
            del self[name]


class DotDict(DotDictMixin, dict):
    """Standard dictionary with attribute access.

    >>> d = DotDict()
    >>> d['spam'] = 'eggs'
    >>> d.spam
    'eggs'
    >>> d.spam = 100
    >>> d['spam']
    100
    """
    __slots__ = '__default_factory'.split()  # pragma: no mutate

    def __init__(self, default_factory=None, **kwds):
        super().__init__(**kwds)
        self.default_factory = default_factory

    def __missing__(self, key):
        if self.__default_factory is None:
            raise KeyError(key)

        result = self.__default_factory(key)
        self[key] = result
        return result

    def __set_default_factory(self, default_factory):
        """Factory function for default values."""
        if default_factory is None:
            self.__default_factory = None
        else:
            argc = len(inspect.signature(default_factory).parameters)
            if argc == 0:
                self.__default_factory = lambda _: default_factory()
            elif argc == 1:
                self.__default_factory = default_factory
            else:
                raise TypeError(
                    'default_factory can only take zero or one argument'  # pragma: no mutate
                )

    default_factory = property(fset=__set_default_factory,
                               doc=__set_default_factory.__doc__)


# vim:et sw=4 ts=4
