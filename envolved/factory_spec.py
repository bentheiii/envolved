from __future__ import annotations

from inspect import signature, Parameter
from itertools import chain
from typing import Dict, Any, get_type_hints, Sequence
from dataclasses import dataclass

missing = object()


@dataclass
class FactoryArgSpec:
    default: Any
    type: Any


@dataclass
class FactorySpec:
    positional: Sequence[FactoryArgSpec]
    keyword: Dict[str, FactoryArgSpec]

    def merge(self, other: FactorySpec) -> FactorySpec:
        return FactorySpec(
            positional=self.positional or other.positional,
            keyword={**other.keyword, **self.keyword},
        )


def factory_spec(factory) -> FactorySpec:
    if isinstance(factory, type):
        initial_mapping = {k: FactoryArgSpec(getattr(factory, k, missing), v) for k, v in get_type_hints(factory).items()}
        cls_spec = FactorySpec(positional=(), keyword=initial_mapping)
        init_spec = factory_spec(factory.__init__)
        new_spec = factory_spec(factory.__new__)
        # we arbitrarily decide that __init__ wins over __new__
        return init_spec.merge(new_spec).merge(cls_spec)

    type_hints = get_type_hints(factory)
    sign = signature(factory)
    pos = []
    kwargs = {}
    for param in sign.parameters.values():
        if param.kind not in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY, Parameter.POSITIONAL_ONLY):
            continue
        if param.default is not Parameter.empty:
            default = param.default
        else:
            default = missing

        ty = type_hints.get(param.name, missing)
        arg_spec = FactoryArgSpec(default, ty)
        if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.POSITIONAL_ONLY):
            pos.append(arg_spec)

        kwargs[param.name] = arg_spec
    return FactorySpec(pos, kwargs)



