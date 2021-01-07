from typing import Any, Optional, TypeVar, Generic, List, Set

import envolved.schema as schema_mod
from envolved.basevar import missing, SingleKeyEnvVar, EnvironmentVariable, BaseVar, ValidatorCallback
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
        self._pending_validators: Optional[List[ValidatorCallback[T]]] = []
        self._children: Optional[Set[EnvVar]] = set()

    def add_type(self, type):
        """
        Override a missing type of the EnvVar.
        :param type: the new type to set.
        :raises RuntimeError: if a non-default type was already set.
        """
        if self._children or self._manifest_var is not None:
            raise RuntimeError('cannot change an EnvVar in use')
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
        if self._children or self._manifest_var is not None:
            raise RuntimeError('cannot change an EnvVar in use')
        if self.key is not ...:
            return
        self.key = name
        if not name.isupper():
            self.kwargs.setdefault('case_sensitive', True)

    def _manifest(self):
        """
        Create an environment variable for the EnvVar to wrap
        """
        if self.key is ...:
            raise RuntimeError('EnvVar must have a name or a key')
        if self.type is ...:
            raise RuntimeError('EnvVar must have a type')

        if isinstance(self.type, schema_mod.SchemaMap):
            var = schema_mod.SchemaVar(self.key, self.default, self.type, **self.kwargs)
        else:
            plaintext_converter = parser(self.type)
            var = SingleKeyEnvVar(self.key, self.default, type=plaintext_converter, **self.kwargs)
        for validator in self._pending_validators:
            var.validator(validator)

        self._manifest_var = var
        self._pending_validators = None
        self._children = None

    def get(self):
        if not self._manifest_var:
            self._manifest()
        return self._manifest_var.get()

    def validator(self, func):
        if self._manifest_var:
            return self._manifest_var.validator(func)
        elif self._children:
            raise RuntimeError('cannot change an EnvVar in use')
        self._pending_validators.append(func)
        return super().validator(func)

    def child(self, prefix: str = ..., **kwargs):
        """
        Create a concrete environment variable object.
        :param prefix: An optional prefix to apply to the key of the variable.
        :return: The BaseVar created.
        """
        if self._manifest_var:
            raise RuntimeError('cannot create child of manifest EnvVar')

        if self.key is ...:
            new_key = prefix
        elif prefix is ...:
            new_key = self.key
        else:
            new_key = prefix+self.key

        kw = {
            'key': new_key,
            'default': self.default,
            'type': self.type,
        }
        kw.update(self.kwargs)
        kw.update(kwargs)

        ret = type(self)(**kw)
        ret._pending_validators = list(self._pending_validators)
        self._children.add(ret)
        return ret
