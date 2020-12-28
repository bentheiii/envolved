import sys
from copy import deepcopy
from typing import Dict, TypeVar, Generic, Any, Mapping, Callable

from envolved.basevar import EnvironmentVariable
from envolved.envvar import EnvVar
from envolved.utils import factory_type_hints

ns_ignore = frozenset((
    '__module__', '__qualname__', '__annotations__'
))

_root = object()


class SchemaMeta(type):
    """
    A metaclass to create a schema.
    """
    def __new__(mcs, name, bases, ns, *, type: Callable):
        """
        :param name: Same as  in type.__new__.
        :param bases: Same as  in type.__new__.
        :param ns: Same as  in type.__new__.
        :param type: The type or factory to apply.
        """
        if type is _root:
            return super().__new__(mcs, name, bases, ns)
        if bases != (Schema,):
            raise TypeError('Schema class must inherit only from Schema')
        annotations = ns.get('__annotations__') or {}
        factory_annotation = factory_type_hints(type)
        ret = SchemaMap(type)
        mod_globs = sys.modules[ns['__module__']].__dict__
        for k, v in ns.items():
            if k in ns_ignore:
                continue
            if not isinstance(v, EnvVar):
                raise TypeError(f'attribute {k!r} of schema class must be an EnvVar')
            # we always use a clone of the envar, to allow envvar reuse
            v = deepcopy(v)
            type_hint = annotations.get(k)
            if type_hint:
                if isinstance(type_hint, str):
                    type_hint = eval(type_hint, mod_globs)
                v.add_type(type_hint)
            if not v.has_type():
                factory_annotated_type = factory_annotation.get(k, factory_annotation.variadic_annotation)
                if factory_annotated_type is not ...:
                    v.add_type(factory_annotated_type)
            v.add_name(k)
            ret[k] = v
        ret.__name__ = name
        return ret

    def __call__(cls, factory, m: Mapping[str, EnvVar] = None, **kwargs: EnvVar):
        """
        create a schema by calling Schema
        :param factory: The type or factory to apply.
        :param m: The mapping of string keys to environment variables
        :param kwargs: additional environment variables.
        """
        # Schema.__call__
        factory_annotation = factory_type_hints(factory)
        ret = SchemaMap(factory)
        if m:
            kwargs.update(m)
        for k, v in kwargs.items():
            if not isinstance(v, EnvVar):
                raise TypeError(f'attribute {k!r} of schema must be an EnvVar')
            v.add_name(k)
            if not v.has_type():
                factory_annotated_type = factory_annotation.get(k, factory_annotation.variadic_annotation)
                if factory_annotated_type is not ...:
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


class MapVar(EnvironmentVariable[Dict[K, V]], Generic[K, V]):
    def __init__(self, key: str, default: Dict[K, V], schema: Mapping[K, EnvVar], *, case_sensitive=...):
        super().__init__(default)
        self.key = key
        self.case_sensitive = case_sensitive
        self.inners = {k: self._make_inner(v) for k, v in schema.items()}

    def _make_inner(self, prototype: EnvVar) -> EnvironmentVariable:
        if self.case_sensitive is not ...:
            prototype = deepcopy(prototype)
            prototype.kwargs['case_sensitive'] = self.case_sensitive

        return prototype(prefix=self.key)

    def _get(self):
        return {
            k: v.get() for (k, v) in self.inners.items()
        }


T = TypeVar('T')


class SchemaVar(MapVar[str, Any], EnvironmentVariable[T], Generic[T]):
    def __init__(self, key: str, default: T, schema: SchemaMap, *, case_sensitive=...):
        super().__init__(key, default, schema, case_sensitive=case_sensitive)

        self.schema = schema

    def _get(self) -> T:
        args = super()._get()
        return self.schema.factory(**args)
