from textwrap import TextWrapper
from typing import List

from envolved.envvar import childless_env_vars


def describe_env_vars(**kwargs):
    root_wrapper = TextWrapper(**kwargs)
    descriptions: List[List[str]] = []

    for env_var in list(childless_env_vars):
        if env_var.owner:
            continue
        descriptions.append(env_var.description(root_wrapper))

    ret = [line for lines in sorted(descriptions) for line in lines]
    return ret
