from __future__ import annotations

import re
from enum import Enum, auto
from functools import lru_cache
from itertools import chain
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    Mapping,
    Optional,
    Pattern,
    Tuple,
    Type,
    TypeVar,
    Union,
)

__all__ = ["Parser", "BoolParser", "CollectionParser", "parser"]

from envolved.utils import extract_from_option

T = TypeVar("T")

Parser = Callable[[str], T]
ParserInput = Union[Parser[T], Type[T]]

special_parsers: Dict[ParserInput[Any], Parser[Any]] = {
    bytes: str.encode,
}


def complex_parser(x: str) -> complex:
    x = x.replace("i", "j")
    return complex(x)


special_parsers[complex] = complex_parser


class BoolParser:
    """
    A helper to parse boolean values from text
    """

    def __init__(
        self,
        maps_to_true: Iterable[str] = (),
        maps_to_false: Iterable[str] = (),
        *,
        default: Optional[bool] = None,
        case_sensitive: bool = False,
    ):
        """
        :param maps_to_true: An iterable of string values that should evaluate to True
        :param maps_to_false: An iterable of string values that should evaluate to True
        :param default: The behaviour for when the value is vacant from both the true iterable and the falsish iterable.
        :param case_sensitive: Whether the string values should match exactly or case-insensitivity.
        """
        if not case_sensitive:
            maps_to_true = map(str.lower, maps_to_true)
            maps_to_false = map(str.lower, maps_to_false)

        self.truth_set = frozenset(maps_to_true)
        self.false_set = frozenset(maps_to_false)

        self.case_sensitive = case_sensitive
        self.default = default

    def __call__(self, x: str) -> bool:
        if not self.case_sensitive:
            x = x.lower()
        if x in self.truth_set:
            return True
        if x in self.false_set:
            return False
        if self.default is None:
            raise ValueError(
                f"must evaluate to either true ({', '.join(self.truth_set)}) or" f" false ({', '.join(self.false_set)})"
            )
        return self.default


special_parsers[bool] = BoolParser(["true"], ["false"])


def parser(t: ParserInput[T]) -> Parser[T]:
    """
    Coerce an object into a parser.
    :param t: The object to coerce to a parser.
    :return: The best-match parser for `t`.
    """
    special_parser = special_parsers.get(t)
    if special_parser is not None:
        return special_parser

    from_option = extract_from_option(t)
    if from_option is not None:
        return parser(from_option)

    if isinstance(t, type) and issubclass(t, Enum):
        return MatchParser.case_insensitive(t)

    if callable(t):
        return t

    raise TypeError(f"cannot coerce type {t!r} to a parser")


E = TypeVar("E")
G = TypeVar("G")

empty_pattern = re.compile("")

Needle = Union[str, Pattern[str]]

_no_regex_flags = re.RegexFlag(0)


def needle_to_pattern(n: Needle, flags: re.RegexFlag = _no_regex_flags) -> Pattern[str]:
    if isinstance(n, str):
        return re.compile(re.escape(n), flags)
    return n


K = TypeVar("K")
V = TypeVar("V")


def _duplicate_avoiding_dict(pairs: Iterator[Tuple[K, V]]) -> Dict[K, V]:
    """
    The default output_type of CollectionParser.delimited_pairwise. Returns a dict from key-value pairs while
     ensuring there are no duplicate keys.
    """
    ret = {}
    for k, v in pairs:
        if k in ret:
            raise ValueError(f"duplicate key {k}")
        ret[k] = v
    return ret


class CollectionParser(Generic[G, E]):
    """
    A parser that splits a string by a delimiter, and parses each part individually.
    """

    def __init__(
        self,
        delimiter: Needle,
        inner_parser: ParserInput[E],
        output_type: Callable[[Iterator[E]], G] = list,  # type: ignore[assignment]
        opener: Needle = empty_pattern,
        closer: Needle = empty_pattern,
    ):
        """
        :param delimiter: The delimiter to split by.
        :param inner_parser: The inner parser to apply to each element.
        :param output_type: The aggregator function of all the parsed elements.
        :param opener: Optional opener that must be present at the start of the string.
        :param closer: Optional closer that must be present at the end of the string.
        """
        self.delimiter_pattern = needle_to_pattern(delimiter)
        self.inner_parser = parser(inner_parser)
        self.output_type = output_type
        self.opener_pattern = needle_to_pattern(opener)
        self.closer_pattern = needle_to_pattern(closer)

    def __call__(self, x: str) -> G:
        opener_match = self.opener_pattern.match(x)
        if not opener_match:
            raise ValueError("position 0, expected opener")
        x = x[opener_match.end() :]
        raw_elements = self.delimiter_pattern.split(x)
        closer_matches = self.closer_pattern.finditer(raw_elements[-1])

        closer_match = None
        for closer_match in closer_matches:  # noqa: B007
            pass
        if not closer_match:
            raise ValueError("expected string to end in closer")
        elif closer_match.end() != len(raw_elements[-1]):
            raise ValueError(
                "expected closer to match end of string, got unexpected suffix: "
                + raw_elements[-1][closer_match.end() :]
            )

        raw_elements[-1] = raw_elements[-1][: closer_match.start()]
        elements = (self.inner_parser(r.strip()) for r in raw_elements)
        return self.output_type(elements)

    @classmethod
    def pair_wise_delimited(
        cls,
        pair_delimiter: Needle,
        key_value_delimiter: Needle,
        key_type: ParserInput[K],
        value_type: Union[ParserInput[V], Mapping[K, ParserInput[V]]],
        output_type: Callable[[Iterator[Tuple[K, V]]], G] = _duplicate_avoiding_dict,  # type: ignore[assignment]
        *,
        key_first: bool = True,
        **kwargs: Any,
    ) -> Parser[G]:
        """
        Create a collectionParser that aggregates to key-value pairs.
        :param pair_delimiter: The separator between different key-value pairs.
        :param key_value_delimiter: The separator between each key and value.
        :param key_type: The parser for key elements.
        :param value_type: The parser for value elements. Can also be a mapping, parsing each key under a different
         parser.
        :param output_type: The tuple aggregator function. Defaults to a duplicate-checking dict.
        :param key_first: If set to false, will evaluate the part behind the key-value separator as a value.
        :param kwargs: forwarded to `CollectionParser.__init__`
        """
        key_value_delimiter = needle_to_pattern(key_value_delimiter)
        key_parser = parser(key_type)
        get_value_parser: Callable[[K], Parser]
        if isinstance(value_type, Mapping):

            @lru_cache(None)
            def get_value_parser(key: K) -> Parser[V]:
                return parser(value_type[key])
        else:
            _value_parser = parser(value_type)

            def get_value_parser(key: K) -> Parser[V]:
                return _value_parser

        def combined_parser(s: str) -> Any:
            split = key_value_delimiter.split(s, maxsplit=2)
            if len(split) != 2:
                raise ValueError(f"expecting key-value pair, got {s}")
            k, v = split
            if not key_first:
                k, v = v, k
            key = key_parser(k)
            value = get_value_parser(key)(v)
            return key, value

        return cls(pair_delimiter, combined_parser, output_type, **kwargs)  # type: ignore[arg-type]


class NoFallback(Enum):
    no_fallback = auto()


no_fallback = NoFallback.no_fallback

CasesInput = Union[Iterable[Tuple[Needle, T]], Mapping[str, T], Type[Enum]]
CasesInputIgnoreCase = Union[Iterable[Tuple[str, T]], Mapping[str, T], Type[Enum]]


class MatchParser(Generic[T]):
    @classmethod
    def _ensure_case_unique(cls, matches: Iterable[str]):
        seen_cases = set()
        for k in matches:
            key = k.lower()
            if key in seen_cases:
                raise ValueError(f"duplicate case-invariant key {k}")
            seen_cases.add(key)

    @classmethod
    def _cases(cls, x: CasesInput, ignore_case: bool) -> Iterable[Tuple[Pattern[str], T]]:
        if isinstance(x, Mapping):
            if ignore_case and __debug__:
                cls._ensure_case_unique(x.keys())
            return cls._cases(x.items(), ignore_case)
        if isinstance(x, type) and issubclass(x, Enum):
            return cls._cases(x.__members__, ignore_case)
        flags = _no_regex_flags
        if ignore_case:
            flags |= re.IGNORECASE
        return ((needle_to_pattern(n, flags), v) for n, v in x)

    def __init__(self, cases: CasesInput, fallback: Union[T, NoFallback] = no_fallback):
        cases_inp = self._cases(cases, ignore_case=False)
        if fallback is not no_fallback:
            cases_inp = chain(cases_inp, [(re.compile(".*"), fallback)])
        self.candidates = [(needle_to_pattern(n), v) for n, v in cases_inp]

    @classmethod
    def case_insensitive(
        cls, cases: CasesInputIgnoreCase, fallback: Union[T, NoFallback] = no_fallback
    ) -> MatchParser[T]:
        cases_inp = cls._cases(cases, ignore_case=True)
        return cls(cases_inp, fallback)

    def __call__(self, x: str) -> T:
        for pattern, value in self.candidates:
            if pattern.fullmatch(x):
                return value
        raise ValueError(f"no match for {x}")
