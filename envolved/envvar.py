from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    MutableSet,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
    overload,
)

from _weakrefset import WeakSet

from envolved.envparser import CaseInsensitiveAmbiguityError, env_parser
from envolved.exceptions import MissingEnvError, SkipDefault
from envolved.factory_spec import FactoryArgSpec, FactorySpec, factory_spec, missing as factory_spec_missing
from envolved.parsers import Parser, ParserInput, parser

T = TypeVar("T")
Self = TypeVar("Self")

K = TypeVar("K")
V = TypeVar("V")


class Missing(Enum):
    missing = auto()


missing = Missing.missing


class AsDefault(Enum):
    as_default = auto()


as_default = AsDefault.as_default


class NoPatch(Enum):
    no_patch = auto()


no_patch = NoPatch.no_patch


class Discard(Enum):
    discard = auto()


discard = Discard.discard

Description = Union[str, Sequence[str]]


@dataclass
class Factory(Generic[T]):
    callback: Callable[[], T]


@dataclass
class _EnvVarResult(Generic[T]):
    value: Union[T, Discard]
    exists: bool


def unwrap_validator(func: Callable[[T], T]) -> Callable[[T], T]:
    if isinstance(func, staticmethod):
        func = func.__func__
    return func


class EnvVar(Generic[T], ABC):
    def __init__(
        self,
        default: Union[T, Factory[T], Missing, Discard],
        description: Optional[Description],
        validators: Iterable[Callable[[T], T]] = (),
    ):
        self._validators: List[Callable[[T], T]] = [unwrap_validator(v) for v in validators]
        self.default = default
        self.description = description
        self.monkeypatch: Union[T, Missing, Discard, NoPatch] = no_patch

    def get(self, **kwargs: Any) -> T:
        if self.monkeypatch is not no_patch:
            if self.monkeypatch is missing:
                key = getattr(self, "key", self)
                raise MissingEnvError(key)
            return self.monkeypatch  # type: ignore[return-value]
        return self._get_validated(**kwargs).value  # type: ignore[return-value]

    def validator(self, validator: Callable[[T], T]) -> EnvVar[T]:
        self._validators.append(validator)
        return self

    def _get_validated(self, **kwargs: Any) -> _EnvVarResult[T]:
        try:
            value = self._get(**kwargs)
        except SkipDefault as sd:
            raise sd.args[0] from None
        except MissingEnvError as mee:
            if self.default is missing:
                raise mee

            default: Union[T, Discard]
            if isinstance(self.default, Factory):
                default = self.default.callback()
            else:
                default = self.default

            return _EnvVarResult(default, exists=False)
        for validator in self._validators:
            value = validator(value)
        return _EnvVarResult(value, exists=True)

    @abstractmethod
    def _get(self, **kwargs: Any) -> T:
        pass

    @abstractmethod
    def with_prefix(self: Self, prefix: str) -> Self:
        pass

    @abstractmethod
    def _get_children(self) -> Iterable[EnvVar]:
        pass

    def _get_descendants(self) -> Iterable[EnvVar]:
        for child in self._get_children():
            yield child
            yield from child._get_descendants()

    @contextmanager
    def patch(self, value: Union[T, Missing, Discard]) -> Iterator[None]:
        previous = self.monkeypatch
        self.monkeypatch = value
        try:
            yield
        finally:
            self.monkeypatch = previous


class SingleEnvVar(EnvVar[T]):
    def __init__(
        self,
        key: str,
        default: Union[T, Missing, Discard, Factory[T]] = missing,
        *,
        type: Union[Type[T], Parser[T]],
        description: Optional[Description] = None,
        case_sensitive: bool = False,
        strip_whitespaces: bool = True,
        validators: Iterable[Callable[[T], T]] = (),
    ):
        super().__init__(default, description, validators)
        self._key = key
        self._type = parser(type)
        self.case_sensitive = case_sensitive
        self.strip_whitespaces = strip_whitespaces

    @property
    def key(self) -> str:
        return self._key

    @property
    def type(self) -> Parser[T]:
        return self._type

    def _get(self, **kwargs: Any) -> T:
        try:
            raw_value = env_parser.get(self.case_sensitive, self._key)
        except KeyError as err:
            raise MissingEnvError(self._key) from err
        except CaseInsensitiveAmbiguityError as cia:
            raise RuntimeError(f"environment error: cannot choose between environment variables {cia.args[0]}") from cia

        if self.strip_whitespaces:
            raw_value = raw_value.strip()
        return self.type(raw_value, **kwargs)

    def with_prefix(self, prefix: str) -> SingleEnvVar[T]:
        return register_env_var(
            SingleEnvVar(
                prefix + self._key,
                self.default,
                type=self.type,
                description=self.description,
                case_sensitive=self.case_sensitive,
                strip_whitespaces=self.strip_whitespaces,
                validators=self._validators,
            )
        )

    def _get_children(self) -> Iterable[EnvVar[Any]]:
        return ()


class SchemaEnvVar(EnvVar[T]):
    def __init__(
        self,
        keys: Mapping[str, EnvVar[Any]],
        default: Union[T, Missing, Discard, Factory[T]] = missing,
        *,
        type: Callable[..., T],
        description: Optional[Description] = None,
        on_partial: Union[T, Missing, AsDefault, Discard, Factory[T]] = missing,
        validators: Iterable[Callable[[T], T]] = (),
        pos_args: Sequence[EnvVar[Any]] = (),
    ):
        super().__init__(default, description, validators)
        self._args = keys
        self._pos_args = pos_args
        self._type = type
        self.on_partial = on_partial

    @property
    def type(self) -> Callable[..., T]:
        return self._type

    @property
    def args(self) -> Mapping[str, EnvVar[Any]]:
        return MappingProxyType(self._args)

    @property
    def pos_args(self) -> Sequence[EnvVar[Any]]:
        return tuple(self._pos_args)

    @property
    def on_partial(self) -> Union[T, Missing, AsDefault, Discard, Factory[T]]:
        return self._on_partial

    @on_partial.setter
    def on_partial(self, value: Union[T, Missing, AsDefault, Discard, Factory[T]]):
        if value is as_default and self.default is missing:
            raise TypeError("on_partial cannot be as_default if default is missing")
        self._on_partial = value

    def _get(self, **kwargs: Any) -> T:
        pos_values = []
        kw_values = kwargs
        any_exist = False
        errs: List[MissingEnvError] = []
        for env_var in self._pos_args:
            try:
                result = env_var._get_validated()  # noqa: SLF001
            except MissingEnvError as e:  # noqa: PERF203
                errs.append(e)
            else:
                if result.value is discard:
                    break
                pos_values.append(result.value)
                if result.exists:
                    any_exist = True
        for key, env_var in self._args.items():
            if key in kw_values:
                # key could be in kwargs because it was passed in as a positional argument, if so, we don't want to
                # overwrite it
                continue
            try:
                result = env_var._get_validated()  # noqa: SLF001
            except MissingEnvError as e:
                errs.append(e)
            else:
                if result.value is not discard:
                    kw_values[key] = result.value
                if result.exists:
                    any_exist = True

        if errs:
            if self.on_partial is not as_default and any_exist:
                if self.on_partial is missing:
                    raise SkipDefault(errs[0])
                if isinstance(self.on_partial, Factory):
                    return self.on_partial.callback()
                return self.on_partial  # type: ignore[return-value]
            raise errs[0]
        return self._type(*pos_values, **kw_values)

    def with_prefix(self, prefix: str) -> SchemaEnvVar[T]:
        return register_env_var(
            SchemaEnvVar(
                {k: v.with_prefix(prefix) for k, v in self._args.items()},
                self.default,
                type=self._type,
                description=self.description,
                on_partial=self.on_partial,
                validators=self._validators,
                pos_args=tuple(v.with_prefix(prefix) for v in self._pos_args),
            )
        )

    def _get_children(self) -> Iterable[EnvVar[Any]]:
        return chain(self._args.values(), self._pos_args)


@overload
def env_var(
    key: str,
    *,
    default: Union[T, Missing, AsDefault, Discard, Factory[T]] = missing,
    description: Optional[Description] = None,
    validators: Iterable[Callable[[T], T]] = (),
    case_sensitive: bool = False,
    strip_whitespaces: bool = True,
) -> InferEnvVar[T]:
    pass


@overload
def env_var(
    key: str,
    *,
    type: ParserInput[T],
    default: Union[T, Missing, Discard, Factory[T]] = missing,
    description: Optional[Description] = None,
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
    default: Union[T, Missing, Discard, Factory[T]] = missing,
    pos_args: Sequence[Union[EnvVar[Any], InferEnvVar[Any]]],
    args: Mapping[str, Union[EnvVar[Any], InferEnvVar[Any]]] = {},
    description: Optional[Description] = None,
    validators: Iterable[Callable[[T], T]] = (),
    on_partial: Union[T, Missing, AsDefault, Discard, Factory[T]] = missing,
) -> SchemaEnvVar[T]:
    pass


@overload
def env_var(
    key: str,
    *,
    type: Callable[..., T],
    default: Union[T, Missing, Discard, Factory[T]] = missing,
    pos_args: Sequence[Union[EnvVar[Any], InferEnvVar[Any]]] = (),
    args: Mapping[str, Union[EnvVar[Any], InferEnvVar[Any]]],
    description: Optional[Description] = None,
    validators: Iterable[Callable[[T], T]] = (),
    on_partial: Union[T, Missing, AsDefault, Discard, Factory[T]] = missing,
) -> SchemaEnvVar[T]:
    pass


def env_var(  # type: ignore[misc]
    key: str,
    *,
    type: Optional[ParserInput[T]] = None,
    default: Union[T, Missing, AsDefault, Discard] = missing,
    description: Optional[Description] = None,
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


all_env_vars: MutableSet[EnvVar] = WeakSet()

EV = TypeVar("EV", bound=EnvVar)


def register_env_var(ev: EV) -> EV:
    all_env_vars.add(ev)
    return ev


class InferType(Enum):
    infer_type = auto()


infer_type = InferType.infer_type


@dataclass
class InferEnvVar(Generic[T]):
    key: Optional[str]
    type: Any
    default: Union[T, Missing, AsDefault, Discard, Factory[T]]
    description: Optional[Description]
    validators: List[Callable[[T], T]]
    case_sensitive: bool
    strip_whitespaces: bool

    def with_spec(self, param_id: Union[str, int], spec: FactoryArgSpec | None) -> SingleEnvVar[T]:
        key = self.key
        if key is None:
            if not isinstance(param_id, str):
                raise ValueError(f"cannot infer key for positional parameter {param_id}, please specify a key")
            key = param_id

        default: Union[T, Missing, Discard, Factory[T]]
        if self.default is as_default:
            if spec is None:
                raise ValueError(f"cannot infer default for parameter {key}, parameter {param_id} not found in factory")

            if spec.default is factory_spec_missing:
                default = missing
            else:
                default = spec.default
        else:
            default = self.default

        if self.type is infer_type:
            if spec is None:
                raise ValueError(f"cannot infer type for parameter {key}, parameter {param_id} not found in factory")
            if spec.type is factory_spec_missing:
                raise ValueError(
                    f"cannot infer type for parameter {key}, parameter {param_id} has no type hint in factory"
                )
            ty = spec.type
        else:
            ty = self.type

        return register_env_var(
            SingleEnvVar(
                key=key,
                default=default,
                description=self.description,
                validators=self.validators,
                case_sensitive=self.case_sensitive,
                strip_whitespaces=self.strip_whitespaces,
                type=ty,
            )
        )

    def validator(self, func: Callable[[T], T]) -> Callable[[T], T]:
        self.validators.append(func)
        return func


def inferred_env_var(
    key: Optional[str] = None,
    *,
    type: Union[ParserInput[T], InferType] = infer_type,
    default: Union[T, Missing, AsDefault, Discard, Factory[T]] = as_default,
    description: Optional[Description] = None,
    validators: Iterable[Callable[[T], T]] = (),
    case_sensitive: bool = False,
    strip_whitespaces: bool = True,
) -> InferEnvVar[T]:
    return InferEnvVar(key, type, default, description, list(validators), case_sensitive, strip_whitespaces)
