import re
from typing import List, Dict, Union, Mapping, Any, Optional

from pytest import raises, mark

from envolved.parsers import complex_parser, BoolParser, CollectionParser, JsonParser


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


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_delimited(trailing, trailing_req):
    p = CollectionParser(re.compile(r'(?<!\\);'), str, trailing_delimiter=trailing_req)
    assert p(r"1;3\;4;3" + ';' * trailing) == ['1', r'3\;4', '3']


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_delimited_str(trailing, trailing_req):
    p = CollectionParser('.', int, trailing_delimiter=trailing_req)
    assert p("1.3.4.3" + '.' * trailing) == [1, 3, 4, 3]


def test_delimited_required():
    p = CollectionParser(';', int, trailing_delimiter=True)
    with raises(ValueError):
        p("1;3;4;3")


def test_delimited_none():
    p = CollectionParser(';', str, trailing_delimiter=False)
    assert p('a;b;c;') == ['a', 'b', 'c', '']


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_mapping(trailing, trailing_req):
    p = CollectionParser.pair_wise_delimited(';', '=', str, int, trailing_delimiter=trailing_req)
    assert p("a=1;b=2;c=3" + ';' * trailing) == {'a': 1, 'b': 2, 'c': 3}


def test_repeating():
    p = CollectionParser.pair_wise_delimited(';', '=', str, int)
    with raises(ValueError):
        p('a=1;b=2;a=1')


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_delimited_brackets(trailing, trailing_req):
    p = CollectionParser(';', int, trailing_delimiter=trailing_req, opener='[', closer=']')
    assert p("[1;3;4;3" + ';' * trailing + ']') == [1, 3, 4, 3]


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_mapping_different_val_types(trailing, trailing_req):
    val_dict = {
        'a': str,
        'b': bool,
        'c': int
    }
    p = CollectionParser.pair_wise_delimited(';', '=', str, val_dict, trailing_delimiter=trailing_req)
    assert p("a=hello world;b=true;c=3" + ';' * trailing) == {'a': 'hello world', 'b': True, 'c': 3}


@mark.parametrize('trailing, trailing_req', [(False, None), (True, None), (False, False), (True, True)])
def test_mapping_vfirst(trailing, trailing_req):
    p = CollectionParser.pair_wise_delimited(';', '=', int, str, key_first=False, trailing_delimiter=trailing_req)
    assert p("a=1;b=2;c=3" + ';' * trailing) == {1: 'a', 2: 'b', 3: 'c'}


def test_json_primitive():
    p = JsonParser(float)
    assert p('3') == 3
    assert p('3.5') == 3.5


def test_json_exact():
    p = JsonParser(bool)
    assert p('true') is True
    assert p('false') is False
    with raises(ValueError):
        p('1')


@mark.parametrize('list_', [list, List])
def test_json_list(list_):
    p = JsonParser(list_)
    assert p('["a", 5, [true]]') == ["a", 5, [True]]


def test_json_alias():
    p = JsonParser(List[int])
    assert p('[1,2,3]') == [1, 2, 3]
    with raises(ValueError):
        p('["a"]')
    with raises(ValueError):
        p('{"a":1}')


def test_json_tuple():
    p = JsonParser((int, bool))
    assert p('true') is True
    assert p('15') == 15
    with raises(ValueError):
        p('3.6')


def test_json_union():
    p = JsonParser(Union[int, bool])
    assert p('true') is True
    assert p('15') == 15
    with raises(ValueError):
        p('3.6')


def test_json_optional():
    p = JsonParser(Optional[int])
    assert p('null') is None
    assert p('15') == 15
    with raises(ValueError):
        p('3.6')


def test_json_alias_dict():
    p = JsonParser(Dict[str, int])
    assert p('{"one":1, "two":2}') == {'one': 1, 'two': 2}


def test_json_alias_nested_dict():
    p = JsonParser(Dict[str, List[float]])
    assert p('{"one":[1], "two":[2,4,8]}') == {'one': [1], 'two': [2, 4, 8]}


@mark.skipif("sys.version_info < (3,8)")
def test_typed_dict():
    from typing import TypedDict

    class A(TypedDict):
        a: str
        b: List[float]

    p = JsonParser(A)

    assert p('{"a": "a", "b": [3,5,1]}') == {"a": "a", "b": [3, 5, 1]}

    with raises(ValueError):
        assert p('{"a": "a", "b": [3,5,1], "c": 3}')

    with raises(ValueError):
        assert p('{"a": "a"}')


@mark.skipif("sys.version_info < (3,8)")
def test_typed_dict_nontotal():
    from typing import TypedDict

    class A(TypedDict, total=False):
        a: str
        b: List[float]

    p = JsonParser(A)

    assert p('{"a": "a", "b": [3,5,1]}') == {"a": "a", "b": [3, 5, 1]}

    assert p('{"a": "a"}') == {"a": "a"}


@mark.skipif("sys.version_info < (3,8)")
def test_typed_dict_for():
    from typing import TypedDict

    class A(TypedDict):
        a: "str"
        b: "List[float]"

    p = JsonParser(A)

    assert p('{"a": "a", "b": [3,5,1]}') == {"a": "a", "b": [3, 5, 1]}

    with raises(ValueError):
        assert p('{"a": "a", "b": [3,5,1], "c": 3}')

    with raises(ValueError):
        assert p('{"a": "a"}')


def test_dict_factory():
    def foo(a: int, b: Mapping[str, Any], c: float = 3, **kwargs: float):
        pass

    p = JsonParser(foo)
    assert p('{"a": 12, "b":{"k":6, "t":[]}, "k":9, "f": 3.2}') == {
        "a": 12,
        "b": {"k": 6, "t": []},
        "k": 9,
        "f": 3.2
    }
