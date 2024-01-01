from textwrap import dedent
from types import SimpleNamespace

from envolved import env_var
from envolved.describe import EnvVarsDescription


def test_describe_single_nested():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("b", type=int, description="Bee"),
        ]
    ).nested()

    assert d.wrap() == [
        "A: Apple",
        "B: Bee",
    ]


def test_describe_single_sensitive():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("b", type=int, description="Bee", case_sensitive=True),
            env_var("c", type=int),
        ]
    ).nested()

    assert d.wrap() == ["A: Apple", "b: Bee", "C"]


def test_describe_single_nested_multiline():
    d = EnvVarsDescription(
        [
            env_var(
                "a",
                type=int,
                description=dedent(
                    """
           Apple
           Banana
        """
                )
                .strip()
                .splitlines(),
            ),
            env_var("b", type=int, description="Bee"),
        ]
    ).nested()

    assert d.wrap() == [
        "A: Apple",
        "   Banana",
        "B: Bee",
    ]


def test_describe_single_nested_long():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="I'm a yankee doodle dandy, a yankee doodle do or die"),
            env_var("b", type=int, description="Bee"),
        ]
    ).nested()

    assert d.wrap(width=20) == [
        "A: I'm a yankee",
        "   doodle dandy, a",
        "   yankee doodle do",
        "   or die",
        "B: Bee",
    ]


def test_describe_multi_nested():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("d", type=int, description="Bee"),
            env_var(
                "c_",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
                description="Cee",
            ),
        ]
    ).nested()

    assert d.wrap() == [
        "A: Apple",
        "Cee:",
        " C_X: x coordinate",
        " C_Y: y coordinate",
        "D: Bee",
    ]


def test_describe_multi_nested_multiline():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("d", type=int, description="Bee"),
            env_var(
                "c_",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
                description=["Cee", "Fee", "Ree"],
            ),
        ]
    ).nested()

    assert d.wrap() == [
        "A: Apple",
        "Cee",
        "Fee",
        "Ree:",
        " C_X: x coordinate",
        " C_Y: y coordinate",
        "D: Bee",
    ]


def test_describe_multi_nested_long():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("d", type=int, description="Bee"),
            env_var(
                "c_",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
                description="I'm a yankee doodle dandy, a yankee doodle do or die",
            ),
        ]
    ).nested()

    assert d.wrap(width=20) == [
        "A: Apple",
        "I'm a yankee doodle",
        "dandy, a yankee",
        "doodle do or die:",
        " C_X: x coordinate",
        " C_Y: y coordinate",
        "D: Bee",
    ]


def test_describe_multi_nested_nodescription():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("d", type=int, description="Bee"),
            env_var(
                "c_",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
        ]
    ).nested()

    assert d.wrap() == [
        "A: Apple",
        " C_X: x coordinate",
        " C_Y: y coordinate",
        "D: Bee",
    ]
