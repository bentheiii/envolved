from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Tuple

from envolved.describe.util import prefix_description, suffix_description, wrap_description as wrap
from envolved.envvar import Description, EnvVar, SchemaEnvVar, SingleEnvVar


class NestedEnvVarsDescription(ABC):
    @abstractmethod
    def get_path(self) -> Tuple[str, ...]: ...

    @abstractmethod
    def wrap(self, *, indent_increment: str, **kwargs: Any) -> Iterable[str]: ...

    @classmethod
    def from_env_var(cls, path: Tuple[str, ...], env_var: EnvVar) -> NestedEnvVarsDescription:
        if isinstance(env_var, SingleEnvVar):
            path = (*path, env_var.key.upper())
            return SingleNestedDescription(path, env_var)
        else:
            assert isinstance(env_var, SchemaEnvVar)
            min_child = min(
                (e.key.upper() for e in env_var._get_descendants() if isinstance(e, SingleEnvVar)),
                default=None,
            )
            if min_child is not None:
                path = (*path, min_child)
            children = [cls.from_env_var(path, child) for child in env_var._get_children()]
            return SchemaNestedDescription(path, env_var, children)


@dataclass
class SingleNestedDescription(NestedEnvVarsDescription):
    path: Tuple[str, ...]
    env_var: SingleEnvVar

    @property
    def key(self) -> str:
        key = self.env_var.key
        if not self.env_var.case_sensitive:
            key = key.upper()

        return key

    def get_path(self) -> Tuple[str, ...]:
        return self.path

    def wrap(self, *, indent_increment: str, **kwargs: Any) -> Iterable[str]:
        text: Description
        if self.env_var.description is None:
            text = self.key
        else:
            prefix = self.key + ": "
            text = prefix_description(prefix, self.env_var.description)
            subsequent_indent_increment = len(prefix)
            kwargs["subsequent_indent"] = kwargs.get("subsequent_indent", "") + " " * subsequent_indent_increment
        return wrap(text, **kwargs)


class NestedDescriptionWithChildren(NestedEnvVarsDescription):
    children: Iterable[NestedEnvVarsDescription]

    @abstractmethod
    def title(self) -> Description | None: ...

    def wrap(self, *, indent_increment: str, **kwargs: Any) -> Iterable[str]:
        title = self.title()
        if title is not None:
            yield from wrap(title, **kwargs)
            kwargs["subsequent_indent"] = kwargs.get("subsequent_indent", "") + indent_increment
            kwargs["initial_indent"] = kwargs.get("initial_indent", "") + indent_increment
        for child in sorted(self.children, key=lambda i: i.get_path()):
            yield from child.wrap(indent_increment=indent_increment, **kwargs)


@dataclass
class SchemaNestedDescription(NestedDescriptionWithChildren):
    path: Tuple[str, ...]
    env_var: SchemaEnvVar
    children: Iterable[NestedEnvVarsDescription]

    def get_path(self) -> Tuple[str, ...]:
        return self.path

    def title(self) -> Description | None:
        if self.env_var.description is None:
            return ""
        else:
            return suffix_description(self.env_var.description, ":")


@dataclass
class RootNestedDescription(NestedDescriptionWithChildren):
    children: Iterable[NestedEnvVarsDescription]

    def get_path(self) -> Tuple[str, ...]:
        return ()

    def title(self) -> Description | None:
        return None

    @classmethod
    def from_envvars(cls, env_vars: Iterable[EnvVar]) -> RootNestedDescription:
        return cls([NestedEnvVarsDescription.from_env_var((), env_var) for env_var in env_vars])

    def wrap(self, *, indent_increment: Optional[str] = None, **kwargs: Any) -> Iterable[str]:
        if indent_increment is None:
            indent_increment = kwargs.get("subsequent_indent", " ")
            assert isinstance(indent_increment, str)
        return list(super().wrap(indent_increment=indent_increment, **kwargs))
