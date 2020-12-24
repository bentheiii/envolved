import sys
from typing import NamedTuple, Any

from attr import dataclass
from pytest import raises, mark

from envolved import Schema, EnvVar


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
def test_schema(set_env, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_type_conflict(set_env, A):
    with raises(RuntimeError):
        class A_Schema(Schema, type=A):
            a = EnvVar('A')
            b = EnvVar('B')
            c: str = EnvVar('C', type=int)


@a
def test_type_override(set_env, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b: float = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36.5')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36.5, 'blue')


@a
def test_schema_anonymous(set_env, A):
    class A_Schema(Schema, type=A):
        a = EnvVar()
        b = EnvVar()
        c: str = EnvVar()

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@mark.skipif(sys.platform == "win32", reason="windows is always case-insensitive")
@a
def test_scheme_case_sensitive(set_env, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b: float = EnvVar('B')
        c: str = EnvVar('C')

    a = EnvVar('a_', type=A_Schema, case_sensitive=True)

    set_env('a_A', 'hi')
    set_env('a_a', 't')
    set_env('a_B', '36')
    set_env('a_C', 'blue')

    assert a.get() == A('hi', 36, 'blue')


def test_mapvar(set_env):
    a = EnvVar('a_', type={
        'a': EnvVar('A', type=str),
        'b': EnvVar('B', type=float),
        'c': EnvVar('C', type=str)
    })

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == {
        'a': 'hi',
        'b': 36,
        'c': 'blue',
    }


@a
def test_schema_inplace(set_env, A):
    A_Schema = Schema(A,
                      a=EnvVar(),
                      b=EnvVar(),
                      c=EnvVar(type=str))

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_inplace(set_env, A):
    A_Schema = Schema(A, {'a': EnvVar()},
                      b=EnvVar(),
                      c=EnvVar(type=str))

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')


@a
def test_schema_forward_ref(set_env, A):
    class A_Schema(Schema, type=A):
        a = EnvVar('A')
        b = EnvVar('B')
        c: 'str' = EnvVar('C')

    a = EnvVar('a_', type=A_Schema)

    set_env('a_a', 'hi')
    set_env('a_b', '36')
    set_env('a_c', 'blue')

    assert a.get() == A('hi', 36, 'blue')
