from copy import deepcopy
from typing import Any, Optional, TypeVar, Generic, Mapping

import envolved.schema as schema_mod
from envolved.basevar import _missing, SingleKeyEnvVar, BaseVar, VarProtocol
from envolved.parsers import parser

T = TypeVar('T')


class EnvVar(VarProtocol[T], Generic[T]):
    def __init__(self, key: str = ..., default: Any = _missing, *, type: Any = ..., **kwargs):
        self.key = key
        self.type = type
        self.default = default
        self.kwargs = kwargs

        self._manifest: Optional[BaseVar] = None

    def add_type(self, type):
        if self._manifest:
            raise ValueError('cannot mutate envvar after manifestation')
        if self.type is not ... and self.type != type:
            raise RuntimeError('type conflict')
        self.type = type

    def has_type(self):
        return self._manifest or (self.type is not ...)

    def add_name(self, name: str):
        if self._manifest:
            raise ValueError('cannot mutate envvar after manifestation')
        if self.key is not ...:
            return
        self.key = name
        if not name.isupper():
            self.kwargs.setdefault('case_sensitive', True)

    def manifest(self):
        self._manifest = self()
        return self._manifest

    def get(self):
        if not self._manifest:
            self.manifest()
        return self._manifest.get()

    def validator(self, func):
        if not self._manifest:
            self.manifest()
        return self._manifest.validator(func)

    def __deepcopy__(self, m={}):
        ret = EnvVar(deepcopy(self.key, m), deepcopy(self.default, m), type=deepcopy(self.type, m))
        ret.kwargs = deepcopy(self.kwargs, m)
        return ret

    def __call__(self, prefix: str = ''):
        if self._manifest:
            raise ValueError('cannot call envvar after manifestation')

        if self.key is ...:
            raise RuntimeError('EnvVar must have a name or a key')
        if self.type is ...:
            raise RuntimeError('EnvVar must have a type')

        key = prefix + self.key

        if isinstance(self.type, schema_mod.SchemaMap):
            return schema_mod.SchemaVar(key, self.default, self.type, **self.kwargs)
        if isinstance(self.type, Mapping):
            return schema_mod.MapVar(key, self.default, self.type, **self.kwargs)

        plaintext_converter = parser(self.type)
        return SingleKeyEnvVar(key, self.default, type=plaintext_converter, **self.kwargs)
