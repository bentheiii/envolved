from abc import abstractmethod
from typing import Generic, TypeVar, Union, List, Callable

from envolved.envparser import env_parser, CaseInsensitiveAmbiguity
from envolved.exceptions import MissingEnvError
from envolved.parsers import Parser, parser

T = TypeVar('T')

Validator = Callable[[T], T]


class VarProtocol(Generic[T]):
    @abstractmethod
    def get(self) -> T:
        pass

    @abstractmethod
    def validator(self, func):
        pass

    def ensurer(self, func):
        def validator(x):
            func(x)
            return x

        return self.validator(validator)


class BaseVar(VarProtocol[T], Generic[T]):
    def __init__(self, default):
        self._default = default
        self._cache: T = _missing
        self._validators: List[Validator[T]] = []

    @abstractmethod
    def _get(self) -> T:
        pass

    def get(self) -> T:
        if self._cache is not _missing:
            return self._cache

        try:
            ret = self._get()
        except MissingEnvError:
            if self._default is _missing:
                raise
            ret = self._default
        else:
            for v in self._validators:
                ret = v(ret)

        self._cache = ret
        return ret

    def validator(self, func):
        self._validators.append(func)
        return func


_missing = object()


class SingleKeyEnvVar(BaseVar[T], Generic[T]):
    def __init__(self, key: str, default: T, *,
                 case_sensitive: bool = False, type: Union[type, Parser] = str):
        super().__init__(default)
        self.key = key
        self.converter = parser(type)
        self.case_sensitive = case_sensitive

    def _get(self) -> T:
        try:
            raw_value = env_parser.get(self.case_sensitive, self.key)
        except KeyError:
            raise MissingEnvError(self.key)
        except CaseInsensitiveAmbiguity as cia:
            raise RuntimeError(f'environment error: cannot choose between environment variables {cia.args[0]}')

        raw_value = raw_value.strip()

        return self.converter(raw_value)
