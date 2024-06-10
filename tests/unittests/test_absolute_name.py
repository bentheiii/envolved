from types import SimpleNamespace

from envolved.absolute_name import AbsoluteName
from envolved.envvar import env_var


def test_absolute_name(monkeypatch):
    a = env_var(
        "a_",
        type=SimpleNamespace,
        args={
            "a": env_var("A", type=str),
            "b": env_var(AbsoluteName("B"), type=str),
            "b2": env_var("b", type=str),
        },
    )

    monkeypatch.setenv("a_a", "1")
    monkeypatch.setenv("B", "2")
    monkeypatch.setenv("a_b", "3")

    assert a.get() == SimpleNamespace(a="1", b="2", b2="3")
