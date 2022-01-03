from os import environ, getenv, name
from typing import MutableMapping, Set


class CaseInsensitiveAmbiguity(Exception):
    """
    The error raised if multiple external environment variables are equally valid for a case-insensitive
     environment variable
    """
    pass


def getenv_unsafe(key):
    ret = getenv(key, None)
    if ret is None:
        raise KeyError
    return ret


def has_env(key):
    return getenv(key, None) is not None


if name == 'nt':
    # on windows, we are always case insensitive
    class EnvParser:
        def get(self, case_sensitive: bool, key: str):
            return getenv_unsafe(key.upper())
else:
    class EnvParser:  # type: ignore[no-redef]
        """
        A helper object capable of getting environment variables.
        """
        environ_case_insensitive: MutableMapping[str, Set[str]]

        # environ_case_insensitive might be out-of-date, so we need to be vigilant when using it

        def __init__(self):
            self._reload()

        def _reload(self):
            """
            recalculate the value of the parser from the environment
            """
            self.environ_case_insensitive = {}
            for k, v in environ.items():
                lower = k.lower()
                if lower not in self.environ_case_insensitive:
                    self.environ_case_insensitive[lower] = set()
                self.environ_case_insensitive[lower].add(k)

        def get(self, case_sensitive: bool, key: str) -> str:
            """
            look up the value of an environment variable.
            :param case_sensitive: Whether to make the lookup case-sensitive.
            :param key: The environment variable name.
            :return: the string value of the environment variable
            :raises KeyError: if the variable is missing
            :raises CaseInsensitiveAmbiguity: if there is ambiguity over multiple case-insensitive matches.
            """

            if case_sensitive:
                return getenv_unsafe(key)

            def out_of_date():
                self._reload()
                return get_case_insensitive(False)

            lowered = key.lower()

            def get_case_insensitive(retry_allowed: bool):
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
                    preferred_key, = candidates
                elif retry_allowed:
                    return out_of_date()
                else:
                    raise CaseInsensitiveAmbiguity(candidates)
                ret = getenv(preferred_key)
                if ret is None:
                    assert retry_allowed
                    return out_of_date()
                return ret

            return get_case_insensitive(True)

env_parser = EnvParser()
"""
A global parser used by environment variables
"""
