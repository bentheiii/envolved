from __future__ import annotations

from typing import Any, Union, Optional

try:
    from types import UnionType
except ImportError:
    UnionType = None

try:
    from types import NoneType
except ImportError:
    NoneType = type(None)


def extract_from_option(t: Any) -> Optional[type]:
    if UnionType and isinstance(t, UnionType):
        parts = t.__args__
    else:
        origin = getattr(t, '__origin__', None)
        if origin is Union:
            parts = t.__args__
        else:
            return None

    if len(parts) == 2 and NoneType in parts:
        return next(p for p in parts if p is not NoneType)
    return None
