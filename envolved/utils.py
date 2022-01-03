from __future__ import annotations

from inspect import Parameter, signature
from typing import Any, Callable, Dict, get_type_hints


def factory_type_hints(factory: Callable) -> Dict[str, Any]:
    """
    Generate type hints for a factory or class. Combining its __init__ and __new__ keyword parameters.
    :param factory: The factory function or type.
    :return: A combined parameter annotation dict for `factory`.
    """
    if isinstance(factory, type):
        initial_mapping = get_type_hints(factory)
        init_hints = factory_type_hints(factory.__init__)  # type: ignore[misc]
        new_hints = factory_type_hints(factory.__new__)
        # we arbitrarily decide that __init__ wins over __new__
        return {**initial_mapping, **new_hints, **init_hints}

    hints = get_type_hints(factory)
    sign = signature(factory)
    hints.update(
        {
            param.name: hints[param.name]
            for param in sign.parameters.values()
            if param.kind in (Parameter.POSITIONAL_OR_KEYWORD, Parameter.KEYWORD_ONLY) and param.name in hints
        }
    )
    return hints
