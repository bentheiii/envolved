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

    assert d.wrap_sorted() == [
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

    assert d.wrap_sorted() == ["A: Apple", "b: Bee", "C"]


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

    assert d.wrap_sorted() == [
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

    assert d.wrap_sorted(width=20) == [
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

    assert d.wrap_sorted() == [
        "A: Apple",
        "C_X: x coordinate",
        "C_Y: y coordinate",
        "D: Bee",
    ]


def test_describe_flat_collision():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
            env_var("x", type=int),
            env_var("z", type=int, description="z coordinate"),
        ]
    ).flat()

    assert d.wrap_sorted() == [
        "X: x coordinate",
        "Y: y coordinate",
        "Z: z coordinate",
    ]


def test_describe_flat_cousins():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int),
                    "a": env_var("a", type=int),
                },
            ),
            env_var("z", type=int, description="z coordinate"),
        ]
    ).flat()

    assert d.wrap_sorted() == [
        "A",
        "X: x coordinate",
        "Y: y coordinate",
        "Z: z coordinate",
    ]


def test_describe_flat_collision_nodesc():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
            env_var("x", type=int),
            env_var("z", type=int, description="z coordinate"),
        ]
    ).flat()

    assert d.wrap_sorted() == [
        "X",
        "Y: y coordinate",
        "Z: z coordinate",
    ]


def test_describe_flat_collision_warning():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="ex"),
                },
            ),
            env_var("x", type=int, description="x coordinate"),
        ]
    ).flat()

    (x_desc,) = d.wrap_sorted()

    assert x_desc in [
        "X: ex",
        "X: x coordinate",
    ]


def test_describe_flat_collision_dup():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="x coordinate"),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
            env_var("x", type=int),
            env_var("z", type=int, description="z coordinate"),
        ]
    ).flat()

    assert sorted(d.wrap_sorted(unique_keys=False)) == [
        "X",
        "X: x coordinate",
        "Y: y coordinate",
        "Z: z coordinate",
    ]


def test_describe_flat_collision_nodesc_dup():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int),
                    "y": env_var("y", type=int, description="y coordinate"),
                },
            ),
            env_var("x", type=int),
            env_var("z", type=int, description="z coordinate"),
        ]
    ).flat()

    assert d.wrap_sorted(unique_keys=False) == [
        "X",
        "X",
        "Y: y coordinate",
        "Z: z coordinate",
    ]


def test_describe_flat_collision_warning_dup():
    d = EnvVarsDescription(
        [
            env_var(
                "",
                type=SimpleNamespace,
                args={
                    "x": env_var("x", type=int, description="ex"),
                },
            ),
            env_var("x", type=int, description="x coordinate"),
        ]
    ).flat()

    assert sorted(d.wrap_sorted(unique_keys=False)) == [
        "X: ex",
        "X: x coordinate",
    ]
