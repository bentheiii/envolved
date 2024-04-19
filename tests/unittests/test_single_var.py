import sys
from unittest.mock import MagicMock, call

from pytest import mark, raises

from envolved import EnvVar, Factory, MissingEnvError, env_var


def test_get_int(monkeypatch):
    monkeypatch.setenv("t", "15")
    t = env_var("t", type=int)

    assert t.get() == 15


def test_get_bool(monkeypatch):
    monkeypatch.setenv("t", "true")
    t = env_var("t", type=bool)

    assert t.get() is True


def test_is_not_cached(monkeypatch):
    monkeypatch.setenv("t", "hi")
    parser = MagicMock(return_value=15)
    t = env_var("T", type=parser)

    assert t.get() == 15
    assert t.get() == 15
    monkeypatch.setenv("t", "ho")
    assert t.get() == 15

    parser.assert_has_calls(
        [
            call("hi"),
            call("hi"),
            call("ho"),
        ]
    )


def test_default(monkeypatch):
    monkeypatch.delenv("t", raising=False)
    t = env_var("t", type=str, default=...)
    assert t.get() is ...


def test_default_factory(monkeypatch):
    monkeypatch.delenv("t", raising=False)
    t = env_var("t", type=str, default=Factory(list))
    t0 = t.get()
    t1 = t.get()
    assert t0 == t1 == []
    assert t0 is not t1


def test_missing(monkeypatch):
    monkeypatch.delenv("t", raising=False)
    t = env_var("t", type=str)
    with raises(MissingEnvError):
        t.get()


def test_validators(monkeypatch):
    monkeypatch.setenv("t", "16")
    t = env_var("T", type=int)

    @t.validator
    def round_to_odd(x):
        return (x // 2) * 2 + 1

    assert t.get() == 17


def test_validators_default(monkeypatch):
    monkeypatch.delenv("t", raising=False)
    t = env_var("T", type=int, default=None)

    @t.validator
    def round_to_odd(x):
        raise RuntimeError

    assert t.get() is None


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_sensitive_missing(monkeypatch):
    monkeypatch.setenv("ab", "T")

    t0 = env_var("AB", type=str, case_sensitive=True)

    with raises(MissingEnvError):
        t0.get()


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_insensitive_ambiguity(monkeypatch):
    monkeypatch.setenv("ab", "T")
    monkeypatch.setenv("AB", "T")

    t = env_var("Ab", type=str)
    t0 = env_var("AB", type=str, case_sensitive=True)

    with raises(RuntimeError):
        t.get()

    assert t0.get() == "T"


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_insensitive_ambiguity_but_reload(monkeypatch):
    monkeypatch.setenv("ab", "T")
    monkeypatch.setenv("AB", "T")

    t = env_var("Ab", type=str)

    with raises(RuntimeError):
        t.get()

    monkeypatch.setenv("Ab", "T1")

    assert t.get() == "T1"


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
def test_case_ambiguity_solved_with_exactness(monkeypatch):
    monkeypatch.setenv("ab", "T0")
    monkeypatch.setenv("AB", "T1")

    t = env_var("AB", type=str)

    assert t.get() == "T1"


def test_templating(monkeypatch):
    parent = env_var("a", type=int)

    a0 = parent.with_prefix("0")
    a1 = parent.with_prefix("1")
    monkeypatch.setenv("0a", "0")
    monkeypatch.setenv("1a", "1")
    monkeypatch.setenv("a", "-1")
    assert a0.get() == 0
    assert a1.get() == 1
    a_nil = parent.with_prefix("")
    assert parent.get() == -1
    assert a_nil.get() == -1


def test_override_default(monkeypatch):
    parent = env_var("a", type=int)

    a0 = parent.with_prefix("0")
    a1 = parent.with_prefix("1")
    a1.default = 1
    monkeypatch.setenv("0a", "0")
    assert a0.get() == 0
    assert a1.get() == 1


def test_override_default_in_constr(monkeypatch):
    parent = env_var("a", type=int)

    a0 = parent.with_prefix("0")
    a1 = parent.with_prefix("1", default=1)
    monkeypatch.setenv("0a", "0")
    assert a0.get() == 0
    assert a1.get() == 1


def test_override_type(monkeypatch):
    parent = env_var("a", type=int)

    a1 = parent.with_prefix("1", default=1, type=len)
    assert a1.default == 1
    assert a1.type == len


def test_patch():
    a = env_var("a", type=int)
    with a.patch(-1):
        assert a.get() == -1


def test_nested_patch():
    a = env_var("a", type=int)
    with a.patch(-1):
        assert a.get() == -1
        with a.patch(0):
            assert a.get() == 0
        assert a.get() == -1


def test_no_strip(monkeypatch):
    a: EnvVar[int] = env_var("a", type=len, strip_whitespaces=False)
    monkeypatch.setenv("a", "  \thi  ")
    assert a.get() == 7


def test_get_with_args(monkeypatch):
    a = env_var("a", type=lambda x, mul: x * mul)
    monkeypatch.setenv("a", "na")
    assert a.get(mul=5) == "nanananana"
    with raises(TypeError):
        a.get()


def test_get_with_args_optional(monkeypatch):
    a = env_var("a", type=lambda x, mul=1: x * mul)
    monkeypatch.setenv("a", "na")
    assert a.get(mul=5) == "nanananana"
    assert a.get() == "na"
