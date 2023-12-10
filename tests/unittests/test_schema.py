from dataclasses import dataclass
from enum import Enum, auto
from types import SimpleNamespace
from typing import Any, NamedTuple, Optional

from pytest import mark, raises, skip

from envolved import MissingEnvError, as_default, env_var
from envolved.basevar import discard
from envolved.infer_env_var import inferred_env_var


class NamedTupleClass(NamedTuple):
    a: str
    b: int = 5
    c: Any = None


@dataclass
class DataClassClass:
    a: str
    b: int = 5
    c: Any = None


class RecordClassInit:
    def __init__(self, a: str, b: int = 5, c=None):
        self.a = a
        self.b = b
        self.c = c

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c


class RecordClassNew:
    def __new__(cls, a: str, b: int = 5, c=None):
        self = super().__new__(cls)
        self.a = a  # type: ignore[attr-defined]
        self.b = b  # type: ignore[attr-defined]
        self.c = c  # type: ignore[attr-defined]

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c


def a_factory(a: str, b: int = 5, c=None):
    return a, b, c


a = mark.parametrize("A", [NamedTupleClass, DataClassClass, RecordClassInit, RecordClassNew, a_factory])


@a
def test_schema(monkeypatch, A):
    a = env_var("a_", type=A, args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)))

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == A("hi", 36, "blue")
    assert a_pos.get() == a.get()


@a
def test_schema_missing(monkeypatch, A):
    a = env_var("a_", type=A, args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)))

    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")

    with raises(MissingEnvError):
        a.get()

    with raises(MissingEnvError):
        a_pos.get()


@a
def test_type_override(monkeypatch, A):
    a = env_var("a_", type=A, args={"a": env_var("A"), "b": env_var("B", type=float), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, pos_args=(env_var("A"), env_var("B", type=float), env_var("C", type=str)))

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36.5")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == A("hi", 36.5, "blue")
    assert a_pos.get() == a.get()


def test_dict_schema(monkeypatch):
    a = env_var(
        "a_", type=dict, args={"a": env_var("A", type=str), "b": env_var("B", type=int), "c": env_var("C", type=str)}
    )

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == {
        "a": "hi",
        "b": 36,
        "c": "blue",
    }


def test_tup_schema(monkeypatch):
    a = env_var(
        "a_",
        type=lambda *args: tuple(args),
        pos_args=(env_var("A", type=str), env_var("B", type=int), env_var("C", type=str)),
    )

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == (
        "hi",
        36,
        "blue",
    )


@a
def test_schema_reuse(monkeypatch, A):
    d = {"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)}

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")
    monkeypatch.setenv("b_a", "hello")
    monkeypatch.setenv("b_b", "63")
    monkeypatch.setenv("b_c", "red")

    a = env_var("a_", type=A, args=d)

    assert a.get() == A("hi", 36, "blue")

    b = env_var("b_", type=A, args=d)

    assert a.get() == A("hi", 36, "blue")
    assert b.get() == A("hello", 63, "red")


def test_schema_notype(monkeypatch):
    s = env_var(
        "s",
        type=SimpleNamespace,
        args={
            "a": env_var("a", type=int),
            "b": env_var("b", type=str),
        },
    )

    monkeypatch.setenv("sa", "12")
    monkeypatch.setenv("sb", "foo")

    assert vars(s.get()) == {"a": 12, "b": "foo"}


@mark.parametrize("decorator", [staticmethod, lambda x: x])
def test_inner_validator(monkeypatch, decorator):
    x = env_var("x", type=int)

    @x.validator
    @decorator
    def add_one(v):
        return v + 1

    s = env_var("s", type=SimpleNamespace, args={"x": x})

    monkeypatch.setenv("sx", "12")
    assert s.get().x == 13


@a
def test_partial_schema(monkeypatch, A):
    a = env_var("a_", type=A, default=None, args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, default=None, pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)))

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")

    with raises(MissingEnvError):
        a.get()

    with raises(MissingEnvError):
        a_pos.get()


@a
def test_partial_schema_ok(monkeypatch, A):
    a = env_var(
        "a_",
        type=A,
        default=None,
        args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)},
        on_partial=as_default,
    )

    a_pos = env_var(
        "a_",
        type=A,
        default=None,
        pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)),
        on_partial=as_default,
    )

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")

    assert a.get() is None
    assert a_pos.get() is None


@a
def test_schema_all_missing(monkeypatch, A):
    a = env_var("a_", type=A, default=None, args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, default=None, pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)))

    assert a.get() is None
    assert a_pos.get() is None


@a
def test_partial_schema_with_default(monkeypatch, A):
    a = env_var(
        "a_", type=A, default=None, args={"a": env_var("A"), "b": env_var("B", default=5), "c": env_var("C", type=str)}
    )
    a_pos = env_var(
        "a_", type=A, default=None, pos_args=(env_var("A"), env_var("B", default=5), env_var("C", type=str))
    )

    monkeypatch.setenv("a_a", "hi")

    with raises(MissingEnvError):
        a.get()

    with raises(MissingEnvError):
        a_pos.get()


@a
def test_partial_schema_ok_with_default(monkeypatch, A):
    a = env_var(
        "a_",
        type=A,
        default=object(),
        args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)},
        on_partial=None,
    )
    a_pos = env_var(
        "a_",
        type=A,
        default=object(),
        pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)),
        on_partial=None,
    )

    monkeypatch.setenv("a_a", "hi")

    assert a.get() is None
    assert a_pos.get() is None


@a
def test_schema_all_missing_with_default(monkeypatch, A):
    a = env_var(
        "a_", type=A, default=None, args={"a": env_var("A"), "b": env_var("B", default=5), "c": env_var("C", type=str)}
    )
    a_pos = env_var(
        "a_", type=A, default=None, pos_args=(env_var("A"), env_var("B", default=5), env_var("C", type=str))
    )

    assert a.get() is None
    assert a_pos.get() is None


@a
def test_schema_all_missing_no_default(monkeypatch, A):
    a = env_var("a_", type=A, args={"a": env_var("A"), "b": env_var("B"), "c": env_var("C", type=str)})
    a_pos = env_var("a_", type=A, pos_args=(env_var("A"), env_var("B"), env_var("C", type=str)))

    with raises(MissingEnvError):
        a.get()

    with raises(MissingEnvError):
        a_pos.get()


@a
def test_autotype_validator(monkeypatch, A):
    b_var = env_var("b")

    @b_var.validator
    def f(v):
        return (v // 10) * 10

    a = env_var("a_", type=A, args={"a": env_var("A"), "b": b_var, "c": env_var("C", type=str)})

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_b", "36")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == A("hi", 30, "blue")


def test_autotype_anonymous_namedtuple(monkeypatch):
    a = env_var("ORIGIN_", type=NamedTuple("A", [("x", int), ("y", int)]), args={"x": env_var("X"), "y": env_var("Y")})

    monkeypatch.setenv("ORIGIN_x", "12")
    monkeypatch.setenv("ORIGIN_y", "36")

    assert a.get() == (12, 36)


def test_simpletype(monkeypatch):
    a = env_var("ORIGIN_", type=SimpleNamespace, args={"x": env_var("X", type=int), "y": env_var("Y", type=int)})

    monkeypatch.setenv("ORIGIN_x", "12")
    monkeypatch.setenv("ORIGIN_y", "36")

    assert a.get() == SimpleNamespace(x=12, y=36)


def test_dict(monkeypatch):
    a = env_var("ORIGIN_", type=dict, args={"x": env_var("X", type=int), "y": env_var("Y", type=int)})

    monkeypatch.setenv("ORIGIN_x", "12")
    monkeypatch.setenv("ORIGIN_y", "36")

    assert a.get() == {"x": 12, "y": 36}


def test_typed_dict(monkeypatch):
    try:
        from typing import TypedDict
    except ImportError:
        skip("typing.TypedDict not available in earlier versions")

    class Point(TypedDict):
        x: int
        y: int

    a = env_var("ORIGIN_", type=Point, args={"x": env_var("X"), "y": env_var("Y")})

    monkeypatch.setenv("ORIGIN_x", "12")
    monkeypatch.setenv("ORIGIN_y", "36")

    assert a.get() == {"x": 12, "y": 36}


def test_schema_discard(monkeypatch):
    a = env_var(
        "a_",
        type=SimpleNamespace,
        args={"a": env_var("A", type=str), "b": env_var("B", type=bool, default=discard), "c": env_var("C", type=str)},
    )
    a_pos = env_var(
        "a_",
        type=lambda *s: tuple(s),
        pos_args=(env_var("A", type=str), env_var("B", type=bool, default=discard), env_var("C", type=str)),
    )

    monkeypatch.setenv("a_a", "hi")
    monkeypatch.setenv("a_c", "blue")

    assert a.get() == SimpleNamespace(a="hi", c="blue")
    assert a_pos.get() == ("hi",)


@a
def test_infer_everything(A, monkeypatch):
    a = env_var("a_", type=A, args={"a": inferred_env_var(), "b": inferred_env_var(), "c": inferred_env_var(type=str)})
    a_pos = env_var(
        "a_", type=A, pos_args=(inferred_env_var("a"), inferred_env_var("b"), inferred_env_var("c", type=str))
    )

    monkeypatch.setenv("a_a", "hi")

    assert a.get() == A("hi", 5, None)
    assert a_pos.get() == a.get()


def test_exotic_type_hints(monkeypatch):
    class Color(Enum):
        RED = auto()
        BLUE = auto()
        GREEN = auto()

    @dataclass
    class A:
        x: Optional[str]
        c: Color

    a = env_var("a_", type=A, args={"x": inferred_env_var(), "c": inferred_env_var()})

    monkeypatch.setenv("a_x", "hi")
    monkeypatch.setenv("a_c", "red")

    assert a.get() == A("hi", Color.RED)


def test_get_runtime(monkeypatch):
    s = env_var(
        "s",
        type=dict,
        args={
            "a": env_var("a", type=int),
            "b": env_var("b", type=str),
        },
    )

    monkeypatch.setenv("sa", "12")
    monkeypatch.setenv("sb", "foo")

    assert s.get(c="bla", d=12) == {"a": 12, "b": "foo", "c": "bla", "d": 12}


def test_patch_beats_runtime():
    s = env_var(
        "s",
        type=dict,
        args={
            "a": env_var("a", type=int),
            "b": env_var("b", type=str),
        },
    )

    with s.patch({"foo": "bar"}):
        assert s.get(c="bla", d=12) == {"foo": "bar"}


def test_validate_runtime(monkeypatch):
    s = env_var(
        "s",
        type=dict,
        args={
            "a": env_var("a", type=int),
            "b": env_var("b", type=str),
        },
    )

    @s.validator
    def validate(d):
        d["d"] *= 2
        return d

    monkeypatch.setenv("sa", "12")
    monkeypatch.setenv("sb", "foo")

    assert s.get(c="bla", d=12) == {"a": 12, "b": "foo", "c": "bla", "d": 24}
