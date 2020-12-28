from abc import abstractmethod
from typing import Generic, TypeVar, Union, List, Callable, Any, Type

from envolved.envparser import env_parser, CaseInsensitiveAmbiguity
from envolved.exceptions import MissingEnvError
from envolved.parsers import Parser, parser

T = TypeVar('T')

Validator = Callable[[T], T]


class BaseVar(Generic[T]):
    """
    Abstract protocol for all environment variables
    """

    @abstractmethod
    def get(self) -> T:
        """
        :return: the evaluated value of the environment variable
        """
        pass

    @abstractmethod
    def validator(self, func: Callable[[T], T]):
        """
        Add a validator to the environment variable
        :param func: the validator function
        :return: `func`, for use as a decorator
        """
        pass

    def ensurer(self, func: Callable[[T], Any]):
        """
        Add an ensuring validator to the environment variable
        :param func: the ensurer function
        :return: `func`, for use as a decorator

        ..note::
            The main difference between this method and validator, is that validator's output is used in place of the
             original value, and ensurer's output is ignored.
        """

        def validator(x):
            func(x)
            return x

        return self.validator(validator)


missing = object()


class EnvironmentVariable(BaseVar[T], Generic[T]):
    """
    A base class for concrete, cached environment variables
    """

    def __init__(self, default):
        """
        :param default: The default value of the environment variable, in case the environment variable is missing.
         Set to the sentinel `missing` to raise if the value is missing.
        """
        self._default = default
        self._cache: T = missing
        self._validators: List[Validator[T]] = []

    @abstractmethod
    def _get(self) -> T:
        """
        :return: The internal value of the variable, without any default-handling, caching, or validation
        :raise MissingEnvError: If the env var is missing.
        """
        pass

    def get(self) -> T:
        if self._cache is not missing:
            return self._cache

        try:
            ret = self._get()
        except MissingEnvError:
            if self._default is missing:
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


class SingleKeyEnvVar(EnvironmentVariable[T], Generic[T]):
    """
    An environment variable mapped to a single external environment variable
    """
    def __init__(self, key: str, default: T, *,
                 case_sensitive: bool = False, type: Union[Type[T], Parser[T]] = str):
        """
        :param key: The external name of the environment variable
        :param default: passed to EnvironmentVariable.__init__
        :param case_sensitive: Whether the name is case sensitive or not
        :param type: The internal conversion type or parser from the string value of the var to the output type
        """
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
