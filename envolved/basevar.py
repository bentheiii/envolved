from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum, auto
from itertools import chain
from textwrap import wrap
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    List,
    Mapping,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)

from envolved.envparser import CaseInsensitiveAmbiguityError, env_parser
from envolved.exceptions import MissingEnvError, SkipDefault
from envolved.parsers import Parser, parser

T = TypeVar("T")
Self = TypeVar("Self")


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


@dataclass
class _EnvVarResult(Generic[T]):
    value: T | Discard
    exists: bool


@dataclass(order=True)
class _Description:
    min_key: str
    lines: List[str]

    @classmethod
    def combine(cls, descs: List[_Description], preamble: List[str], allow_blanks: bool = False) -> _Description:
        descs = sorted(descs)
        lines = list(preamble)
        for d in descs:
            if allow_blanks:
                part_lines: Iterable[str] = d.lines
            else:
                part_lines = (line for line in d.lines if line and not line.isspace())
            lines.extend(part_lines)
        return cls(descs[0].min_key, lines)


def unwrap_validator(func: Callable[[T], T]) -> Callable[[T], T]:
    if isinstance(func, staticmethod):
        func = func.__func__
    return func


class EnvVar(Generic[T], ABC):
    def __init__(
        self,
        default: Union[T, Missing, Discard],
        description: Optional[str],
        validators: Iterable[Callable[[T], T]] = (),
    ):
        self._validators: List[Callable[[T], T]] = [unwrap_validator(v) for v in validators]
        self.default = default
        self.description = description
        self.monkeypatch: Union[T, Missing, Discard, NoPatch] = no_patch

    def get(self) -> T:
        if self.monkeypatch is not no_patch:
            if self.monkeypatch is missing:
                raise MissingEnvError(self.describe())
            return self.monkeypatch  # type: ignore[return-value]
        return self._get_validated().value  # type: ignore[return-value]

    def validator(self, validator: Callable[[T], T]) -> EnvVar[T]:
        self._validators.append(validator)
        return self

    def _get_validated(self) -> _EnvVarResult[T]:
        try:
            value = self._get()
        except SkipDefault as sd:
            raise sd.args[0] from None
        except MissingEnvError as mee:
            if self.default is missing:
                raise mee
            return _EnvVarResult(self.default, exists=False)
        for validator in self._validators:
            value = validator(value)
        return _EnvVarResult(value, exists=True)

    @abstractmethod
    def _get(self) -> T:
        pass

    @abstractmethod
    def describe(self, **text_wrapper_args: Any) -> _Description:
        pass

    @abstractmethod
    def with_prefix(self: Self, prefix: str) -> Self:
        pass

    @abstractmethod
    def _get_children(self) -> Iterable[EnvVar]:
        pass

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
        default: Union[T, Missing, Discard] = missing,
        *,
        type: Union[Type[T], Parser[T]],
        description: Optional[str] = None,
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

    def _get(self) -> T:
        try:
            raw_value = env_parser.get(self.case_sensitive, self._key)
        except KeyError as err:
            raise MissingEnvError(self._key) from err
        except CaseInsensitiveAmbiguityError as cia:
            raise RuntimeError(f"environment error: cannot choose between environment variables {cia.args[0]}") from cia

        if self.strip_whitespaces:
            raw_value = raw_value.strip()
        return self.type(raw_value)

    def describe(self, **text_wrapper_args: Any) -> _Description:
        key = self._key
        if not self.case_sensitive:
            key = key.upper()

        if self.description:
            desc = " ".join(self.description.strip().split())
            description_text = f"{key}: {desc}"
        else:
            description_text = key
        return _Description(key, wrap(description_text, **text_wrapper_args))

    def with_prefix(self, prefix: str) -> SingleEnvVar[T]:
        return SingleEnvVar(
            prefix + self._key,
            self.default,
            type=self.type,
            description=self.description,
            case_sensitive=self.case_sensitive,
            strip_whitespaces=self.strip_whitespaces,
            validators=self._validators,
        )

    def _get_children(self) -> Iterable[EnvVar[Any]]:
        return ()


class SchemaEnvVar(EnvVar[T]):
    def __init__(
        self,
        keys: Mapping[str, EnvVar[Any]],
        default: Union[T, Missing, Discard] = missing,
        *,
        type: Callable[..., T],
        description: Optional[str] = None,
        on_partial: Union[T, Missing, AsDefault, Discard] = missing,
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
    def on_partial(self) -> Union[T, Missing, AsDefault, Discard]:
        return self._on_partial

    @on_partial.setter
    def on_partial(self, value: Union[T, Missing, AsDefault, Discard]):
        if value is as_default and self.default is missing:
            raise TypeError("on_partial cannot be as_default if default is missing")
        self._on_partial = value

    def _get(self) -> T:
        pos_values = []
        kw_values = {}
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
            try:
                result = env_var._get_validated()  # noqa: SLF001
            except MissingEnvError as e:  # noqa: PERF203
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
                return self.on_partial  # type: ignore[return-value]
            raise errs[0]
        return self._type(*pos_values, **kw_values)

    def describe(self, **text_wrapper_args: Any) -> _Description:
        if self.description:
            desc = " ".join(self.description.strip().split()) + ":"
            preamble = wrap(desc, **text_wrapper_args)
        else:
            # if there's no title, we need to add a newline to make the output look nice
            preamble = [""]
        inner_wrapper_args = dict(text_wrapper_args)
        inner_wrapper_args["initial_indent"] = "\t" + inner_wrapper_args.get("initial_indent", "")
        inner_wrapper_args["subsequent_indent"] = "\t" + inner_wrapper_args.get("subsequent_indent", "")
        parts = [env_var.describe(**inner_wrapper_args) for env_var in chain(self._pos_args, self._args.values())]
        return _Description.combine(parts, preamble)

    def with_prefix(self, prefix: str) -> SchemaEnvVar[T]:
        return SchemaEnvVar(
            {k: v.with_prefix(prefix) for k, v in self._args.items()},
            self.default,
            type=self._type,
            description=self.description,
            on_partial=self.on_partial,
            validators=self._validators,
            pos_args=tuple(v.with_prefix(prefix) for v in self._pos_args),
        )

    def _get_children(self) -> Iterable[EnvVar[Any]]:
        return chain(self._args.values(), self._pos_args)
