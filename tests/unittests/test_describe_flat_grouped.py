from textwrap import dedent
from types import SimpleNamespace

from pytest import mark

from envolved import env_var
from envolved.describe import EnvVarsDescription


def test_describe_single_flat():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="Apple"),
            env_var("b", type=int, description="Bee"),
        ]
    ).flat()

    assert d.wrap_grouped() == [
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
    ).flat()

    assert d.wrap_grouped() == ["A: Apple", "b: Bee", "C"]


def test_describe_single_flat_multiline():
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
    ).flat()

    assert d.wrap_grouped() == [
        "A: Apple",
        "   Banana",
        "B: Bee",
    ]


def test_describe_single_flat_long():
    d = EnvVarsDescription(
        [
            env_var("a", type=int, description="I'm a yankee doodle dandy, a yankee doodle do or die"),
            env_var("b", type=int, description="Bee"),
        ]
    ).flat()

    assert d.wrap_grouped(width=20) == [
        "A: I'm a yankee",
        "   doodle dandy, a",
        "   yankee doodle do",
        "   or die",
        "B: Bee",
    ]


@mark.parametrize(
    "schema_desc",
    [
        None,
        "Cee",
        ["Cee", "Fee", "Ree"],
        "I'm a yankee doodle dandy, a yankee doodle do or die",
    ],
)
def test_describe_multi_flat(schema_desc):
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
                description=schema_desc,
            ),
        ]
    ).flat()

    assert d.wrap_grouped() == [
        "A: Apple",
        "C_X: x coordinate",
        "C_Y: y coordinate",
        "D: Bee",
    ]


@mark.parametrize(
    "schema_desc",
    [
        None,
        "Cee",
        ["Cee", "Fee", "Ree"],
        "I'm a yankee doodle dandy, a yankee doodle do or die",
    ],
)
def test_describe_multi_flat_dragup(schema_desc):
    d = EnvVarsDescription(
        [
            env_var("B", type=int, description="Apple"),
            env_var("d", type=int, description="Bee"),
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "a": env_var("a", type=int, description="A coordinate"),
                    "x": env_var("c_x", type=int, description="x coordinate"),
                    "y": env_var("c_y", type=int, description="y coordinate"),
                },
                description=schema_desc,
            ),
        ]
    ).flat()

    assert d.wrap_grouped() == [
        "A: A coordinate",
        "C_X: x coordinate",
        "C_Y: y coordinate",
        "B: Apple",
        "D: Bee",
    ]
