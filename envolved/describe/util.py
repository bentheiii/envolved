from textwrap import wrap
from typing import Any, Iterable

from envolved.envvar import Description


def wrap_description(description: Description, **kwargs: Any) -> Iterable[str]:
    if isinstance(description, str):
        yield from wrap(description, **kwargs)
    else:
        is_first_paragraph = True
        for line in description:
            yield from wrap(line, **kwargs)
            if is_first_paragraph:
                kwargs["initial_indent"] = kwargs.get("subsequent_indent", "")
                is_first_paragraph = False


def prefix_description(prefix: str, description: Description) -> Description:
    if isinstance(description, str):
        return prefix + description.lstrip()
    elif description:
        return [prefix + description[0].lstrip(), *description[1:]]
    else:
        return prefix


def suffix_description(description: Description, suffix: str) -> Description:
    if isinstance(description, str):
        return description.rstrip() + suffix
    elif description:
        return [*description[:-1], description[-1].rstrip() + suffix]
    else:
        return suffix
