import sys
from types import SimpleNamespace
from typing import Dict, TypeVar, Generic, Any, Mapping, Callable, Iterable, Tuple, Optional

from envolved.basevar import EnvironmentVariable, validates
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

    def __new__(mcs, name, bases, ns, *, type: Callable = SimpleNamespace):
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
        mod_globs = sys.modules[ns['__module__']].__dict__
        return _schema(annotations, type, mod_globs,
                       ((k, v) for (k, v) in ns.items() if k not in ns_ignore),
                       name)

    def __call__(cls, factory=SimpleNamespace, m: Mapping[str, EnvVar] = None, **kwargs: EnvVar):
        """
        create a schema by calling Schema
        :param factory: The type or factory to apply.
        :param m: The mapping of string keys to environment variables
        :param kwargs: additional environment variables.
        """
        # Schema.__call__
        if m is None \
                and not isinstance(factory, Callable) \
                and isinstance(factory, Mapping):
            m = factory
            factory = SimpleNamespace

        if m:
            kwargs.update(m)

        return _schema({}, factory, None, kwargs.items(), None)


class Schema(metaclass=SchemaMeta, type=_root):
    pass


class SchemaMap(Dict[str, Any]):
    def __init__(self, factory):
        super().__init__()
        self._factory = factory

    def __getattr__(self, item):
        if item in self:
            return self.get(item)
        raise AttributeError(item)


def _schema(annotations, factory,
            str_resolution_globs: Optional[dict], items: Iterable[Tuple[str, EnvVar]],
            name):
    factory_annotation = factory_type_hints(factory)
    ret = SchemaMap(factory)
    seen_vars = set()
    for k, v in items:
        if validates(v) in seen_vars:
            continue
        if not isinstance(v, EnvVar):
            raise TypeError(f'attribute {k!r} of schema class must be an EnvVar or validator for an envvar')
        if v in seen_vars:
            raise RuntimeError(f'attribute {k} is an envvar that has already been used')
        seen_vars.add(v)
        type_hint = annotations.get(k)
        if type_hint:
            if isinstance(type_hint, str):
                type_hint = eval(type_hint, str_resolution_globs)
            v.add_type(type_hint)
        if not v.has_type():
            factory_annotated_type = factory_annotation.get(k, factory_annotation.variadic_annotation)
            if factory_annotated_type is not ...:
                v.add_type(factory_annotated_type)
        v.add_name(k)
        ret[k] = v
    if name:
        ret.__name__ = name
    return ret


T = TypeVar('T')


class SchemaVar(EnvironmentVariable[T], Generic[T]):
    def __init__(self, key: str, default: T, schema: SchemaMap, *, case_sensitive=...):
        super().__init__(default)
        self.key = key
        self.case_sensitive = case_sensitive
        self.inners = {k: self._make_inner(v) for k, v in schema.items()}
        self.schema = schema

    def _make_inner(self, prototype: EnvVar) -> EnvironmentVariable:
        kwargs = {}
        if self.case_sensitive is not ...:
            kwargs['case_sensitive'] = self.case_sensitive

        return prototype.child(prefix=self.key, **kwargs)

    def _get(self) -> T:
        args = {
            k: v.get() for (k, v) in self.inners.items()
        }
        return self.schema._factory(**args)
