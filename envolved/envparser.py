from os import environ, name
from typing import Dict, MutableMapping


class CaseInsensitiveAmbiguity(Exception):
    """
    The error raised if multiple external environment variables are equally valid for a case-insensitive
     environment variable
    """
    pass


if name == 'nt':
    # on windows, we are always case insensitive
    class EnvParser:
        _environ: MutableMapping[str, str]

        def __init__(self):
            self.reload()

        def reload(self):
            self._environ = dict(environ)

        def get(self, case_sensitive: bool, key: str):
            return self._environ[key.upper()]
else:
    class EnvParser:
        """
        A helper object capable of getting
        """
        _environ: MutableMapping[str, str]
        _environ_case_insensitive: MutableMapping[str, Dict[str, str]]

        def __init__(self):
            self.reload()

        def reload(self):
            """
            recalculate the value of the parser from the environment
            """
            self._environ = dict(environ)
            self._environ_case_insensitive = {}
            for k, v in self._environ.items():
                lower = k.lower()
                if lower not in self._environ_case_insensitive:
                    self._environ_case_insensitive[lower] = {}
                self._environ_case_insensitive[lower][k] = v

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
                return self._environ[key]
            candidates = self._environ_case_insensitive[key.lower()]
            if len(candidates) == 1:
                raw_value, = candidates.values()
                return raw_value
            elif key in candidates:
                return candidates[key]
            raise CaseInsensitiveAmbiguity(candidates)

env_parser = EnvParser()
"""
A global parser used by environment variables
"""
