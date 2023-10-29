from __future__ import annotations

from dataclasses import dataclass
from inspect import Parameter, signature
from itertools import zip_longest
from typing import Any, Callable, Dict, Optional, Sequence, Type, Union, get_type_hints

missing = object()


@dataclass
class FactoryArgSpec:
    default: Any
    type: Any

    @classmethod
    def merge(cls, a: Optional[FactoryArgSpec], b: Optional[FactoryArgSpec]) -> FactoryArgSpec:
        if not (a and b):
            ret = a or b
            assert ret is not None
            return ret
        return FactoryArgSpec(
            default=a.default if a.default is not missing else b.default,
            type=a.type if a.type is not missing else b.type,
        )


@dataclass
class FactorySpec:
    positional: Sequence[FactoryArgSpec]
    keyword: Dict[str, FactoryArgSpec]

    def merge(self, other: FactorySpec) -> FactorySpec:
        positionals = [FactoryArgSpec.merge(a, b) for a, b in zip_longest(self.positional, other.positional)]
        keyword = {
            k: FactoryArgSpec.merge(self.keyword.get(k), other.keyword.get(k))
            for k in {*self.keyword.keys(), *other.keyword.keys()}
        }
        return FactorySpec(
            positional=positionals,
            keyword=keyword,
        )


def factory_spec(factory: Union[Callable[..., Any], Type], skip_pos: int = 0) -> FactorySpec:
    if isinstance(factory, type):
        initial_mapping = {
            k: FactoryArgSpec(getattr(factory, k, missing), v) for k, v in get_type_hints(factory).items()
        }
        cls_spec = FactorySpec(positional=(), keyword=initial_mapping)
        init_spec = factory_spec(factory.__init__, skip_pos=1)  # type: ignore[misc]
        new_spec = factory_spec(factory.__new__, skip_pos=1)
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
    if skip_pos:
        del pos[:skip_pos]
    return FactorySpec(pos, kwargs)
