import sys
from abc import ABC, abstractmethod
from os import environ, getenv, name
from threading import Lock
from typing import Any, MutableMapping, Set, Tuple, Type


class CaseInsensitiveAmbiguityError(Exception):
    """
    The error raised if multiple external environment variables are equally valid for a case-insensitive
     environment variable
    """


def getenv_unsafe(key: str) -> str:
    ret = getenv(key, None)
    if ret is None:
        raise KeyError
    return ret


def has_env(key: str) -> bool:
    return getenv(key, None) is not None


class BaseEnvParser(ABC):
    @abstractmethod
    def get(self, case_sensitive: bool, key: str) -> str:
        """
        Should raise KeyError if missing, and AmbiguiyError if there are multiple case-insensitive matches
        """


# on windows, we are always case insensitive
class CaseInsensitiveEnvParser(BaseEnvParser):
    def get(self, case_sensitive: bool, key: str) -> str:
        return getenv_unsafe(key.upper())


class ReloadingEnvParser(BaseEnvParser, ABC):
    environ_case_insensitive: MutableMapping[str, Set[str]]

    def reload(self):
        if self.lock.locked():
            # if the lock is already held by someone, we don't need to do any work, just wait until they're done
            with self.lock:
                return
        with self.lock:
            self.environ_case_insensitive = {}
            for k in environ.keys():
                lower = k.lower()
                if lower not in self.environ_case_insensitive:
                    self.environ_case_insensitive[lower] = set()
                self.environ_case_insensitive[lower].add(k)

    def __init__(self):
        self.lock = Lock()
        self.reload()


class AuditingEnvParser(ReloadingEnvParser):
    environ_case_insensitive: MutableMapping[str, Set[str]]

    def __init__(self):
        super().__init__()
        sys.addaudithook(self.audit_hook)

    def audit_hook(self, event: str, args: Tuple[Any, ...]):  # pragma: no cover
        if event == "os.putenv":
            if not args:
                return
            key = args[0]
            if isinstance(key, bytes):
                try:
                    key = key.decode("ascii")
                except UnicodeDecodeError:
                    return
            elif not isinstance(key, str):
                return
            lower = key.lower()
            with self.lock:
                if lower not in self.environ_case_insensitive:
                    self.environ_case_insensitive[lower] = set()
                self.environ_case_insensitive[lower].add(key)
        elif event == "os.unsetenv":
            if not args:
                return
            key = args[0]
            if isinstance(key, bytes):
                try:
                    key = key.decode("ascii")
                except UnicodeDecodeError:
                    return
            elif not isinstance(key, str):
                return
            lower = key.lower()
            with self.lock:
                if lower in self.environ_case_insensitive:
                    self.environ_case_insensitive[lower].discard(key)

    def get(self, case_sensitive: bool, key: str) -> str:
        if case_sensitive:
            return getenv_unsafe(key)

        lowered = key.lower()
        candidates = self.environ_case_insensitive[lowered]  # will raise KeyError if not found
        if not candidates:
            raise KeyError(key)
        if key in candidates:
            preferred_key = key
        elif len(candidates) == 1:
            (preferred_key,) = candidates
        else:
            raise CaseInsensitiveAmbiguityError(candidates)
        ret = getenv(preferred_key)
        if ret is None:
            # someone messed with the env without triggering the auditing hook
            self.reload()
            return self.get(case_sensitive, key)
        return ret


class NonAuditingEnvParser(ReloadingEnvParser):
    def get(self, case_sensitive: bool, key: str) -> str:
        if case_sensitive:
            return getenv_unsafe(key)

        def out_of_date() -> str:
            self.reload()
            return get_case_insensitive(retry_allowed=False)

        lowered = key.lower()

        def get_case_insensitive(retry_allowed: bool) -> str:
            if retry_allowed and lowered not in self.environ_case_insensitive:
                # if a retry is allowed, and no candidates are available, we need to retry
                return out_of_date()
            candidates = self.environ_case_insensitive[lowered]
            if key in candidates:
                preferred_key = key
            elif retry_allowed and has_env(key):
                # key is not a candidate, but it is in the env
                return out_of_date()
            elif len(candidates) == 1:
                (preferred_key,) = candidates
            elif retry_allowed:
                return out_of_date()
            else:
                raise CaseInsensitiveAmbiguityError(candidates)
            ret = getenv(preferred_key)
            if ret is None:
                assert retry_allowed
                return out_of_date()
            return ret

        return get_case_insensitive(retry_allowed=True)


EnvParser: Type[BaseEnvParser]
if name == "nt":
    # in windows, all env vars are uppercase
    EnvParser = CaseInsensitiveEnvParser
elif sys.version_info >= (3, 8):  # adding audit hooks is only supported in python 3.8+
    EnvParser = AuditingEnvParser
else:
    EnvParser = NonAuditingEnvParser


env_parser = EnvParser()
"""
A global parser used by environment variables
"""
