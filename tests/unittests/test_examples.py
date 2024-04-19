import enum
import re
from types import SimpleNamespace

from pytest import MonkeyPatch, fixture

from envolved import env_var
from envolved.parsers import CollectionParser, FindIterCollectionParser, LookupParser, MatchParser


class FakeEnviron:
    def __init__(self, monkeypatch: MonkeyPatch) -> None:
        self.monkeypatch = monkeypatch

    def __setitem__(self, key: str, value: str) -> None:
        self.monkeypatch.setenv(key, value)


@fixture()
def os():
    return SimpleNamespace(environ=FakeEnviron(MonkeyPatch()))


def test_bool_special_parser(os):
    enable_cache_ev = env_var("ENABLE_CACHE", type=bool)

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() is False


def test_bypass_bool_parser(os):
    enable_cache_ev = env_var("ENABLE_CACHE", type=lambda x: bool(x))

    os.environ["ENABLE_CACHE"] = "False"

    assert enable_cache_ev.get() is True


def test_collection_parser(os):
    countries = env_var("COUNTRIES", type=CollectionParser(",", str.lower, set))

    os.environ["COUNTRIES"] = "United States,Canada,Mexico"

    assert countries.get() == {"united states", "canada", "mexico"}


def test_collection_parser_pairwise(os):
    headers_ev = env_var("HTTP_HEADERS", type=CollectionParser.pair_wise_delimited(";", ":", str.upper, str))

    os.environ["HTTP_HEADERS"] = "Foo:bar;baz:qux"

    assert headers_ev.get() == {"FOO": "bar", "BAZ": "qux"}


def test_collection_parser_pairwise_2(os):
    server_params_ev = env_var(
        "SERVER_PARAMS",
        type=CollectionParser.pair_wise_delimited(
            ";",
            ":",
            str,
            {
                "host": str,
                "port": int,
                "is_ssl": bool,
            },
        ),
    )

    os.environ["SERVER_PARAMS"] = "host:localhost;port:8080;is_ssl:false"

    assert server_params_ev.get() == {"host": "localhost", "port": 8080, "is_ssl": False}


def test_find_iter_collection_parser(os):
    def parse_group(match: re.Match) -> set[int]:
        return {int(x) for x in match.group(1).split(",")}

    groups_ev = env_var("GROUPS", type=FindIterCollectionParser(re.compile(r"{([,\d]+)}(,|$)"), parse_group))

    os.environ["GROUPS"] = "{1,2,3},{4,5,6},{7,8,9}"

    assert groups_ev.get() == [{1, 2, 3}, {4, 5, 6}, {7, 8, 9}]


def test_match_parser(os):
    class Color(enum.Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    color_ev = env_var("COLOR", type=MatchParser(Color))

    os.environ["COLOR"] = "RED"

    assert color_ev.get() == Color.RED


def test_lookup_parser(os):
    class Color(enum.Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

    color_ev = env_var("COLOR", type=LookupParser(Color))

    os.environ["COLOR"] = "RED"

    assert color_ev.get() == Color.RED
