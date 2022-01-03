from typing import Tuple


class MissingEnvError(Exception):
    """
    An exception raised when looking up a missing environment variable without a default.
    """
    args: Tuple[str]


class SkipDefault(BaseException):
    """
    an exception raised when a missing env error should be raised, even if a default is defined
    """
    args: Tuple[MissingEnvError]
