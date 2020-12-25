import sys
from unittest.mock import MagicMock

from pytest import raises, mark

from envolved import EnvVar, MissingEnvError


def test_get_int(set_env):
    set_env('t', '15')
    t = EnvVar('t', type=int)

    assert t.get() == 15


def test_get_bool(set_env):
    set_env('t', 'true')
    t = EnvVar('t', type=bool)

    assert t.get() is True


def test_is_cached(set_env):
    set_env('t', 'hi')
    parser = MagicMock(return_value=15)
    t = EnvVar('T', type=parser)

    assert t.get() == 15
    assert t.get() == 15

    parser.assert_called_once_with('hi')


def test_default(del_env):
    del_env('t')
    t = EnvVar('t', type=str, default=...)
    assert t.get() is ...


def test_missing(del_env):
    del_env('t')
    t = EnvVar('t', type=str)
    with raises(MissingEnvError):
        t.get()


def test_validators(set_env):
    set_env('t', '16')
    t = EnvVar('T', type=int)

    @t.validator
    def round_to_odd(x):
        return (x // 2) * 2 + 1

    assert t.get() == 17


def test_validators_default(del_env):
    del_env('t')
    t = EnvVar('T', type=int, default=None)

    @t.validator
    def round_to_odd(x):
        raise RuntimeError

    assert t.get() is None


def test_ensurer(set_env):
    set_env('t', 'howdy')
    t = EnvVar('T', type=str)

    @t.ensurer
    def _(x):
        if x.startswith('f'):
            raise ValueError

    assert t.get()


def test_ensurer_fails(set_env):
    set_env('t', 'friend')
    t = EnvVar('T', type=str)

    @t.ensurer
    def _(x):
        if x.startswith('f'):
            raise ValueError

    with raises(ValueError):
        t.get()


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_insensitive_ambiguity(set_env):
    set_env('ab', 'T')
    set_env('AB', 'T')

    t = EnvVar('Ab', type=str)
    t0 = EnvVar('AB', type=str, case_sensitive=True)

    with raises(RuntimeError):
        t.get()

    assert t0.get() == 'T'


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_ambiguity_solved_with_exactness(set_env):
    set_env('ab', 'T0')
    set_env('AB', 'T1')

    t = EnvVar('AB', type=str)

    assert t.get() == 'T1'


def test_case_invalid(set_env):
    a = EnvVar(type=int)
    with raises(RuntimeError):
        a.get()

    b = EnvVar('b')
    with raises(RuntimeError):
        b.get()

    c: int = EnvVar('c')
    with raises(RuntimeError):
        c.get()
