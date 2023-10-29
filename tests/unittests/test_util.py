import sys
from functools import reduce
from typing import Optional, Union

from pytest import mark

from envolved.utils import extract_from_option


@mark.parametrize("t", [int, str])
def test_extract_from_union(t):
    assert extract_from_option(Union[t, None]) is t
    assert extract_from_option(Union[None, t]) is t
    assert extract_from_option(Optional[t]) is t


@mark.parametrize("t", [Union[int, str], int, str, Union[None, None], Union[str, int, None], None])  # noqa: PYI016
def test_extract_from_union_fail(t):
    assert extract_from_option(t) is None


@mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
@mark.parametrize("t", [int, str])
def test_extract_from_new_union(t):
    assert extract_from_option(t | None) is t
    assert extract_from_option(None | t) is t


@mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
@mark.parametrize("t", [[int, str], [type(None), type(None)], [str, int, None]])
def test_extract_from_new_union_fail(t):
    t = reduce(lambda a, b: a | b, t)
    assert extract_from_option(t) is None
