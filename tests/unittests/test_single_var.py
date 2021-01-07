import sys
from unittest.mock import MagicMock

from pytest import raises, mark

from envolved import EnvVar, MissingEnvError


def test_get_int(monkeypatch):
    monkeypatch.setenv('t', '15')
    t = EnvVar('t', type=int)

    assert t.get() == 15


def test_get_bool(monkeypatch):
    monkeypatch.setenv('t', 'true')
    t = EnvVar('t', type=bool)

    assert t.get() is True


def test_is_cached(monkeypatch):
    monkeypatch.setenv('t', 'hi')
    parser = MagicMock(return_value=15)
    t = EnvVar('T', type=parser)

    assert t.get() == 15
    assert t.get() == 15

    parser.assert_called_once_with('hi')


def test_default(monkeypatch):
    monkeypatch.delenv('t', raising=False)
    t = EnvVar('t', type=str, default=...)
    assert t.get() is ...


def test_missing(monkeypatch):
    monkeypatch.delenv('t', raising=False)
    t = EnvVar('t', type=str)
    with raises(MissingEnvError):
        t.get()


def test_validators(monkeypatch):
    monkeypatch.setenv('t', '16')
    t = EnvVar('T', type=int)

    @t.validator
    def round_to_odd(x):
        return (x // 2) * 2 + 1

    assert t.get() == 17


def test_validators_default(monkeypatch):
    monkeypatch.delenv('t', raising=False)
    t = EnvVar('T', type=int, default=None)

    @t.validator
    def round_to_odd(x):
        raise RuntimeError

    assert t.get() is None


def test_ensurer(monkeypatch):
    monkeypatch.setenv('t', 'howdy')
    t = EnvVar('T', type=str)

    @t.ensurer
    def _(x):
        if x.startswith('f'):
            raise ValueError

    assert t.get()


def test_ensurer_fails(monkeypatch):
    monkeypatch.setenv('t', 'friend')
    t = EnvVar('T', type=str)

    @t.ensurer
    def _(x):
        if x.startswith('f'):
            raise ValueError

    with raises(ValueError):
        t.get()


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_insensitive_ambiguity(monkeypatch):
    monkeypatch.setenv('ab', 'T')
    monkeypatch.setenv('AB', 'T')

    t = EnvVar('Ab', type=str)
    t0 = EnvVar('AB', type=str, case_sensitive=True)

    with raises(RuntimeError):
        t.get()

    assert t0.get() == 'T'


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_ambiguity_solved_with_exactness(monkeypatch):
    monkeypatch.setenv('ab', 'T0')
    monkeypatch.setenv('AB', 'T1')

    t = EnvVar('AB', type=str)

    assert t.get() == 'T1'


def test_case_invalid(monkeypatch):
    a = EnvVar(type=int)
    with raises(RuntimeError):
        a.get()

    b = EnvVar('b')
    with raises(RuntimeError):
        b.get()

    c: int = EnvVar('c')
    with raises(RuntimeError):
        c.get()


def test_templating(monkeypatch):
    parent = EnvVar('a', type=int)

    a0 = parent.child('0')
    a1 = parent.child('1')
    monkeypatch.setenv('0a', '0')
    monkeypatch.setenv('1a', '1')
    monkeypatch.setenv('a', '-1')
    assert a0.get() == 0
    assert a1.get() == 1
    a_nil = parent.child('')
    assert parent.get() == -1
    with raises(RuntimeError):
        parent.child('')
    assert a_nil.get() == -1


def test_templating_manifest(monkeypatch):
    parent = EnvVar('a', type=int)
    monkeypatch.setenv('a', '-1')
    assert parent.get() == -1

    with raises(RuntimeError):
        parent.child('0')


def test_override_default(monkeypatch):
    parent = EnvVar('a', type=int)

    a0 = parent.child('0')
    a1 = parent.child('1', default=1)
    monkeypatch.setenv('0a', '0')
    assert a0.get() == 0
    assert a1.get() == 1


def test_parent_no_name(monkeypatch):
    parent = EnvVar(type=int)

    a0 = parent.child('0')
    monkeypatch.setenv('0', '10')
    assert a0.get() == 10
