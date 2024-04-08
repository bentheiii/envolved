import re
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import List

from pydantic import BaseModel as BaseModel2, RootModel, TypeAdapter
from pydantic.v1 import BaseModel as BaseModel1
from pytest import mark, raises

from envolved.parsers import (
    BoolParser,
    CollectionParser,
    FindIterCollectionParser,
    LookupParser,
    MatchParser,
    complex_parser,
    parser,
)


def test_complex():
    assert complex_parser("0") == 0
    assert complex_parser("1+1i") == 1 + 1j
    assert complex_parser("3i") == 3j


def test_bool_parser():
    p = BoolParser(("y", "yes"), ("n", "no"), case_sensitive=True)

    assert p("y")
    assert not p("no")
    with raises(ValueError):
        p("Yes")


def test_bool_default():
    p = BoolParser(("y", "yes"), ("n", "no"), default=False)
    assert not p("Hi")


def test_delimited():
    p = CollectionParser(re.compile(r"(?<!\\);"), str)
    assert p(r"1;3\;4;3") == ["1", r"3\;4", "3"]


def test_delimited_str():
    p = CollectionParser(".", int)
    assert p("1.3.4.3") == [1, 3, 4, 3]


def test_delimited_strip():
    p = CollectionParser(".", int)
    assert p("1.3 .4 .3") == [1, 3, 4, 3]


def test_delimited_no_strip():
    p = CollectionParser(".", len, strip=False)
    assert p("1.3 .4 .3") == [1, 2, 2, 1]


def test_mapping():
    p = CollectionParser.pair_wise_delimited(";", "=", str, int)
    assert p("a = 1; b=2 ;c=3") == {"a": 1, "b": 2, "c": 3}


def test_mapping_nostrip_keys():
    p = CollectionParser.pair_wise_delimited(";", "=", str, int, strip_keys=False)
    assert p("a =1; b=2 ;c= 3") == {"a ": 1, "b": 2, "c": 3}


def test_mapping_nostrip_values():
    p = CollectionParser.pair_wise_delimited(";", "=", str, len, strip_values=False)
    assert p("a =1; b=2 ;c= 3") == {"a": 1, "b": 1, "c": 2}


def test_repeating():
    p = CollectionParser.pair_wise_delimited(";", "=", str, int)
    with raises(ValueError):
        p("a=1;b=2;a=1")


def test_delimited_brackets():
    p = CollectionParser(";", int, opener="[", closer="]")
    assert p("[1;3;4;3]") == [1, 3, 4, 3]


def test_mapping_different_val_types():
    val_dict = {"a": str, "b": bool, "c": int}
    p = CollectionParser.pair_wise_delimited(";", "=", str, val_dict)
    assert p("a=hello world;b=true;c=3") == {"a": "hello world", "b": True, "c": 3}


def test_mapping_different_val_types_with_missing():
    val_dict = defaultdict(lambda: str)
    val_dict.update({"b": bool, "c": int})
    p = CollectionParser.pair_wise_delimited(";", "=", str, val_dict)
    assert p("a=hello world;b=true;c=3") == {"a": "hello world", "b": True, "c": 3}


def test_mapping_vfirst():
    p = CollectionParser.pair_wise_delimited(";", "=", int, str, key_first=False)
    assert p("a=1;b=2;c=3") == {1: "a", 2: "b", 3: "c"}


def test_infix_closer_collections():
    assert CollectionParser(";", str, opener="[", closer="]")("[a;b;c]d]") == ["a", "b", "c]d"]


@mark.parametrize("bad_str", ["", "[", "]", "a=1;b=2;c=3", "[a=1;b=2;c=3]d=4"])
def test_invalid_collections(bad_str):
    with raises(ValueError):
        CollectionParser(";", str, opener="[", closer="]")(bad_str)


def test_match_cases():
    parser = MatchParser(
        (
            (re.compile("[0-9]+"), "num"),
            (re.compile("[a-z]+"), "lower"),
            (re.compile("[A-Z]+"), "upper"),
            ("swordfish19", "password"),
            (re.compile("swordfish19"), "unreachable"),
        )
    )

    assert parser("123") == "num"
    assert parser("abc") == "lower"
    assert parser("ABC") == "upper"
    assert parser("swordfish19") == "password"
    with raises(ValueError):
        parser("swordfish191")


def test_match_dict():
    parser = MatchParser(
        {
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    assert parser("a") == 1
    assert parser("b") == 2
    assert parser("c") == 3

    with raises(ValueError):
        parser("A")


def test_match_enum():
    class MyEnum(Enum):
        RED = 10
        BLUE = 20
        GREEN = 30

    parser = MatchParser(MyEnum)

    assert parser("RED") is MyEnum.RED
    assert parser("BLUE") is MyEnum.BLUE
    assert parser("GREEN") is MyEnum.GREEN


def test_match_enum_caseignore():
    class MyEnum(Enum):
        RED = 10
        BLUE = 20
        GREEN = 30

    parser = MatchParser.case_insensitive(MyEnum)

    assert parser("RED") is MyEnum.RED
    assert parser("blue") is MyEnum.BLUE
    assert parser("green") is MyEnum.GREEN


def test_match_dict_caseignore():
    parser = MatchParser.case_insensitive(
        {
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    assert parser("A") == 1
    assert parser("b") == 2
    assert parser("C") == 3

    with raises(ValueError):
        parser("D")


def test_lookup_dict():
    parser = LookupParser(
        {
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    assert parser("a") == 1
    assert parser("b") == 2
    assert parser("c") == 3

    with raises(ValueError):
        parser("A")


def test_lookup_enum():
    class MyEnum(Enum):
        RED = 10
        BLUE = 20
        GREEN = 30

    parser = LookupParser(MyEnum)

    assert parser("RED") is MyEnum.RED
    assert parser("BLUE") is MyEnum.BLUE
    assert parser("GREEN") is MyEnum.GREEN


def test_lookup_enum_caseignore():
    class MyEnum(Enum):
        RED = 10
        BLUE = 20
        GREEN = 30

    parser = LookupParser.case_insensitive(MyEnum)

    assert parser("RED") is MyEnum.RED
    assert parser("blue") is MyEnum.BLUE
    assert parser("green") is MyEnum.GREEN


def test_lookup_dict_caseignore():
    parser = LookupParser.case_insensitive(
        {
            "a": 1,
            "b": 2,
            "c": 3,
        }
    )

    assert parser("A") == 1
    assert parser("b") == 2
    assert parser("C") == 3

    with raises(ValueError):
        parser("D")


def test_basemodel2():
    class M(BaseModel2):
        a: int
        b: str

    p = parser(M)
    assert p('{"a": "1", "b": "hi"}') == M(a=1, b="hi")


def test_basemodel1():
    class M(BaseModel1):
        a: int
        b: str

    p = parser(M)
    assert p('{"a": "1", "b": "hi"}') == M(a=1, b="hi")


def test_rootmodel():
    m = RootModel[List[int]]
    p = parser(m)
    assert p("[1,2,3]") == m([1, 2, 3])


def test_typeadapter():
    t = TypeAdapter(List[int])
    p = parser(t)
    assert p("[1,2,3]") == [1, 2, 3]


@mark.parametrize("closer", ["];]", re.compile(r"\];\]")])
def test_delimited_boundries_collections(closer):
    assert CollectionParser(";", str, opener="[;[", closer=closer)("[;[a;b;c];]") == ["a", "b", "c"]


def test_finditer_parser():
    p = FindIterCollectionParser(re.compile(r"\d+(?:\s*)"), lambda m: int(m[0]))
    assert p("1 2 3 4") == [1, 2, 3, 4]


def test_finditer_parser_complex():
    @dataclass
    class Node:
        name: str
        values: List[int]

    values_parser = CollectionParser(";", int, opener="(", closer=")")
    p = FindIterCollectionParser(
        re.compile(r"(\w+)(?:\s*)(\(.*?\))?;?"), lambda m: Node(m[1], values_parser(m[2]) if m[2] else [])
    )
    assert p("a(1;2;3);b(4;5;6)") == [Node("a", [1, 2, 3]), Node("b", [4, 5, 6])]
