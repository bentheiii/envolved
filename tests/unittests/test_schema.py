from types import SimpleNamespace
from typing import Any, NamedTuple

from attr import dataclass
from pytest import mark, raises, skip

from envolved import MissingEnvError, as_default, env_var


class A_NT(NamedTuple):
    a: str
    b: int
    c: Any


@dataclass
class A_DC:
    a: str
    b: int
    c: Any


class A_RCI:
    def __init__(self, a: str, b: int, c):
        self.a = a
        self.b = b
        self.c = c

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c


class A_RCN:
    def __new__(cls, a: str, b: int, c):
        self = super().__new__(cls)
        self.a = a  # type: ignore[attr-defined]
        self.b = b  # type: ignore[attr-defined]
        self.c = c  # type: ignore[attr-defined]

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c


def a_factory(a: str, b: int, c):
    return a, b, c


a = mark.parametrize('A', [A_NT, A_DC, A_RCI, A_RCN, a_factory])


@a
def test_schema(monkeypatch, A):
    a = env_var('a_', type=A, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_missing(monkeypatch, A):
    a = env_var('a_', type=A, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    with raises(MissingEnvError):
        a.get()


@a
def test_type_override(monkeypatch, A):
    a = env_var('a_', type=A, args=dict(
        a=env_var('A'),
        b=env_var('B', type=float),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36.5')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36.5, 'blue')


def test_dict_schema(monkeypatch):
    a = env_var('a_', type=dict, args=dict(
        a=env_var('A', type=str),
        b=env_var('B', type=int),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == {
        'a': 'hi',
        'b': 36,
        'c': 'blue',
    }


@a
def test_schema_reuse(monkeypatch, A):
    d = dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    )

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')
    monkeypatch.setenv('b_a', 'hello')
    monkeypatch.setenv('b_b', '63')
    monkeypatch.setenv('b_c', 'red')

    a = env_var('a_', type=A, args=d)

    assert a.get() == A('hi', 36, 'blue')

    b = env_var('b_', type=A, args=d)

    assert a.get() == A('hi', 36, 'blue')
    assert b.get() == A('hello', 63, 'red')


def test_schema_notype(monkeypatch):
    s = env_var('s', type=SimpleNamespace, args=dict(
        a=env_var('a', type=int),
        b=env_var('b', type=str),
    ))

    monkeypatch.setenv('sa', '12')
    monkeypatch.setenv('sb', 'foo')

    assert vars(s.get()) == {'a': 12, 'b': 'foo'}


@mark.parametrize('decorator', [staticmethod, lambda x: x])
def test_inner_validator(monkeypatch, decorator):
    x = env_var('x', type=int)

    @x.validator
    @decorator
    def add_one(v):
        return v + 1

    s = env_var('s', type=SimpleNamespace, args=dict(
        x=x
    ))

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 13


@a
def test_partial_schema(monkeypatch, A):
    a = env_var('a_', type=A, default=None, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')

    with raises(MissingEnvError):
        a.get()


@a
def test_partial_schema_ok(monkeypatch, A):
    a = env_var('a_', type=A, default=None, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ), on_partial=as_default)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')

    assert a.get() is None


@a
def test_schema_all_missing(monkeypatch, A):
    a = env_var('a_', type=A, default=None, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ))

    assert a.get() is None


@a
def test_partial_schema_with_default(monkeypatch, A):
    a = env_var('a_', type=A, default=None, args=dict(
        a=env_var('A'),
        b=env_var('B', default=5),
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')

    with raises(MissingEnvError):
        a.get()


@a
def test_partial_schema_ok_with_default(monkeypatch, A):
    a = env_var('a_', type=A, default=object(), args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ), on_partial=None)

    monkeypatch.setenv('a_a', 'hi')

    assert a.get() is None


@a
def test_schema_all_missing_with_default(monkeypatch, A):
    a = env_var('a_', type=A, default=None, args=dict(
        a=env_var('A'),
        b=env_var('B', default=5),
        c=env_var('C', type=str)
    ))

    assert a.get() is None


@a
def test_schema_all_missing_no_default(monkeypatch, A):
    a = env_var('a_', type=A, args=dict(
        a=env_var('A'),
        b=env_var('B'),
        c=env_var('C', type=str)
    ))

    with raises(MissingEnvError):
        a.get()


@a
def test_autotype_validator(monkeypatch, A):
    b_var = env_var('b')

    @b_var.validator
    def f(v):
        return (v // 10) * 10

    a = env_var('a_', type=A, args=dict(
        a=env_var('A'),
        b=b_var,
        c=env_var('C', type=str)
    ))

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 30, 'blue')


def test_autotype_anonymous_namedtuple(monkeypatch):
    a = env_var('ORIGIN', type=NamedTuple('A', [('x', int), ('y', int)]), args=dict(
        x=env_var('_X'),
        y=env_var('_Y')
    ))

    monkeypatch.setenv('ORIGIN_x', '12')
    monkeypatch.setenv('ORIGIN_y', '36')

    assert a.get() == (12, 36)


def test_simpletype(monkeypatch):
    a = env_var('ORIGIN', type=SimpleNamespace, args=dict(
        x=env_var('_X', type=int),
        y=env_var('_Y', type=int)
    ))

    monkeypatch.setenv('ORIGIN_x', '12')
    monkeypatch.setenv('ORIGIN_y', '36')

    assert a.get() == SimpleNamespace(x=12, y=36)


def test_dict(monkeypatch):
    a = env_var('ORIGIN', type=dict, args=dict(
        x=env_var('_X', type=int),
        y=env_var('_Y', type=int)
    ))

    monkeypatch.setenv('ORIGIN_x', '12')
    monkeypatch.setenv('ORIGIN_y', '36')

    assert a.get() == dict(x=12, y=36)


def test_typed_dict(monkeypatch):
    try:
        from typing import TypedDict
    except ImportError:
        skip('typing.TypedDict not available in earlier versions')

    class Point(TypedDict):
        x: int
        y: int

    a = env_var('ORIGIN', type=Point, args=dict(
        x=env_var('_X'),
        y=env_var('_Y')
    ))

    monkeypatch.setenv('ORIGIN_x', '12')
    monkeypatch.setenv('ORIGIN_y', '36')

    assert a.get() == dict(x=12, y=36)
