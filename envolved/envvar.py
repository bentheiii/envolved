from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING, Any, Callable, Dict, Generic, Iterable, List, Mapping, MutableSet, NoReturn, Optional, TypeVar,
    Union, overload
)

from _weakrefset import WeakSet

from envolved.basevar import EnvVar, SchemaEnvVar, SingleEnvVar, missing
from envolved.utils import factory_type_hints

if TYPE_CHECKING:  # pragma: no cover
    from envolved.basevar import AsDefault, Missing

T = TypeVar('T')

K = TypeVar('K')
V = TypeVar('V')


@overload
def env_var(key: str, *, default: Union[T, Missing] = missing,
            description: Optional[str] = None, validators: Iterable[Callable[[T], T]] = (),
            case_sensitive: bool = False, strip_whitespaces: bool = True) -> AutoTypedEnvVar[T]:
    pass


@overload
def env_var(key: str, *, type: Callable[[str], T], default: Union[T, Missing] = missing,
            description: Optional[str] = None, validators: Iterable[Callable[[T], T]] = (),
            case_sensitive: bool = False, strip_whitespaces: bool = True) -> SingleEnvVar[T]:
    pass


@overload
def env_var(key: str, *, type: Callable[..., T], default: Union[T, Missing] = missing,
            args: Dict[str, Union[EnvVar[Any], AutoTypedEnvVar]],
            description: Optional[str] = None, validators: Iterable[Callable[[T], T]] = (),
            on_partial: Union[T, Missing, AsDefault] = missing) -> SchemaEnvVar[T]:
    pass


def env_var(key: str, *, type: Optional[Callable[..., T]] = None,  # type: ignore[misc]
            default: Union[T, Missing] = missing, description: Optional[str] = None,
            validators: Iterable[Callable[[T], T]] = (), **kwargs):
    args = kwargs.pop('args', None)
    if args:
        # schema var
        if type is None:
            raise TypeError('type cannot be omitted for schema env vars')
        on_partial = kwargs.pop('on_partial', missing)
        if kwargs:
            raise TypeError(f'Unexpected keyword arguments: {kwargs}')
        keys = {}
        factory_types: Optional[Mapping[str, Any]] = None
        for k, v in args.items():
            if isinstance(v, AutoTypedEnvVar):
                if factory_types is None:
                    factory_types = factory_type_hints(type)
                var_type = factory_types.get(k)
                if var_type is None:
                    raise TypeError(f'No type hint found for parameter {k!r} in factory {type!r}')
                v = v.with_type(var_type)
            keys[k] = v.with_prefix(key)
            assert keys[k] is not None
        ev: EnvVar = SchemaEnvVar(keys, default, type=type, on_partial=on_partial, description=description,
                                  validators=validators)
    else:
        # single var
        case_sensitive = kwargs.pop('case_sensitive', False)
        strip_whitespaces = kwargs.pop('strip_whitespaces', True)
        if kwargs:
            raise TypeError(f'Unexpected keyword arguments: {kwargs}')
        if type is None:
            return AutoTypedEnvVar(key, default, description, list(validators), case_sensitive, strip_whitespaces)
        ev = SingleEnvVar(key, default, type=type, case_sensitive=case_sensitive, strip_whitespaces=strip_whitespaces,
                          description=description, validators=validators)
    return register_env_var(ev)


@dataclass
class AutoTypedEnvVar(Generic[T]):
    key: str
    default: Union[T, Missing] = missing
    description: Optional[str] = None
    validators: List[Callable[[T], T]] = field(default_factory=list)
    case_sensitive: bool = False
    strip_whitespaces: bool = True

    def with_type(self, type: Callable[[str], T]) -> SingleEnvVar[T]:
        return env_var(self.key, default=self.default, type=type, description=self.description,
                       validators=self.validators, case_sensitive=self.case_sensitive,
                       strip_whitespaces=self.strip_whitespaces)

    def validator(self, func: Callable[[T], T]) -> Callable[[T], T]:
        self.validators.append(func)
        return func

    def with_prefix(self, prefix: str) -> AutoTypedEnvVar[T]:
        return AutoTypedEnvVar(prefix + self.key, self.default, description=self.description,
                               validators=list(self.validators), case_sensitive=self.case_sensitive,
                               strip_whitespaces=self.strip_whitespaces)

    if not TYPE_CHECKING:
        def get(self) -> NoReturn:
            raise AttributeError('this env-var is auto-typed and cannot be accessed directly (did you forget to '
                                 'specify a type?)')


top_level_env_vars: MutableSet[EnvVar] = WeakSet()

EV = TypeVar('EV', bound=EnvVar)


def register_env_var(ev: EV) -> EV:
    global top_level_env_vars

    top_level_env_vars.add(ev)
    top_level_env_vars -= frozenset(ev._get_children())
    return ev
