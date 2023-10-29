from __future__ import annotations

from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableSet,
    Optional,
    Sequence,
    TypeVar,
    Union,
    overload,
)

from _weakrefset import WeakSet

from envolved.basevar import AsDefault, Discard, EnvVar, Missing, SchemaEnvVar, SingleEnvVar, missing
from envolved.factory_spec import FactorySpec, factory_spec
from envolved.infer_env_var import AutoTypedEnvVar, InferEnvVar, inferred_env_var
from envolved.parsers import ParserInput

T = TypeVar("T")

K = TypeVar("K")
V = TypeVar("V")


@overload
def env_var(
    key: str,
    *,
    default: Union[T, Missing, AsDefault, Discard] = missing,
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    case_sensitive: bool = False,
    strip_whitespaces: bool = True,
) -> AutoTypedEnvVar[T]:
    pass


@overload
def env_var(
    key: str,
    *,
    type: ParserInput[T],
    default: Union[T, Missing, Discard] = missing,
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    case_sensitive: bool = False,
    strip_whitespaces: bool = True,
) -> SingleEnvVar[T]:
    pass


@overload
def env_var(
    key: str,
    *,
    type: Callable[..., T],
    default: Union[T, Missing, Discard] = missing,
    pos_args: Sequence[Union[EnvVar[Any], InferEnvVar[T]]],
    args: Dict[str, Union[EnvVar[Any], InferEnvVar[T]]] = {},  # noqa: B006
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    on_partial: Union[T, Missing, AsDefault, Discard] = missing,
) -> SchemaEnvVar[T]:
    pass


@overload
def env_var(
    key: str,
    *,
    type: Callable[..., T],
    default: Union[T, Missing, Discard] = missing,
    pos_args: Sequence[Union[EnvVar[Any], InferEnvVar[T]]] = (),
    args: Dict[str, Union[EnvVar[Any], InferEnvVar[T]]],
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    on_partial: Union[T, Missing, AsDefault, Discard] = missing,
) -> SchemaEnvVar[T]:
    pass


def env_var(  # type: ignore[misc]
    key: str,
    *,
    type: Optional[ParserInput[T]] = None,
    default: Union[T, Missing, AsDefault, Discard] = missing,
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    **kwargs: Any,
):
    pos_args = kwargs.pop("pos_args", ())
    args: Mapping[str, Union[InferEnvVar[T], EnvVar[T]]] = kwargs.pop("args", {})
    if args or pos_args:
        # schema var
        if type is None:
            raise TypeError("type cannot be omitted for schema env vars")
        on_partial = kwargs.pop("on_partial", missing)
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {kwargs}")
        pos: List[EnvVar] = []
        keys: Dict[str, EnvVar] = {}
        factory_specs: Optional[FactorySpec] = None
        for p in pos_args:
            if isinstance(p, InferEnvVar):
                if factory_specs is None:
                    factory_specs = factory_spec(type)
                idx = len(pos)
                if idx >= len(factory_specs.positional):
                    raise TypeError(f"Cannot infer for positional parameter {len(pos)}")
                var_spec = factory_specs.positional[idx]
                arg: EnvVar[Any] = p.with_spec(idx, var_spec)
            else:
                arg = p
            pos.append(arg.with_prefix(key))
        for k, v in args.items():
            if isinstance(v, InferEnvVar):
                if factory_specs is None:
                    factory_specs = factory_spec(type)
                kw_var_spec = factory_specs.keyword.get(k)
                if kw_var_spec is None:
                    raise TypeError(f"No type hint found for parameter {k!r} in factory {type!r}")
                arg = v.with_spec(k, kw_var_spec)
            else:
                arg = v
            keys[k] = arg.with_prefix(key)
        ev: EnvVar = SchemaEnvVar(
            keys,
            default,
            type=type,
            on_partial=on_partial,
            description=description,
            validators=validators,
            pos_args=tuple(pos),
        )
    else:
        # single var
        case_sensitive = kwargs.pop("case_sensitive", False)
        strip_whitespaces = kwargs.pop("strip_whitespaces", True)
        if kwargs:
            raise TypeError(f"Unexpected keyword arguments: {kwargs}")
        if type is None:
            return inferred_env_var(
                key,
                default=default,
                description=description,
                validators=validators,
                case_sensitive=case_sensitive,
                strip_whitespaces=strip_whitespaces,
            )
        ev = SingleEnvVar(
            key,
            default,
            type=type,
            case_sensitive=case_sensitive,
            strip_whitespaces=strip_whitespaces,
            description=description,
            validators=validators,
        )
    return register_env_var(ev)


top_level_env_vars: MutableSet[EnvVar] = WeakSet()

EV = TypeVar("EV", bound=EnvVar)


def register_env_var(ev: EV) -> EV:
    global top_level_env_vars  # noqa: PLW0603

    top_level_env_vars.add(ev)
    top_level_env_vars -= frozenset(ev._get_children())  # noqa: SLF001
    return ev
