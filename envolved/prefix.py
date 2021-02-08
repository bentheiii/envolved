from __future__ import annotations

import re
from functools import partial
from operator import itemgetter
from string import whitespace
from textwrap import TextWrapper
from typing import Pattern, TypeVar, Generic, Callable, Tuple, List, Collection, TYPE_CHECKING, Union, Match

from envolved.basevar import BaseVar, ValidatorCallback, BaseVarResult
from envolved.envparser import prefix_parser

if TYPE_CHECKING:
    from envolved.envvar import EnvVar

M = TypeVar('M')
K = TypeVar('K')
V = TypeVar('V')


class PrefixVar(BaseVar[M], Generic[M, K, V]):
    def __init__(self, key: str, prefix_capture: Pattern[str], inner_parent: EnvVar[V],
                 aggregator: Callable[[Collection[Tuple[K, V]]], M] = dict, case_sensitive: bool = False,
                 description: str = None, match_key_callback: Union[Callable[[Match[str]], K], str, int] = 0):
        if not case_sensitive and not (prefix_capture.flags & re.IGNORECASE):
            # add case insensitivity if needed
            prefix_capture = re.compile(prefix_capture.pattern, prefix_capture.flags | re.IGNORECASE)
        if not callable(match_key_callback):
            match_key_callback = itemgetter(match_key_callback)

        self.key = key
        self.prefix_capture = prefix_capture
        self.inner_parent = inner_parent
        self.aggregator = aggregator
        self.case_sensitive = case_sensitive
        self.match_key_callback = match_key_callback
        self._description = description

        self._validators: List[ValidatorCallback[M]] = []

        self.inner_parent.owner = self

    def _child(self, subprefix, _raw=False):
        if _raw:
            key = subprefix
        else:
            key = self.key + subprefix
        ret = self.inner_parent.child(key)
        ret.owner = self
        return ret

    def get_(self):
        pairs = []
        sub_prefixes = set()
        for key, _ in prefix_parser.get_envs_with_prefix(self.key, self.case_sensitive):
            postfix = key[len(self.key):]
            sub_prefix_match = self.prefix_capture.match(postfix)
            if not sub_prefix_match:
                continue
            sub_prefix = sub_prefix_match[0]
            result_key = self.match_key_callback(sub_prefix_match)
            if sub_prefix in sub_prefixes:
                continue
            sub_prefixes.add(sub_prefix)
            child = self._child(sub_prefix)
            value = child.get()
            pairs.append((result_key, value))
        agg = self.aggregator(pairs)
        for validator in self._validators:
            agg = validator(agg)
        return BaseVarResult(agg, bool(pairs))

    def validator(self, func: Callable = None, *, per_element=False):
        if func is None:
            return partial(self.validator, per_element=per_element)

        if isinstance(func, staticmethod):
            callback = func.__func__
        else:
            callback = func

        if per_element:
            self.inner_parent.validator(func)
        else:
            self._validators.append(callback)

        return super().validator(func)

    def description(self, parent_wrapper: TextWrapper) -> List[str]:
        key = self.key.strip(whitespace + '_')
        if self.case_sensitive:
            key = key.upper()
        if self._description:
            desc = ' '.join(self._description.strip().split())
            suffix = ': ' + desc
        else:
            suffix = ':'
        child_wrapper = TextWrapper(**vars(parent_wrapper))
        child_wrapper.initial_indent = parent_wrapper.subsequent_indent + child_wrapper.initial_indent

        k = re.escape(self.key) + self.prefix_capture.pattern.rstrip('^')
        if not self.case_sensitive:
            k = k.upper()

        child = self._child(k, _raw=True)
        ret = [parent_wrapper.fill(key + suffix)]
        ret.extend(child.description(child_wrapper))
        return ret
