from abc import abstractmethod, ABC
from functools import partial
from textwrap import TextWrapper
from typing import Generic, TypeVar, Union, List, Callable, Any, Type, Optional, NamedTuple
from weakref import ref

from envolved.envparser import env_parser, CaseInsensitiveAmbiguity
from envolved.exceptions import MissingEnvError
from envolved.parsers import Parser, parser

T = TypeVar('T')

ValidatorCallback = Callable[[T], T]


class BaseVarResult(NamedTuple):
    """
    Detailed outcome of getting the value of an environment variable
    """
    value: Any
    """
    The parsed and validated value of the variable
    """
    is_presence: bool
    """
    Whether this outcome should count as the environment variable as being "present". Used to resolve partial schemas
    """


class BaseVar(Generic[T], ABC):
    """
    Abstract protocol for all environment variables
    """
    @abstractmethod
    def get_(self) -> BaseVarResult:
        """
        :return: Retrieved value of the environment variable as a BaseVarResult object.
        """
        pass

    def get(self) -> T:
        """
        :return: the evaluated value of the environment variable
        """
        return self.get_().value

    @abstractmethod
    def validator(self, func: ValidatorCallback[T]):
        """
        Add a validator to the environment variable
        :param func: the validator function
        :return: `func`, for use as a decorator

        ..note::
            this also marks the function as a validator
        """
        if not hasattr(func, '__validates__'):
            try:
                setattr(func, '__validates__', ref(self))
            except AttributeError:
                pass
        return func

    def ensurer(self, func: Callable[[T], Any], **kwargs):
        """
        Add an ensuring validator to the environment variable
        :param func: the ensurer function
        :return: `func`, for use as a decorator

        ..note::
            The main difference between this method and validator, is that validator's output is used in place of the
             original value, and ensurer's output is ignored.
        """
        if func is None:
            return partial(self.ensurer, **kwargs)

        def validator(x):
            func(x)
            return x

        return self.validator(validator, **kwargs)

    @abstractmethod
    def description(self, parent_wrapper: TextWrapper) -> List[str]:
        pass


def validates(v):
    raw_ref = getattr(v, '__validates__', None)
    if not isinstance(raw_ref, ref):
        return None
    return raw_ref()


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
        self._validators: List[ValidatorCallback[T]] = []

    @abstractmethod
    def _get(self) -> T:
        """
        :return: The internal value of the variable, without any default-handling, caching, or validation
        :raise MissingEnvError: If the env var is missing.
        """
        pass

    def get_(self):
        try:
            ret = self._get()
        except MissingEnvError:
            if self._default is missing:
                raise
            presence = False
            ret = self._default
        else:
            presence = True
            for v in self._validators:
                ret = v(ret)

        return BaseVarResult(ret, presence)

    def validator(self, func):
        if isinstance(func, staticmethod):
            callback = func.__func__
        else:
            callback = func
        self._validators.append(callback)
        return super().validator(func)


class SingleKeyEnvVar(EnvironmentVariable[T], Generic[T]):
    """
    An environment variable mapped to a single external environment variable
    """

    def __init__(self, key: str, default: T, *,
                 case_sensitive: bool = False, type: Union[Type[T], Parser[T]] = str,
                 description: Optional[str] = None):
        """
        :param key: The external name of the environment variable.
        :param default: passed to EnvironmentVariable.__init__.
        :param case_sensitive: Whether the name is case sensitive or not.
        :param type: The internal conversion type or parser from the string value of the var to the output type.
        :param description: Description of the variable.
        """
        super().__init__(default)
        self.key = key
        self.converter = parser(type)
        self.case_sensitive = case_sensitive
        self._description = description

    def _get(self) -> T:
        try:
            raw_value = env_parser.get(self.case_sensitive, self.key)
        except KeyError:
            raise MissingEnvError(self.key)
        except CaseInsensitiveAmbiguity as cia:
            raise RuntimeError(f'environment error: cannot choose between environment variables {cia.args[0]}')

        raw_value = raw_value.strip()

        return self.converter(raw_value)

    def description(self, parent_wrapper: TextWrapper) -> List[str]:
        key = self.key
        if not self.case_sensitive:
            key = key.upper()

        if not self._description:
            return parent_wrapper.wrap(key)
        desc = ' '.join(self._description.strip().split())
        return parent_wrapper.wrap(key+': '+desc)
