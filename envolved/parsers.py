from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from typing import (
    Dict, Callable, Iterable, Optional, TypeVar, Generic, Pattern, Union, List, Any, Tuple, Type, Mapping, Iterator,
    Container
)

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
    TDMeta = None
else:
    TDMeta = type(TypedDict('TD', {'x': str}))
    del TypedDict

__all__ = ['Parser', 'BoolParser', 'CollectionParser', 'JsonParser', 'parser']

T = TypeVar('T')

Parser = Callable[[str], T]
ParserInput = Union[Parser[T], Type[T]]

text_parser: Dict[type, Parser] = {}

for t in (str, int, float):
    text_parser[t] = t


def complex_parser(x: str):
    x = x.replace('i', 'j')
    return complex(x)


text_parser[complex] = complex_parser


class BoolParser(Parser[bool]):
    def __init__(self, maps_to_true: Iterable[str], maps_to_false: Iterable[str], *,
                 default_case: Optional[bool] = None, case_sensitive: bool = False):
        if not case_sensitive:
            maps_to_true = map(str.lower, maps_to_true)
            maps_to_false = map(str.lower, maps_to_false)

        self.truth_set = frozenset(maps_to_true)
        self.false_set = frozenset(maps_to_false)

        self.case_sensitive = case_sensitive
        self.default_case = default_case

    def __call__(self, x: str):
        if not self.case_sensitive:
            x = x.lower()
        if x in self.truth_set:
            return True
        if x in self.false_set:
            return False
        if self.default_case is None:
            raise ValueError(f"must evaluate to either true ({', '.join(self.truth_set)}) or"
                             f" false ({', '.join(self.false_set)})")
        return self.default_case


text_parser[bool] = BoolParser(['true'], ['false'])


def parser(t: ParserInput[T]) -> Parser[T]:
    if t in text_parser:
        return text_parser[t]

    if callable(t):
        return t

    raise TypeError


E = TypeVar('E')
G = TypeVar('G')

empty_pattern = re.compile('')

Needle = Union[str, Pattern[str]]


def needle_to_pattern(n: Needle) -> Pattern:
    if isinstance(n, Pattern):
        return n
    return re.compile(re.escape(n))


K = TypeVar('K')
V = TypeVar('V')


def _duplicate_avoiding_dict(pairs: Iterator[Tuple[Any, Any]]):
    ret = {}
    for k, v in pairs:
        if k in ret:
            raise ValueError(f'duplicate key {k}')
        ret[k] = v
    return ret


class CollectionParser(Parser[G], Generic[G, E]):
    def __init__(self, delimiter_pattern: Pattern[str], inner_parser: Callable[[T], E],
                 trailing_delimiter: Optional[bool], output_type: Callable[[Iterator[E]], G],
                 opener_pattern: Pattern[str], closer_pattern: Pattern[str]):
        self.delimiter_pattern = delimiter_pattern
        self.inner_parser = inner_parser
        self.output_type = output_type
        self.opener_pattern = opener_pattern
        self.closer_pattern = closer_pattern
        self.trailing_delimiter = trailing_delimiter

    def __call__(self, x: str):
        opener_match = self.opener_pattern.match(x)
        if not opener_match:
            raise ValueError('position 0, expected opener')
        x = x[opener_match.end():]
        raw_elements = self.delimiter_pattern.split(x)
        closer_matches = self.closer_pattern.finditer(raw_elements[-1])
        if not closer_matches:
            raise ValueError('expected string to end in closer')
        closer_match = None
        for closer_match in closer_matches:
            pass
        raw_elements[-1] = raw_elements[-1][:closer_match.start()]
        if not raw_elements[-1]:
            if self.trailing_delimiter or self.trailing_delimiter is None:
                raw_elements.pop()
        elif self.trailing_delimiter:
            raise ValueError('expected trailing delimiter')
        elements = (self.inner_parser(r.strip()) for r in raw_elements)
        return self.output_type(elements)

    @classmethod
    def delimited(cls, separator: Needle, inner_type, output_type: Callable[[Iterator[E]], G] = list, *,
                  trailing_separator: Optional[bool] = None, opener_pattern: Needle = empty_pattern,
                  closer_pattern: Needle = empty_pattern):
        inner_converter = parser(inner_type)

        return cls(needle_to_pattern(separator), inner_converter, trailing_separator, output_type,
                   needle_to_pattern(opener_pattern), needle_to_pattern(closer_pattern))

    @classmethod
    def pair_wise_delimited(cls, pair_separator: Needle, key_value_separator: Needle,
                            key_type: ParserInput[K], value_type: Union[ParserInput[V], Mapping[K, ParserInput[V]]],
                            output_type: Callable[[List[Tuple[K, V]]], G] = _duplicate_avoiding_dict, *,
                            trailing_separator: Optional[bool] = None, key_first: bool = True,
                            opener_pattern: Needle = empty_pattern, closer_pattern: Needle = empty_pattern):
        key_value_separator = needle_to_pattern(key_value_separator)
        key_parser = parser(key_type)
        if isinstance(value_type, Mapping):
            @lru_cache
            def get_value_parser(key):
                return parser(value_type[key])
        else:
            _value_parser = parser(value_type)

            def get_value_parser(key):
                return _value_parser

        def actual_parser(s: str):
            split = key_value_separator.split(s, maxsplit=2)
            if len(split) != 2:
                raise ValueError(f'expecting key-value pair, got {s}')
            k, v = split
            if not key_first:
                k, v = v, k
            key = key_parser(k)
            value = get_value_parser(key)(v)
            return key, value

        return cls.delimited(pair_separator, actual_parser, output_type,
                             trailing_separator=trailing_separator, opener_pattern=opener_pattern,
                             closer_pattern=closer_pattern)


class JsonParser(Parser):
    def __init__(self, expected_type: Any):
        self.expected_type = expected_type

    @classmethod
    def validate_type(cls, v, t):
        origin = get_origin(t)
        if origin is None:
            if type(v) is t:
                return
            if type(v) is int and t is float:
                return
            elif isinstance(t, Container) and type(v) in t:
                return
            elif TDMeta and isinstance(t, TDMeta) and type(v) is dict:
                not_seen = dict(t.__annotations__)
                for k, value in v.items():
                    try:
                        annotation = not_seen.pop(k)
                    except KeyError:
                        if t.__total__:
                            raise ValueError(f'unexpected key {k}')
                        continue
                    cls.validate_type(value, annotation)
                if not_seen:
                    raise ValueError(f'expected keys {list(not_seen)}')
                return

            raise ValueError(f'expected an object of type {t}, got {type(v).__name__} instead')

        if not isinstance(v, origin):
            raise ValueError(f'expected an object of type {t}, got {type(v).__name__} instead')

        # we tell if the generic alias is special by checking if we can typecheck against it
        try:
            isinstance(None, t)
        except TypeError:
            pass
        else:
            # alias is special, no point to check further
            return
        args = get_args(t)
        if origin is list:
            arg, = args
            for i in v:
                cls.validate_type(i, arg)
        elif origin is dict:
            k_arg, v_arg = args
            for key, value in v.items():
                cls.validate_type(key, k_arg)
                cls.validate_type(value, v_arg)
        else:
            raise TypeError(f'unrecognized origin {origin}')

    def __call__(self, x: str):
        decoded = json.loads(x)
        if self.expected_type is not object:
            self.validate_type(decoded, self.expected_type)
        return decoded
