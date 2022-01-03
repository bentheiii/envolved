import re

from pytest import mark, raises

from envolved.parsers import BoolParser, CollectionParser, complex_parser


def test_complex():
    assert complex_parser('0') == 0
    assert complex_parser('1+1i') == 1 + 1j
    assert complex_parser('3i') == 3j


def test_bool_parser():
    p = BoolParser(('y', 'yes'), ('n', 'no'), case_sensitive=True)

    assert p('y')
    assert not p('no')
    with raises(ValueError):
        p('Yes')


def test_bool_default():
    p = BoolParser(('y', 'yes'), ('n', 'no'), default=False)
    assert not p('Hi')


def test_delimited():
    p = CollectionParser(re.compile(r'(?<!\\);'), str)
    assert p(r"1;3\;4;3") == ['1', r'3\;4', '3']


def test_delimited_str():
    p = CollectionParser('.', int)
    assert p("1.3.4.3") == [1, 3, 4, 3]


def test_mapping():
    p = CollectionParser.pair_wise_delimited(';', '=', str, int)
    assert p("a=1;b=2;c=3") == {'a': 1, 'b': 2, 'c': 3}


def test_repeating():
    p = CollectionParser.pair_wise_delimited(';', '=', str, int)
    with raises(ValueError):
        p('a=1;b=2;a=1')


def test_delimited_brackets():
    p = CollectionParser(';', int, opener='[', closer=']')
    assert p("[1;3;4;3]") == [1, 3, 4, 3]


def test_mapping_different_val_types():
    val_dict = {
        'a': str,
        'b': bool,
        'c': int
    }
    p = CollectionParser.pair_wise_delimited(';', '=', str, val_dict)
    assert p("a=hello world;b=true;c=3") == {'a': 'hello world', 'b': True, 'c': 3}


def test_mapping_vfirst():
    p = CollectionParser.pair_wise_delimited(';', '=', int, str, key_first=False)
    assert p("a=1;b=2;c=3") == {1: 'a', 2: 'b', 3: 'c'}


def test_infix_closer_collections():
    assert CollectionParser(';', str, opener='[', closer=']')('[a;b;c]d]') == ['a', 'b', 'c]d']


@mark.parametrize('bad_str', ['', '[', ']', 'a=1;b=2;c=3', '[a=1;b=2;c=3]d=4'])
def test_invalid_collections(bad_str):
    with raises(ValueError):
        CollectionParser(';', str, opener='[', closer=']')(bad_str)
