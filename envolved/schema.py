import sys
from copy import deepcopy
from inspect import signature, Parameter
from typing import Dict, TypeVar, Generic, Any, Mapping, Callable, get_type_hints

from envolved.basevar import BaseVar
from envolved.envvar import EnvVar

ns_ignore = frozenset((
    '__module__', '__qualname__', '__annotations__'
))

_root = object()


def factory_type_hints(factory):
    if isinstance(factory, type):
        ret = {}
        new_sig = signature(factory.__new__)
        new_ann = get_type_hints(factory.__new__)
        init_sig = signature(factory.__init__)
        init_ann = get_type_hints(factory.__init__)
        for k in new_sig.parameters.keys() | init_sig.parameters.keys():
            init_param = init_sig.parameters.get(k)
            init_type = init_param \
                        and init_param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY) \
                        and init_ann.get(k)

            # we arbitrarily decide that __init__ wins out
            if init_type:
                ret[k] = init_type

            new_param = new_sig.parameters.get(k)
            new_type = new_param \
                       and new_param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY) \
                       and new_ann.get(k)

            if new_type:
                ret[k] = new_type
        return ret
    return get_type_hints(factory)


class SchemaMeta(type):
    def __new__(mcs, name, bases, ns, *, type: Callable):
        if type is _root:
            return super().__new__(mcs, name, bases, ns)
        annotations = ns.get('__annotations__') or {}
        factory_annotation = factory_type_hints(type)
        ret = SchemaMap(type)
        mod_globs = sys.modules[ns['__module__']].__dict__
        for k, v in ns.items():
            if k in ns_ignore:
                continue
            if not isinstance(v, EnvVar):
                raise TypeError(f'attribute {k!r} of schema class must be an EnvVar')
            type_hint = annotations.get(k)
            if type_hint:
                if isinstance(type_hint, str):
                    type_hint = eval(type_hint, mod_globs)
                v.add_type(type_hint)
            if not v.has_type():
                factory_annotated_type = factory_annotation.get(k)
                if factory_annotated_type:
                    v.add_type(factory_annotated_type)
            v.add_name(k)
            ret[k] = v
        return ret

    def __call__(cls, factory, m: Mapping[str, EnvVar] = None, **kwargs: EnvVar):
        # Schema.__call__
        ret = SchemaMap(factory)
        if m:
            kwargs.update(m)
        factory_annotation = factory_type_hints(factory)
        for k, v in kwargs.items():
            if not isinstance(v, EnvVar):
                raise TypeError(f'attribute {k!r} of schema class must be an EnvVar')
            v.add_name(k)
            if not v.has_type():
                factory_annotated_type = factory_annotation.get(k)
                if factory_annotated_type:
                    v.add_type(factory_annotated_type)
            ret[k] = v
        return ret


class Schema(metaclass=SchemaMeta, type=_root):
    pass


class SchemaMap(Dict[str, Any]):
    def __init__(self, factory):
        super().__init__()
        self.factory = factory


K = TypeVar('K')
V = TypeVar('V')


class MapVar(BaseVar[Dict[K, V]], Generic[K, V]):
    def __init__(self, key: str, default: Dict[K, V], schema: Mapping[K, EnvVar], *, case_sensitive=...):
        super().__init__(default)
        self.key = key
        self.case_sensitive = case_sensitive
        self.inners = {k: self._make_inner(v) for k, v in schema.items()}

    def _make_inner(self, prototype: EnvVar) -> BaseVar:
        if self.case_sensitive is not ...:
            prototype = deepcopy(prototype)
            prototype.kwargs['case_sensitive'] = self.case_sensitive

        return prototype(prefix=self.key)

    def _get(self):
        return {
            k: v.get() for (k, v) in self.inners.items()
        }


T = TypeVar('T')


class SchemaVar(MapVar[str, Any], BaseVar[T], Generic[T]):
    def __init__(self, key: str, default: T, schema: SchemaMap, *, case_sensitive=...):
        super().__init__(key, default, schema, case_sensitive=case_sensitive)

        self.schema = schema

    def _get(self) -> T:
        args = super()._get()
        return self.schema.factory(**args)
