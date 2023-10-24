from __future__ import annotations

from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING, Any, Callable, Dict, Generic, Iterable, List, Mapping, MutableSet, NoReturn, Optional, TypeVar,
    Union, overload, Sequence
)

from _weakrefset import WeakSet

from envolved.basevar import EnvVar, SchemaEnvVar, SingleEnvVar, missing
from envolved.factory_spec import FactorySpec
from envolved.infer_env_var import AutoTypedEnvVar, InferEnvVar, infer_type, inferred_env_var
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
            pos_args: Sequence[Union[EnvVar[Any], InferEnvVar[T]]] = (), args: Dict[str, Union[EnvVar[Any], InferEnvVar[T]]] = {},
            description: Optional[str] = None, validators: Iterable[Callable[[T], T]] = (),
            on_partial: Union[T, Missing, AsDefault] = missing) -> SchemaEnvVar[T]:
    pass


def env_var(key: str, *, type: Optional[Callable[..., T]] = None,  # type: ignore[misc]
            default: Union[T, Missing] = missing, description: Optional[str] = None,
            validators: Iterable[Callable[[T], T]] = (), **kwargs):
    pos_args = kwargs.pop('pos_args', ())
    args = kwargs.pop('args', {})
    if args or pos_args:
        # schema var
        if type is None:
            raise TypeError('type cannot be omitted for schema env vars')
        on_partial = kwargs.pop('on_partial', missing)
        if kwargs:
            raise TypeError(f'Unexpected keyword arguments: {kwargs}')
        keys = {}
        factory_spec: Optional[FactorySpec] = None
        for k, v in args.items():
            if isinstance(v, InferEnvVar):
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
            return inferred_env_var(key, default=default, description=description, validators=validators,
                                    case_sensitive=case_sensitive, strip_whitespaces=strip_whitespaces)
        ev = SingleEnvVar(key, default, type=type, case_sensitive=case_sensitive, strip_whitespaces=strip_whitespaces,
                          description=description, validators=validators)
    return register_env_var(ev)


top_level_env_vars: MutableSet[EnvVar] = WeakSet()

EV = TypeVar('EV', bound=EnvVar)


def register_env_var(ev: EV) -> EV:
    global top_level_env_vars

    top_level_env_vars.add(ev)
    top_level_env_vars -= frozenset(ev._get_children())
    return ev
