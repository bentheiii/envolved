from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from typing import (
    Dict, Callable, Iterable, Optional, TypeVar, Generic, Pattern, Union, Any, Tuple, Type, Mapping, Iterator,
    get_type_hints, NamedTuple, FrozenSet, Sequence
)

from envolved.utils import factory_type_hints

if sys.version_info >= (3, 8, 0):
    from typing import get_args, get_origin
else:
    def get_origin(v):
        return getattr(v, '__origin__', None)

    def get_args(v):
        return getattr(v, '__args__', None)

try:
    from typing import TypedDict
except ImportError:
    TypedDict = TDMeta = None
else:
    TDMeta = type(TypedDict('TD', {'x': str}))

__all__ = ['Parser', 'BoolParser', 'CollectionParser', 'JsonParser', 'parser']

T = TypeVar('T')

# pytype: disable=invalid-annotation
Parser = Callable[[str], T]
ParserInput = Union[Parser[T], Type[T]]

special_parsers: Dict[type, Parser[Any]] = {}


def complex_parser(x: str):
    x = x.replace('i', 'j')
    return complex(x)


special_parsers[complex] = complex_parser


class BoolParser(Parser[bool]):
    """
    A helper to parse boolean values from text
    """

    def __init__(self, maps_to_true: Iterable[str] = (), maps_to_false: Iterable[str] = (), *,
                 default: Optional[bool] = None, case_sensitive: bool = False):
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

    def __call__(self, x: str):
        if not self.case_sensitive:
            x = x.lower()
        if x in self.truth_set:
            return True
        if x in self.false_set:
            return False
        if self.default is None:
            raise ValueError(f"must evaluate to either true ({', '.join(self.truth_set)}) or"
                             f" false ({', '.join(self.false_set)})")
        return self.default


special_parsers[bool] = BoolParser(['true'], ['false'])


def parser(t: ParserInput[T]) -> Parser[T]:
    """
    Coerce an object into a parser.
    :param t: The object to coerce to a parser.
    :return: The best-match parser for `t`.
    """
    if t in special_parsers:
        return special_parsers[t]

    if callable(t):
        return t

    raise TypeError


E = TypeVar('E')
G = TypeVar('G')

empty_pattern = re.compile('')

Needle = Union[str, Pattern[str]]


def needle_to_pattern(n: Needle) -> Pattern:
    """
    :param n: either a string or compiled regex pattern.
    :return: `n` converted to a regex pattern
    """
    if isinstance(n, str):
        return re.compile(re.escape(n))
    return n


K = TypeVar('K')
V = TypeVar('V')


def _duplicate_avoiding_dict(pairs: Iterator[Tuple[Any, Any]]):
    """
    The default output_type of CollectionParser.delimited_pairwise. Returns a dict from key-value pairs while
     ensuring there are no duplicate keys.
    """
    ret = {}
    for k, v in pairs:
        if k in ret:
            raise ValueError(f'duplicate key {k}')
        ret[k] = v
    return ret


class CollectionParser(Parser[G], Generic[G, E]):
    """
    A parser that splits a string by a delimiter, and parses each part individually.
    """

    def __init__(self, delimiter: Needle, inner_parser: ParserInput[E],
                 output_type: Callable[[Iterator[E]], G] = list, trailing_delimiter: Optional[bool] = None,
                 opener: Needle = empty_pattern, closer: Needle = empty_pattern):
        """
        :param delimiter: The delimiter to split by.
        :param inner_parser: The inner parser to apply to each element.
        :param output_type: The aggregator function of all the parsed elements.
        :param trailing_delimiter: Whether to accept or require a delimiter after all other elements. Default value is
         to accept, but not require.
        :param opener: Optional opener that must be present at the start of the string.
        :param closer: Optional closer that must be present at the end of the string.
        """
        self.delimiter_pattern = needle_to_pattern(delimiter)
        self.inner_parser = parser(inner_parser)
        self.output_type = output_type
        self.opener_pattern = needle_to_pattern(opener)
        self.closer_pattern = needle_to_pattern(closer)
        self.trailing_delimiter = trailing_delimiter

    def __call__(self, x: str):
        opener_match = self.opener_pattern.match(x)
        if not opener_match:
            raise ValueError('position 0, expected opener')
        x = x[opener_match.end():]
        raw_elements = self.delimiter_pattern.split(x)
        closer_matches = self.closer_pattern.finditer(raw_elements[-1])

        closer_match = None
        for closer_match in closer_matches:
            pass
        if not closer_match:
            raise ValueError('expected string to end in closer')

        raw_elements[-1] = raw_elements[-1][:closer_match.start()]
        if not raw_elements[-1]:
            if self.trailing_delimiter or self.trailing_delimiter is None:
                raw_elements.pop()
        elif self.trailing_delimiter:
            raise ValueError('expected trailing delimiter')
        elements = (self.inner_parser(r.strip()) for r in raw_elements)
        return self.output_type(elements)

    @classmethod
    def pair_wise_delimited(cls, pair_delimiter: Needle, key_value_delimiter: Needle,
                            key_type: ParserInput[K], value_type: Union[ParserInput[V], Mapping[K, ParserInput[V]]],
                            output_type: Callable[[Iterator[Tuple[K, V]]], G] = _duplicate_avoiding_dict, *,
                            key_first: bool = True, **kwargs):
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
        if isinstance(value_type, Mapping):
            @lru_cache(None)
            def get_value_parser(key):
                return parser(value_type[key])
        else:
            _value_parser = parser(value_type)

            def get_value_parser(key):
                return _value_parser

        def combined_parser(s: str):
            split = key_value_delimiter.split(s, maxsplit=2)
            if len(split) != 2:
                raise ValueError(f'expecting key-value pair, got {s}')
            k, v = split
            if not key_first:
                k, v = v, k
            key = key_parser(k)
            value = get_value_parser(key)(v)
            return key, value

        return cls(pair_delimiter, combined_parser, output_type, **kwargs)


no_default = object()


class _JsonDictSpecs(NamedTuple):
    annotations: Mapping[str, Any]
    required: FrozenSet[str]
    default_annotation: Any = no_default


class JsonParser(Parser):
    """
    A parser to parse json strings.
    """

    def __init__(self, expected_type: Any):
        """
        :param expected_type: If other than `object`, parsing will fail if the parsed value is of a different type.
        """
        self.expected_type = expected_type

    @classmethod
    def validate_type(cls, value, t):
        if t in (object, Any):
            return True
        if t is None:
            return value is None
        if type(t) in (bool, int, float, str):
            return cls.validate_type(value, type(t)) and value == t
        if isinstance(t, _JsonDictSpecs):
            if type(value) is not dict:
                return False
            required = set(t.required)
            for k, value in value.items():
                required.discard(k)
                try:
                    annotation = t.annotations[k]
                except KeyError:
                    if t.default_annotation is no_default:
                        return False
                    annotation = t.default_annotation
                if not cls.validate_type(value, annotation):
                    return False
            if required:
                return False
            return True
        if isinstance(t, Mapping):
            jds = _JsonDictSpecs(
                t,
                frozenset(t)
            )
            return cls.validate_type(value, jds)
        if TDMeta and isinstance(t, TDMeta):
            type_hints = get_type_hints(t)
            jds = _JsonDictSpecs(
                type_hints,
                frozenset(type_hints) if t.__total__ else frozenset()
            )
            return cls.validate_type(value, jds)
        if isinstance(t, type):
            if t is float:
                return type(value) in (int, float)
            return type(value) is t
        if type(t) is tuple:
            return any(cls.validate_type(value, i) for i in t)
        origin = get_origin(t)
        if origin:
            args = get_args(t)
            if origin is Union:
                return any(cls.validate_type(value, i) for i in args)

            # generic alias
            if not isinstance(value, origin):
                return False
            # we tell if the generic alias is special by checking if we can typecheck against it
            try:
                isinstance(None, t)
            except TypeError:
                pass
            else:
                # alias is special, no point to check further
                return True

            if issubclass(origin, Sequence):
                arg, = args
                return all(cls.validate_type(i, arg) for i in value)
            if issubclass(origin, Mapping):
                k_arg, v_arg = args
                return all(
                    (cls.validate_type(k, k_arg) and cls.validate_type(v, v_arg))
                    for (k, v) in value.items()
                )
            raise TypeError(f'unrecognized origin {origin}')
        if callable(t):
            type_hints = factory_type_hints(t)
            default_annotation = (
                type_hints.variadic_annotation
                if type_hints.variadic_annotation is not ...
                else no_default
            )
            jds = _JsonDictSpecs(
                type_hints,
                frozenset(type_hints.required),
                default_annotation
            )
            return cls.validate_type(value, jds)
        raise TypeError(f'unrecognized expected type {t}')

    def __call__(self, x: str):
        decoded = json.loads(x)
        if not self.validate_type(decoded, self.expected_type):
            raise ValueError(f'expected type {self.expected_type}, got {type(decoded)}')
        return decoded
