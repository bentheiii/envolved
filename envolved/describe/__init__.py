from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Set, TypeVar, Union

from envolved.describe.flat import FlatEnvVarsDescription
from envolved.describe.nested import NestedEnvVarsDescription, RootNestedDescription
from envolved.envvar import EnvVar, InferEnvVar, top_level_env_vars


def describe_env_vars(**kwargs: Any) -> List[str]:
    ret = EnvVarsDescription().nested().wrap(**kwargs)
    assert isinstance(ret, list)
    return ret


class EnvVarsDescription:
    def __init__(self, env_vars: Iterable[EnvVar] | None = None) -> None:
        self.env_var_roots = set()
        children: Set[EnvVar] = set()

        if env_vars is None:
            env_vars = top_level_env_vars
        for env_var in env_vars:
            self.env_var_roots.add(env_var)
            children.update(env_var._get_descendants())
        # remove any children we found along the way
        self.env_var_roots -= children

    def flat(self) -> FlatEnvVarsDescription:
        return FlatEnvVarsDescription.from_envvars(self.env_var_roots)

    def nested(self) -> NestedEnvVarsDescription:
        return RootNestedDescription.from_envvars(self.env_var_roots)


T = TypeVar(
    "T",
    bound=Union[EnvVar, InferEnvVar, Iterable[Union[EnvVar, InferEnvVar]], Mapping[Any, Union[EnvVar, InferEnvVar]]],
)


def exclude_from_description(to_exclude: T) -> T:
    global top_level_env_vars  # noqa: PLW0603

    if isinstance(to_exclude, EnvVar):
        evs = frozenset((to_exclude,))
    elif isinstance(to_exclude, InferEnvVar):
        evs = frozenset()
    elif isinstance(to_exclude, Mapping):
        evs = frozenset(to_exclude.values())
    elif isinstance(to_exclude, Iterable):
        evs = frozenset(to_exclude)
    else:
        raise TypeError(f"cannot exclude unrecognized type {type(to_exclude)!r}")

    top_level_env_vars -= evs

    return to_exclude
