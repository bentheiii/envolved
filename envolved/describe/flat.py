from __future__ import annotations

from dataclasses import dataclass
from itertools import chain, groupby
from typing import Any, Iterable, List, Tuple
from warnings import warn

from envolved.describe.util import prefix_description, wrap_description as wrap
from envolved.envvar import Description, EnvVar, SingleEnvVar


@dataclass
class SingleEnvVarDescription:
    path: Iterable[str]
    env_var: SingleEnvVar

    @property
    def key(self) -> str:
        key = self.env_var.key
        if not self.env_var.case_sensitive:
            key = key.upper()

        return key

    def wrap(self, **kwargs: Any) -> Iterable[str]:
        text: Description
        if self.env_var.description is None:
            text = self.key
        else:
            text = prefix_description(self.key + ": ", self.env_var.description)
            subsequent_indent_increment = len(self.key) + 2
            kwargs["subsequent_indent"] = kwargs.get("subsequent_indent", "") + " " * subsequent_indent_increment
        return wrap(text, **kwargs)

    @classmethod
    def from_envvar(cls, path: Tuple[str, ...], env_var: EnvVar) -> Iterable[SingleEnvVarDescription]:
        if isinstance(env_var, SingleEnvVar):
            yield cls(
                (
                    *path,
                    env_var.key.upper(),
                ),
                env_var,
            )
        else:
            min_child = min(
                (e.key.upper() for e in env_var._get_descendants() if isinstance(e, SingleEnvVar)),
                default=None,
            )
            if min_child is not None:
                path = (*path, min_child)
            for child in env_var._get_children():
                yield from cls.from_envvar(path, child)

    @classmethod
    def collate(cls, instances: Iterable[SingleEnvVarDescription]) -> SingleEnvVarDescription:
        # collate multiple descriptions of the same env var
        assert len({i.env_var.key for i in instances}) == 1
        # in case of conflict we choose arbitrarily, with a warning
        # first we prefer an env var with a description, if one exists
        with_description = []
        without_description = []
        for instance in instances:
            if instance.env_var.description is None:
                without_description.append(instance)
            else:
                with_description.append(instance)

        if with_description:
            if len(with_description) > 1 and len({i.env_var.description for i in with_description}) > 1:
                warn(
                    f"multiple descriptions for env var {with_description[0].env_var.key!r}, choosing arbitrarily",
                    stacklevel=2,
                )
            return with_description[0]
        else:
            return without_description[0]


class FlatEnvVarsDescription:
    def __init__(self, env_var_descriptions: Iterable[SingleEnvVarDescription]) -> None:
        self.env_var_descriptions = env_var_descriptions

    def wrap_sorted(self, *, unique_keys: bool = True, **kwargs: Any) -> Iterable[str]:
        def key(i: SingleEnvVarDescription) -> str:
            return i.key.upper()

        env_var_descriptions = sorted(self.env_var_descriptions, key=key)

        ret: List[str] = []

        for _, group in groupby(env_var_descriptions, key=key):
            g = tuple(group)
            if len(g) > 1 and unique_keys:
                ret.extend(SingleEnvVarDescription.collate(g).wrap(**kwargs))
            else:
                ret.extend(chain.from_iterable(i.wrap(**kwargs) for i in g))

        return ret

    def wrap_grouped(self, **kwargs: Any) -> Iterable[str]:
        env_var_descriptions = sorted(self.env_var_descriptions, key=lambda i: (i.path, i.env_var.key))
        ret = list(
            chain.from_iterable(
                chain.from_iterable(d.wrap(**kwargs) for d in group)
                for _, group in groupby(env_var_descriptions, key=lambda i: i.path)
            )
        )
        return ret

    @classmethod
    def from_envvars(cls, env_vars: Iterable[EnvVar]) -> FlatEnvVarsDescription:
        env_var_descriptions = list(
            chain.from_iterable(SingleEnvVarDescription.from_envvar((), env_var) for env_var in env_vars)
        )
        return cls(env_var_descriptions)
