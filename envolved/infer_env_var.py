from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING, Any, Callable, Generic, Iterable, List, NoReturn, Optional, TypeVar, Union

from envolved.basevar import AsDefault, Discard, Missing, SingleEnvVar, as_default, missing
from envolved.factory_spec import FactoryArgSpec, missing as factory_spec_missing
from envolved.parsers import ParserInput

T = TypeVar("T")


class InferType(Enum):
    infer_type = auto()


infer_type = InferType.infer_type


@dataclass
class InferEnvVar(Generic[T]):
    key: Optional[str]
    type: Any
    default: Union[T, Missing, AsDefault, Discard]
    description: Optional[str]
    validators: List[Callable[[T], T]]
    case_sensitive: bool
    strip_whitespaces: bool

    def with_spec(self, param_id: Union[str, int], spec: FactoryArgSpec) -> SingleEnvVar[T]:
        key = self.key
        if key is None:
            if not isinstance(param_id, str):
                raise ValueError(f"cannot infer key for positional parameter {param_id}, please specify a key")
            key = param_id

        default = spec.default if self.default is as_default else self.default
        if default is factory_spec_missing:
            default = missing

        ty = spec.type if self.type is infer_type else self.type
        if ty is factory_spec_missing:
            raise ValueError(f"cannot infer type for parameter {key}, type not found in factory")

        return SingleEnvVar(
            key=key,
            default=default,
            description=self.description,
            validators=self.validators,
            case_sensitive=self.case_sensitive,
            strip_whitespaces=self.strip_whitespaces,
            type=ty,
        )

    def validator(self, func: Callable[[T], T]) -> Callable[[T], T]:
        self.validators.append(func)
        return func


def inferred_env_var(
    key: Optional[str] = None,
    *,
    type: Union[ParserInput[T], InferType] = infer_type,
    default: Union[T, Missing, AsDefault, Discard] = as_default,
    description: Optional[str] = None,
    validators: Iterable[Callable[[T], T]] = (),
    case_sensitive: bool = True,
    strip_whitespaces: bool = True,
) -> InferEnvVar[T]:
    return InferEnvVar(key, type, default, description, list(validators), case_sensitive, strip_whitespaces)


class AutoTypedEnvVar(InferEnvVar[T]):
    if not TYPE_CHECKING:

        def get(self) -> NoReturn:
            raise AttributeError(
                "this env-var is auto-typed and cannot be accessed directly (did you forget to " "specify a type?)"
            )
