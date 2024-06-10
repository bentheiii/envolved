class AbsoluteName(str):
    __slots__ = ()


def with_prefix(prefix: str, name: str) -> str:
    if isinstance(name, AbsoluteName):
        return name
    return prefix + name
