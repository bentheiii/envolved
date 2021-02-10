from functools import partial
from textwrap import TextWrapper
from typing import Any, Optional, TypeVar, Generic, List, Set, MutableSet, Pattern, Mapping, Tuple
from weakref import WeakSet

from envolved.basevar import missing, SingleKeyEnvVar, EnvironmentVariable, BaseVar, ValidatorCallback
from envolved.parsers import parser
from envolved.prefix import PrefixVar
from envolved.schema import SchemaMap, SchemaVar

T = TypeVar('T')


class EnvVar(BaseVar[T], Generic[T]):
    """
    An adaptive object capable of being used as an environment variable or to generate other environment variables.
    """

    def __init__(self, key: str = ..., default: Any = missing, *, type: Any = ...,
                 prefix_capture: Optional[Pattern] = None, **kwargs):
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
        self.owner = None
        self.prefix_capture = prefix_capture

        self._manifest_var: Optional[EnvironmentVariable] = None
        self._pending_validators: Optional[List[Tuple[ValidatorCallback[T], Mapping[str, Any]]]] = []
        self._children: Optional[Set[EnvVar]] = set()

        childless_env_vars.add(self)

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

    def _inner_var(self) -> EnvironmentVariable:
        if not self._manifest_var:
            var = self._manifest()
            self._manifest_var = var
            self._pending_validators = None
            self._children = None
        return self._manifest_var

    def _manifest(self):
        """
        Create an environment variable for the EnvVar to wrap
        """
        if self.key is ...:
            raise RuntimeError('EnvVar must have a name or a key')

        if self.prefix_capture:
            if isinstance(self.type, EnvVar):
                inner_var = self.type.child('')
            else:
                inner_var = EnvVar('', self.default, type=self.type,
                                   case_sensitive=self.kwargs.get('case_sensitive', False))
            var = PrefixVar(self.key, self.prefix_capture, inner_var, **self.kwargs)
        elif isinstance(self.type, SchemaMap):
            if self.type is ...:
                raise RuntimeError('EnvVar must have a type')
            var = SchemaVar(self.key, self.default, self.type, **self.kwargs)
        else:
            # single key env var
            if self.type is ...:
                raise RuntimeError('EnvVar must have a type')
            plaintext_converter = parser(self.type)
            var = SingleKeyEnvVar(self.key, self.default, type=plaintext_converter, **self.kwargs)
        for validator, kw in self._pending_validators:
            var.validator(validator, **kw)

        return var

    def get_(self):
        return self._inner_var().get_()

    def validator(self, func=None, **kwargs):
        if func is None:
            return partial(self.validator, **kwargs)

        if self._manifest_var:
            return self._manifest_var.validator(func, **kwargs)
        elif self._children:
            raise RuntimeError('cannot change an EnvVar in use')
        self._pending_validators.append((func, kwargs))
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
            new_key = prefix + self.key

        kw = {
            'key': new_key,
            'default': self.default,
            'type': self.type,
            'prefix_capture': self.prefix_capture
        }
        kw.update(self.kwargs)
        kw.update(kwargs)

        ret = type(self)(**kw)
        ret._pending_validators = list(self._pending_validators)
        self._children.add(ret)
        childless_env_vars.discard(self)
        return ret

    def description(self, parent_wrapper: TextWrapper) -> List[str]:
        if self._manifest_var:
            return self._manifest_var.description(parent_wrapper)
        return self._manifest().description(parent_wrapper)


childless_env_vars: MutableSet[EnvVar] = WeakSet()
