import sys
from typing import NamedTuple, Any

from attr import dataclass
from pytest import raises, mark

from envolved import Schema, EnvVar, MissingEnvError


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
        self.a = a
        self.b = b
        self.c = c

    def __eq__(self, other):
        return self.a == other.a and self.b == other.b and self.c == other.c


def a_factory(a: str, b: int, c):
    return a, b, c


a = mark.parametrize('A', [A_NT, A_DC, A_RCI, A_RCN, a_factory])


@a
def test_schema(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_missing(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    with raises(MissingEnvError):
        a.get()


@a
def test_type_conflict(monkeypatch, A):
    with raises(RuntimeError):
        class A_Schema(Schema, type=A):
            a = EnvVar('A')
            b = EnvVar('B')
            c: str = EnvVar('C', type=int)


@a
def test_type_override(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b: float = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36.5')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36.5, 'blue')


@a
def test_schema_anonymous(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar()
        b = EnvVar()
        c: str = EnvVar()

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
@a
def test_scheme_case_sensitive(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b: float = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema, case_sensitive=True)

    monkeypatch.setenv('a_A', 'hi')
    monkeypatch.setenv('a_a', 't')
    monkeypatch.setenv('a_B', '36')
    monkeypatch.setenv('a_C', 'blue')

    assert a.get() == A('hi', 36, 'blue')


def test_dict_schema(monkeypatch):
    a = EnvVar('a_', type=Schema(
        dict,
        a=EnvVar('A', type=str),
        b=EnvVar('B', type=float),
        c=EnvVar('C', type=str)
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
def test_schema_inplace(monkeypatch, A):
    A_Schema = Schema(A,
                      a=EnvVar(),
                      b=EnvVar(),
                      c=EnvVar(type=str))

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_inplace_mapping(monkeypatch, A):
    A_Schema = Schema(A, {'a': EnvVar()},
                      b=EnvVar(),
                      c=EnvVar(type=str))

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_forward_ref(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: 'str' = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_reuse(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')
    monkeypatch.setenv('a_c', 'blue')
    monkeypatch.setenv('b_a', 'hello')
    monkeypatch.setenv('b_b', '63')
    monkeypatch.setenv('b_c', 'red')

    a = EnvVar('a_', type=A_Schema)

    assert a.get() == A('hi', 36, 'blue')

    b = EnvVar('b_', type=A_Schema)

    assert a.get() == A('hi', 36, 'blue')
    assert b.get() == A('hello', 63, 'red')


@a
def test_schema_reuse_inner(monkeypatch, A):
    with raises(RuntimeError):
        class A_Schema(Schema, type=A):
            a = b = EnvVar()
            c: str = EnvVar()


def test_schema_variadic(monkeypatch):
    def foo(a: int, b: str, **kwargs: float):
        return a, b, kwargs

    class F_Schema(Schema, type=foo):
        a = EnvVar()
        b = EnvVar()
        g = EnvVar()

    f = EnvVar('f_', type=F_Schema)
    monkeypatch.setenv('f_a', '36')
    monkeypatch.setenv('f_b', 'hi')
    monkeypatch.setenv('f_g', '15.6')
    assert f.get() == (36, 'hi', {'g': 15.6})


def test_schema_variadic_resolution():
    class A:
        def __init__(self, **k: int):
            pass

        def __new__(cls, **k: str):
            pass

    class A_Schema(Schema, type=A):
        b = EnvVar()

    assert A_Schema['b'].type == int


def test_schema_notype(monkeypatch):
    class S(Schema):
        a: int = EnvVar()
        b: str = EnvVar()

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sa', '12')
    monkeypatch.setenv('sb', 'foo')

    assert vars(s.get()) == {'a': 12, 'b': 'foo'}


def test_schema_notype_inline(monkeypatch):
    s = EnvVar('s', type=Schema(
        a=EnvVar(type=int),
        b=EnvVar(type=str),
    ))

    monkeypatch.setenv('sa', '12')
    monkeypatch.setenv('sb', 'foo')

    assert vars(s.get()) == {'a': 12, 'b': 'foo'}


def test_schema_notype_inline_mapping(monkeypatch):
    s = EnvVar('s', type=Schema(
        {'a': EnvVar(type=int)},
        b=EnvVar(type=str),
    ))

    monkeypatch.setenv('sa', '12')
    monkeypatch.setenv('sb', 'foo')

    assert vars(s.get()) == {'a': 12, 'b': 'foo'}


@mark.parametrize('decorator', [staticmethod, lambda x: x])
def test_inner_validator(monkeypatch, decorator):
    class S(Schema):
        x: int = EnvVar()

        @x.validator
        @decorator
        def add_one(v):
            return v + 1

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 13


def test_inner_validator_outside(monkeypatch):
    class S(Schema):
        x: int = EnvVar()

    @S.x.validator
    def add_one(v):
        return v + 1

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 13


def test_inner_validator_outside_bad(monkeypatch):
    class S(Schema):
        x: int = EnvVar()

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 12

    with raises(RuntimeError):
        @S.x.validator
        def add_one(v):
            return v + 1


def test_inner_validator_outside_inline(monkeypatch):
    S = Schema({
        'x': EnvVar(type=int)
    })

    @S.x.validator
    def add_one(v):
        return v + 1

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 13


def test_inner_validator_outside_bad_inline(monkeypatch):
    S = Schema({
        'x': EnvVar(type=int)
    })

    s = EnvVar('s', type=S)

    monkeypatch.setenv('sx', '12')
    assert s.get().x == 12

    with raises(RuntimeError):
        @S.x.validator
        def add_one(v):
            return v + 1


@a
def test_get_inner_vars(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    monkeypatch.setenv('A', 'hi')
    assert A_Schema.a.get() == 'hi'


@a
def test_partial_schema(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema, default=None)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')

    with raises(MissingEnvError):
        a.get()


@a
def test_partial_schema_ok(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema, default=None, raise_for_partial=False)

    monkeypatch.setenv('a_a', 'hi')
    monkeypatch.setenv('a_b', '36')

    assert a.get() is None


@a
def test_schema_all_missing(monkeypatch, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema, default=None)

    assert a.get() is None
