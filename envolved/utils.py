from __future__ import annotations

from inspect import signature, Parameter
from typing import Dict, Any, Callable, get_type_hints, Set


class FactoryKeywordParameters(Dict[str, Any]):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.required: Set[str] = set()
        self.variadic_annotation = ...

    def union(self, other: FactoryKeywordParameters):
        ret = type(self)(self)
        ret.required = set(self.required)
        ret.variadic_annotation = self.variadic_annotation

        for k, v in other.items():
            # first one always wins out
            if k in ret:
                continue
            ret[k] = v
            if k in other.required:
                ret.required.add(k)
        if ret.variadic_annotation is ...:
            ret.variadic_annotation = other.variadic_annotation
        return ret


def factory_type_hints(factory: Callable) -> FactoryKeywordParameters:
    """
    Generate type hints for a factory or class. Combining its __init__ and __new__ keyword parameters.
    :param factory: The factory function or type.
    :return: A combined parameter annotation dict for `factory`.
    """
    if isinstance(factory, type):
        init_hints = factory_type_hints(factory.__init__)
        new_hints = factory_type_hints(factory.__new__)
        # we arbitrarily decide that __init__ wins over __new__
        return init_hints.union(new_hints)

    hints = get_type_hints(factory)
    sign = signature(factory)
    ret = FactoryKeywordParameters()

    for param in sign.parameters.values():
        if param.kind not in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY, Parameter.VAR_KEYWORD) \
                or param.name not in hints:
            continue

        hint = hints[param.name]
        if param.kind == Parameter.VAR_KEYWORD:
            ret.variadic_annotation = hint
            continue

        if param.default == Parameter.empty:
            ret.required.add(param.name)
        ret[param.name] = hint

    return ret
