from __future__ import annotations

from itertools import chain
from typing import Any, Iterable, List, Mapping, Set, TypeVar, Union

from envolved.describe.flat import FlatEnvVarsDescription
from envolved.describe.nested import NestedEnvVarsDescription, RootNestedDescription
from envolved.envvar import EnvVar, InferEnvVar, all_env_vars


def describe_env_vars(**kwargs: Any) -> List[str]:
    ret = EnvVarsDescription().nested().wrap(**kwargs)
    assert isinstance(ret, list)
    return ret


class EnvVarsDescription:
    def __init__(self, env_vars: Iterable[EnvVar] | None = None) -> None:
        self.env_var_roots = set()
        children: Set[EnvVar] = set()

        if env_vars is None:
            env_vars = all_env_vars
            to_exclude = roots_to_exclude_from_description | set(
                chain.from_iterable(r._get_descendants() for r in roots_to_exclude_from_description)
            )
        else:
            to_exclude = set()

        for env_var in env_vars:
            self.env_var_roots.add(env_var)
            children.update(env_var._get_descendants())
        # remove any children we found along the way
        self.env_var_roots -= children
        # remove any children we were asked to exclude
        self.env_var_roots -= to_exclude

    def flat(self) -> FlatEnvVarsDescription:
        return FlatEnvVarsDescription.from_envvars(self.env_var_roots)

    def nested(self) -> NestedEnvVarsDescription:
        return RootNestedDescription.from_envvars(self.env_var_roots)


T = TypeVar(
    "T",
    bound=Union[EnvVar, InferEnvVar, Iterable[Union[EnvVar, InferEnvVar]], Mapping[Any, Union[EnvVar, InferEnvVar]]],
)

roots_to_exclude_from_description: Set[EnvVar] = set()


def exclude_from_description(to_exclude: T) -> T:
    if isinstance(to_exclude, EnvVar):
        roots_to_exclude_from_description.add(to_exclude)
    elif isinstance(to_exclude, Mapping):
        exclude_from_description(to_exclude.values())
    elif isinstance(to_exclude, Iterable):
        for v in to_exclude:
            exclude_from_description(v)
    elif isinstance(to_exclude, InferEnvVar):
        pass
    else:
        raise TypeError(f"cannot exclude unrecognized type {type(to_exclude)!r}")

    return to_exclude
