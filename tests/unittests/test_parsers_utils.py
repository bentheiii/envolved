import re

from pytest import mark, raises

from envolved.parsers import strip_opener_and_closer


@mark.parametrize("closer", ["]", re.compile(r"\]")])
def test_strip_bounds(closer):
    assert strip_opener_and_closer("[abca]", re.compile(r"\["), closer) == "abca"


@mark.parametrize("x", ["[aabc]", "[aabcaaaa]", "[bc]"])
def test_strip_bounds_dyn(x):
    assert strip_opener_and_closer(x, re.compile(r"\[a*"), re.compile(r"a*\]")) == "bc"


def test_strip_bounds_overlapping_closer():
    assert strip_opener_and_closer("fababa", re.compile(""), re.compile("aba")) == "fab"


def test_strip_no_closer():
    with raises(ValueError):
        strip_opener_and_closer("ab", re.compile("a"), re.compile("c"))


def test_strip_closer_not_at_end():
    with raises(ValueError):
        strip_opener_and_closer("abf", re.compile("a"), re.compile("b"))


@mark.parametrize("closer", ["a]", re.compile(r"a\]")])
def test_strip_no_double_strip(closer):
    with raises(ValueError):
        strip_opener_and_closer("[a]", re.compile(r"\[a"), closer)
