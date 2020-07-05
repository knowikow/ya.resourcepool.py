import pytest

from ya.dotdict import DotDict  # , DotDictMixin


def test_items():
    "setitem and getitem work like with dict"
    instance = DotDict()
    instance['spam'] = 'eggs'

    assert instance['spam'] == 'eggs'


def test_attrs():
    "getattr and setattr are symmetric"
    instance = DotDict()
    instance.spam = 'eggs'

    assert instance.spam == 'eggs'


def test_setattr():
    "setattr does the same thing as setitem"
    instance = DotDict()
    instance.spam = 'eggs'

    assert instance['spam'] == 'eggs'


def test_getattr():
    "getattr does the same thing as getitem"
    instance = DotDict()
    instance['spam'] = 'eggs'

    assert instance.spam == 'eggs'


def test_key_error():
    "Trying to get a non-existing key will raise an AttributeError"
    instance = DotDict()
    with pytest.raises(AttributeError):
        instance.spam


def test_init_kwargs():
    "Initial items can be given as keyword arguments"
    instance = DotDict(spam='eggs')
    assert instance['spam'] == 'eggs'
    assert instance.spam == 'eggs'


def test_default_factory():
    "By giving a default factory we get defaultdict behaviour"
    instance = DotDict(default_factory=lambda: 'foobar')

    assert instance.spam == 'foobar'
    assert instance['eggs'] == 'foobar'


def test_default_factory_inserts_value():
    "By giving a default factory we get defaultdict behaviour"
    instance = DotDict(default_factory=lambda: 'foobar')

    assert 'spam' not in instance
    assert instance.spam == 'foobar'
    assert 'spam' in instance
    assert instance['spam'] == 'foobar'


def test_set_default_factory():
    "By giving a default factory we get defaultdict behaviour"
    instance = DotDict()

    with pytest.raises(AttributeError):
        instance.spam

    instance.default_factory = lambda: 'foobar'

    assert instance.spam == 'foobar'
    assert instance['eggs'] == 'foobar'


def test_default_factory_with_arg():
    "Default factories can take the key as argument"
    instance = DotDict(default_factory=lambda x: f'value of {x}')

    assert instance.spam == 'value of spam'
    assert instance['eggs'] == 'value of eggs'


def test_invalid_default_factory():
    "Default factory must either take zero or one argument"
    with pytest.raises(TypeError):
        DotDict(default_factory=lambda x, y: None)


# vim:et sw=4 ts=4
