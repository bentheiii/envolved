import gc
import re
from _operator import itemgetter
from collections import namedtuple
from math import sqrt
from types import SimpleNamespace

from envolved import EnvVar, Schema, describe_env_vars


def test_pattern(monkeypatch):
    a = EnvVar('', prefix_capture=re.compile('[ab]+'), type=int)

    monkeypatch.setenv('a', '0')
    monkeypatch.setenv('b', '1')
    monkeypatch.setenv('cada', '2')
    monkeypatch.setenv('ba', '3')
    monkeypatch.setenv('ab', '4')

    assert a.get() == {
        'A': 0,
        'B': 1,
        'BA': 3,
        'AB': 4,
    }


def test_in_schema(monkeypatch):
    p = EnvVar('p_', type=Schema(
        name=EnvVar(type=str),
        coords=EnvVar('c', prefix_capture=re.compile('[a-z]'), type=float)
    ))

    monkeypatch.setenv('p_name', 'origin')
    monkeypatch.setenv('p_cx', '1')
    monkeypatch.setenv('p_cy', '2')
    monkeypatch.setenv('p_cz', '3')

    assert p.get() == SimpleNamespace(
        name='origin',
        coords={
            'X': 1,
            'Y': 2,
            'Z': 3
        }
    )


def test_nested_maps(monkeypatch):
    a = EnvVar('a_', prefix_capture=re.compile('[a-z]+'),
               type=EnvVar('_', prefix_capture=re.compile('[a-z]+'), type=float))

    monkeypatch.setenv('a_one_two', '1.2')
    monkeypatch.setenv('a_one_ten', '1.10')
    monkeypatch.setenv('a_three_two', '3.2')

    assert a.get() == {
        'ONE': {
            'TWO': 1.2,
            'TEN': 1.10,
        },
        'THREE': {
            'TWO': 3.2
        }
    }


def test_inner_schema(monkeypatch):
    Point = namedtuple('Point', 'x y')

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=Schema(Point,
                           x=EnvVar(type=int),
                           y=EnvVar(type=int),
                           ))

    monkeypatch.setenv('a_p_x', '15')
    monkeypatch.setenv('a_p_y', '7')
    monkeypatch.setenv('a_q_x', '10')
    monkeypatch.setenv('a_q_y', '0')

    assert a.get() == {
        'P': Point(15, 7),
        'Q': Point(10, 0)
    }


def test_outer_validator(monkeypatch):
    Point = namedtuple('Point', 'x y')

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=Schema(Point,
                           x=EnvVar(type=int),
                           y=EnvVar(type=int),
                           ))

    monkeypatch.setenv('a_p_x', '15')
    monkeypatch.setenv('a_p_y', '7')
    monkeypatch.setenv('a_q_x', '10')
    monkeypatch.setenv('a_q_y', '0')

    @a.validator
    def add(value):
        x = sum(v.x for v in value.values())
        y = sum(v.y for v in value.values())
        return Point(x, y)

    assert a.get() == Point(25, 7)


def test_inner_validator(monkeypatch):
    Point = namedtuple('Point', 'x y')

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=Schema(Point,
                           x=EnvVar(type=int),
                           y=EnvVar(type=int),
                           ))

    monkeypatch.setenv('a_p_x', '16')
    monkeypatch.setenv('a_p_y', '12')
    monkeypatch.setenv('a_q_x', '10')
    monkeypatch.setenv('a_q_y', '0')

    @a.validator(per_element=True)
    def normalize(value):
        radius = sqrt(value.x ** 2 + value.y ** 2)
        return Point(value.x / radius, value.y / radius)

    assert a.get() == {
        'P': Point(0.8, 0.6),
        'Q': Point(1, 0)
    }


def test_inner_validator_preset(monkeypatch):
    Point = namedtuple('Point', 'x y')

    inner = EnvVar(type=Schema(Point,
                               x=EnvVar(type=int),
                               y=EnvVar(type=int),
                               ))

    @inner.validator()
    def normalize(value):
        radius = sqrt(value.x ** 2 + value.y ** 2)
        return Point(value.x / radius, value.y / radius)

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=inner)

    monkeypatch.setenv('a_p_x', '16')
    monkeypatch.setenv('a_p_y', '12')
    monkeypatch.setenv('a_q_x', '10')
    monkeypatch.setenv('a_q_y', '0')

    assert a.get() == {
        'P': Point(0.8, 0.6),
        'Q': Point(1, 0)
    }


def test_inner_validator_postset(monkeypatch):
    Point = namedtuple('Point', 'x y')

    inner = EnvVar(type=Schema(Point,
                               x=EnvVar(type=int),
                               y=EnvVar(type=int),
                               ))

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=inner)

    @inner.validator()
    def normalize(value):
        radius = sqrt(value.x ** 2 + value.y ** 2)
        return Point(value.x / radius, value.y / radius)

    monkeypatch.setenv('a_p_x', '16')
    monkeypatch.setenv('a_p_y', '12')
    monkeypatch.setenv('a_q_x', '10')
    monkeypatch.setenv('a_q_y', '0')

    assert a.get() == {
        'P': Point(0.8, 0.6),
        'Q': Point(1, 0)
    }


def test_describe(monkeypatch):
    Point = namedtuple('Point', 'x y')

    a = EnvVar('a_', prefix_capture=re.compile('([a-z])_'), match_key_callback=1,
               type=Schema(Point,
                           x=EnvVar(type=int, description='bloo'),
                           y=EnvVar(type=int),
                           ), description='bla')

    assert describe_env_vars(initial_indent='', subsequent_indent='\t') == [
        'a: bla',
        '\tA_([A-Z]):',
        '\t\tA_([A-Z])_X: bloo',
        '\t\tA_([A-Z])_Y'
    ]
