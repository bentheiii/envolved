from __future__ import annotations

import re
from enum import Enum, auto
from itertools import chain
from sys import version_info
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

from typing_extensions import Concatenate, TypeAlias

from envolved.utils import extract_from_option

__all__ = ["Parser", "BoolParser", "CollectionParser", "parser"]


BaseModel1: Optional[Type]
BaseModel2: Optional[Type]
TypeAdapter: Optional[Type]

try:  # pydantic v2
    from pydantic import BaseModel as BaseModel2, TypeAdapter
    from pydantic.v1 import BaseModel as BaseModel1
except ImportError:
    BaseModel2 = TypeAdapter = None
    try:  # pydantic v1
        from pydantic import BaseModel as BaseModel1
    except ImportError:
        BaseModel1 = None

T = TypeVar("T")

if version_info >= (3, 11):
    # theoretically, I'd like to restrict this to keyword arguments only, but that's not possible yet in python
    Parser: TypeAlias = Callable[Concatenate[str, ...], T]
else:
    # we can only use Concatenate[str, ...] in python 3.11+
    Parser: TypeAlias = Callable[[str], T]  # type: ignore[misc, no-redef]

ParserInput = Union[Parser[T], Type[T]]

special_parser_inputs: Dict[ParserInput[Any], Parser[Any]] = {
    bytes: str.encode,
}

parser_special_instances: Dict[Type, Callable[[Any], Parser]] = {}
if TypeAdapter is not None:
    parser_special_instances[TypeAdapter] = lambda t: t.validate_json

parser_special_superclasses: Dict[Type, Callable[[Type], Parser]] = {}
if BaseModel1 is not None:
    parser_special_superclasses[BaseModel1] = lambda t: t.parse_raw
if BaseModel2 is not None:
    parser_special_superclasses[BaseModel2] = lambda t: t.model_validate_json


def complex_parser(x: str) -> complex:
    x = x.replace("i", "j")
    return complex(x)


special_parser_inputs[complex] = complex_parser


def parser(t: ParserInput[T]) -> Parser[T]:
    """
    Coerce an object into a parser.
    :param t: The object to coerce to a parser.
    :return: The best-match parser for `t`.
    """
    special_parser = special_parser_inputs.get(t)
    if special_parser is not None:
        return special_parser

    from_option = extract_from_option(t)
    if from_option is not None:
        return parser(from_option)

    for special_cls, parser_factory in parser_special_instances.items():
        if isinstance(t, special_cls):
            return parser_factory(t)

    if isinstance(t, type):
        for supercls, parser_factory in parser_special_superclasses.items():
            if issubclass(t, supercls):
                return parser_factory(t)

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


def strip_opener_idx(x: str, opener: Pattern[str]) -> int:
    opener_match = opener.match(x)
    if not opener_match:
        raise ValueError("position 0, expected opener")
    return opener_match.end()


def strip_closer_idx(x: str, closer: Needle, pos: int) -> int:
    if isinstance(closer, str):
        if len(closer) + pos > len(x) or not x.endswith(closer):
            raise ValueError("expected string to end in closer")
        return len(x) - len(closer)
    else:
        assert isinstance(closer, Pattern)
        # now we have a problem, as the standard re module doesn't support reverse matches
        closer_matches = closer.finditer(x, pos)
        closer_match = None
        for closer_match in closer_matches:  # noqa: B007
            # we iterate to find the last match
            pass
        if not closer_match:
            raise ValueError("expected string to end in closer")
        else:
            while closer_match.end() != len(x):
                # finditer could have missed an overlapping match, if there is an overlapping match
                # it will be found after the start of the last match (but before its end)
                closer_match = closer.search(x, closer_match.start() + 1)
                # if there is a match, it's an overlapping match, but it doesn't neccessarily end at
                # the end of the string
                if not closer_match:
                    raise ValueError("expected string to end in closer")
        return closer_match.start()


def strip_opener_and_closer(x: str, opener: Pattern[str], closer: Needle) -> str:
    start_idx = strip_opener_idx(x, opener)
    end_idx = strip_closer_idx(x, closer, start_idx)

    if start_idx != 0 or end_idx != len(x):
        return x[start_idx:end_idx]
    return x


def value_parser_func(value_type: Union[ParserInput[V], Mapping[K, ParserInput[V]]]) -> Callable[[K], Parser[V]]:
    if isinstance(value_type, Mapping):
        value_parsers = {k: parser(v) for k, v in value_type.items()}

        def get_value_parser(key: K) -> Parser[V]:
            try:
                return value_parsers[key]
            except KeyError:
                # in case the mapping has a default value or the like
                return parser(value_type[key])
    else:
        _value_parser = parser(value_type)

        def get_value_parser(key: K) -> Parser[V]:
            return _value_parser

    return get_value_parser


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
        closer: Needle = "",
        *,
        strip: bool = True,
    ):
        self.delimiter_pattern = needle_to_pattern(delimiter)
        self.inner_parser = parser(inner_parser)
        self.output_type = output_type
        self.opener_pattern = needle_to_pattern(opener)
        self.closer = closer
        self.strip = strip

    def __call__(self, x: str) -> G:
        x = strip_opener_and_closer(x, self.opener_pattern, self.closer)
        raw_items = iter(self.delimiter_pattern.split(x))
        if self.strip:
            raw_items = (r.strip() for r in raw_items)
        elements = (self.inner_parser(r) for r in raw_items)
        return self.output_type(elements)

    @classmethod
    def pair_wise_delimited(
        cls,
        pair_delimiter: Needle,
        key_value_delimiter: Needle,
        key_type: ParserInput[K],
        value_type: Union[ParserInput[V], Mapping[K, ParserInput[V]]],
        output_type: Callable[[Iterator[Tuple[K, V]]], G] = _duplicate_avoiding_dict,  # type: ignore[assignment]
        key_first: bool = True,
        strip_keys: bool = True,
        strip_values: bool = True,
        **kwargs: Any,
    ) -> Parser[G]:
        key_value_delimiter = needle_to_pattern(key_value_delimiter)
        key_parser = parser(key_type)
        get_value_parser = value_parser_func(value_type)

        def combined_parser(s: str) -> Tuple[K, V]:
            split = key_value_delimiter.split(s, maxsplit=2)
            if len(split) != 2:
                raise ValueError(f"expecting key-value pair, got {s}")
            k, v = split
            if not key_first:
                k, v = v, k
            if strip_keys:
                k = k.strip()
            if strip_values:
                v = v.strip()
            key = key_parser(k)
            value = get_value_parser(key)(v)
            return key, value

        return cls(pair_delimiter, combined_parser, output_type, **kwargs)  # type: ignore[arg-type]


def find_iter_contingient(x: str, pattern: Pattern[str]) -> Iterator[re.Match[str]]:
    start_idx = 0
    while start_idx < len(x):
        match = pattern.match(x, start_idx)
        if match is None:
            raise ValueError(f"could not match pattern {pattern} at position {start_idx}")
        start_idx = match.end()
        yield match


class FindIterCollectionParser(Generic[G, E]):
    def __init__(
        self,
        element_pattern: Pattern[str],
        element_func: Callable[[re.Match[str]], E],
        output_type: Callable[[Iterator[E]], G] = list,  # type: ignore[assignment]
        opener: Needle = empty_pattern,
        closer: Needle = "",
    ):
        self.prefix_pattern = element_pattern
        self.element_func = element_func
        self.output_type = output_type
        self.opener_pattern = needle_to_pattern(opener)
        self.closer = closer

    def __call__(self, x: str) -> G:
        x = strip_opener_and_closer(x, self.opener_pattern, self.closer)
        raw_matches = find_iter_contingient(x, self.prefix_pattern)
        elements = (self.element_func(r) for r in raw_matches)
        return self.output_type(elements)


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


LookupCases = Union[Iterable[Tuple[str, T]], Mapping[str, T], Type[Enum]]


class LookupParser(Generic[T]):
    def __init__(
        self, lookup: LookupCases, fallback: Union[T, NoFallback] = no_fallback, *, _case_sensitive: bool = True
    ):
        cases: Iterable[Tuple[str, T]]
        if isinstance(lookup, Mapping):
            cases = lookup.items()
        elif isinstance(lookup, type) and issubclass(lookup, Enum):
            cases = lookup.__members__.items()  # type: ignore[assignment]
        else:
            cases = lookup

        if _case_sensitive:
            self.lookup = dict(cases)
        else:
            self.lookup = {k.lower(): v for k, v in cases}
        self.fallback = fallback
        self.case_sensitive = _case_sensitive

    @classmethod
    def case_insensitive(cls, lookup: LookupCases, fallback: Union[T, NoFallback] = no_fallback) -> LookupParser[T]:
        return cls(lookup, fallback, _case_sensitive=False)

    def __call__(self, x: str) -> T:
        if not self.case_sensitive:
            key = x.lower()
        else:
            key = x
        try:
            return self.lookup[key]
        except KeyError as e:
            if self.fallback is no_fallback:
                raise ValueError(f"no match for {x}") from e
            return self.fallback


parser_special_superclasses[Enum] = LookupParser.case_insensitive  # type: ignore[assignment]


class BoolParser(LookupParser[bool]):
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
        super().__init__(
            chain(
                ((x, True) for x in maps_to_true),
                ((x, False) for x in maps_to_false),
            ),
            fallback=default if default is not None else no_fallback,
            _case_sensitive=case_sensitive,
        )


special_parser_inputs[bool] = BoolParser(["true"], ["false"])
