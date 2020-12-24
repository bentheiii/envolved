from os import environ
from typing import Dict, MutableMapping


class CaseInsensitiveAmbiguity(Exception):
    pass


class EnvParser:
    _environ: MutableMapping[str, str]
    _environ_case_insensitive: MutableMapping[str, Dict[str, str]]

    def __init__(self):
        self.reload()

    def reload(self):
        self._environ = environ
        self._environ_case_insensitive = {}
        for k, v in self._environ.items():
            lower = k.lower()
            if lower not in self._environ_case_insensitive:
                self._environ_case_insensitive[lower] = {}
            self._environ_case_insensitive[lower][k] = v

    def get(self, case_sensitive: bool, key: str):
        if case_sensitive:
            return self._environ[key]
        key = key.lower()
        candidates = self._environ_case_insensitive[key]
        if len(candidates) == 1:
            raw_value, = candidates.values()
        else:
            raise CaseInsensitiveAmbiguity(candidates)
        return raw_value


env_parser = EnvParser()
