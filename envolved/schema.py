from __future__ import annotations

import sys
from string import whitespace
from textwrap import TextWrapper
from types import SimpleNamespace
from typing import Dict, TypeVar, Generic, Any, Mapping, Callable, Iterable, Tuple, Optional, List, TYPE_CHECKING

from envolved.exceptions import MissingEnvError
from envolved.basevar import EnvironmentVariable, validates
from envolved.utils import factory_type_hints
if TYPE_CHECKING:
    from envolved.envvar import EnvVar

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
        v.owner = ret
        ret[k] = v
    if name:
        ret.__name__ = name
    return ret


T = TypeVar('T')


class PartialSchemaError(Exception):
    pass


class SchemaVar(EnvironmentVariable[T], Generic[T]):
    def __init__(self, key: str, default: T, schema: SchemaMap, *, case_sensitive: bool = ...,
                 raise_for_partial: bool = True, description: Optional[str] = None):
        """
        :param key: The prefix for all child env vars
        :param default: The default value if child env vars are missing
        :param schema: The schema mapping to use
        :param case_sensitive: Whether child env vars should be case sensitive, default is per-child.
        :param raise_for_partial: If set to true (the default), setting some but not all of the child env vars will
         cause an error to be raised, regardless of whether there is a default value.
        """
        super().__init__(default)
        self.key = key
        self.case_sensitive = case_sensitive
        self.inners: Mapping[str, EnvVar] = {k: self._make_inner(v) for k, v in schema.items()}
        self.schema = schema
        self.raise_for_partial = raise_for_partial

        self._description = description

    def _make_inner(self, prototype: EnvVar) -> EnvVar:
        kwargs = {}
        if self.case_sensitive is not ...:
            kwargs['case_sensitive'] = self.case_sensitive

        ret = prototype.child(prefix=self.key, **kwargs)
        ret.owner = self
        return ret

    def _get(self) -> T:
        args = {}
        presence = False
        missing = None
        for k, v in self.inners.items():
            try:
                result = v.get_()
            except MissingEnvError as e:
                if not self.raise_for_partial:
                    raise

                if presence:
                    raise PartialSchemaError(e)
                if not missing:
                    missing = e
            else:
                if not presence and result.is_presence:
                    if self.raise_for_partial and missing:
                        raise PartialSchemaError(missing)
                    presence = True
                args[k] = result.value

        if missing:
            assert not presence
            raise missing

        return self.schema._factory(**args)

    def get_(self):
        try:
            return super().get_()
        except PartialSchemaError as ex:
            raise ex.args[0]

    def description(self, parent_wrapper: TextWrapper) -> List[str]:
        key = self.key.strip(whitespace+'_')
        if self.case_sensitive is not False:
            key = key.upper()
        if self._description:
            desc = ' '.join(self._description.strip().split())
            suffix = ': '+desc
        else:
            suffix = ':'
        child_wrapper = TextWrapper(**vars(parent_wrapper))
        child_wrapper.initial_indent = parent_wrapper.subsequent_indent + child_wrapper.initial_indent
        headings = []
        for v in self.inners.values():
            headings.append(v._manifest().description(child_wrapper))
        ret = [parent_wrapper.fill(key+suffix)]
        ret.extend(line for lines in sorted(headings) for line in lines)
        return ret
