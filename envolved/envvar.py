from copy import deepcopy
from typing import Any, Optional, TypeVar, Generic, Mapping

import envolved.schema as schema_mod
from envolved.basevar import missing, SingleKeyEnvVar, EnvironmentVariable, BaseVar
from envolved.parsers import parser

T = TypeVar('T')


class EnvVar(BaseVar[T], Generic[T]):
    """
    An adaptive object capable of being used as an environment variable or to generate other environment variables.
    """
    def __init__(self, key: str = ..., default: Any = missing, *, type: Any = ..., **kwargs):
        """
        :param key: The name or suffix of the variable. Must be set or inferred before usage.
        :param default: The default value of the variable. By default will raise an error.
        :param type: The type, schema, or parser of the variable. Must be set or inferred before usage.
        :param kwargs: forwarded to appropriate BaseVar constructor.
        """
        self.key = key
        self.type = type
        self.default = default
        self.kwargs = kwargs

        self._manifest_var: Optional[EnvironmentVariable] = None

    def add_type(self, type):
        """
        Override a missing type of the EnvVar.
        :param type: the new type to set.
        :raises RuntimeError: if a non-default type was already set.
        """
        if self._manifest_var:
            raise ValueError('cannot mutate envvar after manifestation')
        if self.type is not ... and self.type != type:
            raise RuntimeError('type conflict')
        self.type = type

    def has_type(self):
        """
        :return: Whether the EnvVar has a type.
        """
        return self.type is not ...

    def add_name(self, name: str):
        """
        Override a missing name of the EnvVar. If the new name is all-upper, infers that the variable key is
         case-sensitive.
        :param name: the new name to set.

        .. note::
            If the name is already set, this method does nothing
        """
        if self._manifest_var:
            raise ValueError('cannot mutate envvar after manifestation')
        if self.key is not ...:
            return
        self.key = name
        if not name.isupper():
            self.kwargs.setdefault('case_sensitive', True)

    def _manifest(self):
        """
        Create an environment variable for the EnvVar to wrap
        """
        self._manifest_var = self()

    def get(self):
        if not self._manifest_var:
            self._manifest()
        return self._manifest_var.get()

    def validator(self, func):
        if not self._manifest_var:
            self._manifest()
        return self._manifest_var.validator(func)

    def __deepcopy__(self, m={}):
        ret = EnvVar(deepcopy(self.key, m), deepcopy(self.default, m), type=deepcopy(self.type, m))
        ret.kwargs = deepcopy(self.kwargs, m)
        return ret

    def __call__(self, prefix: str = ''):
        """
        Create a concrete environment variable object.
        :param prefix: An optional prefix to apply to the key of the variable.
        :return: The BaseVar created.
        """
        if self._manifest_var:
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
