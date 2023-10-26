from typing import Any, Iterable, List, Mapping, TypeVar, Union

from envolved.basevar import _Description
from envolved.envvar import EnvVar, top_level_env_vars


def describe_env_vars(**kwargs: Any) -> List[str]:
    descriptions: List[_Description] = sorted(env_var.describe(**kwargs) for env_var in top_level_env_vars)
    return _Description.combine(descriptions, [], allow_blanks=True).lines


T = TypeVar("T", bound=Union[EnvVar, Iterable[EnvVar], Mapping[Any, EnvVar]])


def exclude_from_description(to_exclude: T) -> T:
    global top_level_env_vars  # noqa: PLW0603

    if isinstance(to_exclude, EnvVar):
        evs = frozenset((to_exclude,))
    elif isinstance(to_exclude, Mapping):
        evs = frozenset(to_exclude.values())
    elif isinstance(to_exclude, Iterable):
        evs = frozenset(to_exclude)
    else:
        raise TypeError(f"cannot exclude unrecognized type {type(to_exclude)!r}")

    top_level_env_vars -= evs

    return to_exclude
