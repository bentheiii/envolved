from textwrap import dedent
from types import SimpleNamespace

from envolved import env_var
from envolved.describe import describe_env_vars, exclude_from_description


def test_describe():
    a = env_var(  # noqa: F841
        "a",
        type=str,
        description="""
    full description of A
    """,
    )

    point_args = {
        "x": env_var("x", type=int, description="x coordinate"),
        "y": env_var("y", type=int, description="y coordinate"),
    }
    exclude_from_description(point_args)

    p = env_var("p_", type=SimpleNamespace, args=point_args)  # noqa: F841

    q = env_var(  # noqa: F841
        "q_",
        type=SimpleNamespace,
        args=point_args,
        description=dedent(
            """
            point Q
            next line
            """
        ).strip(),
    )

    b = env_var("b", type=str)  # noqa: F841

    t = env_var(  # noqa: F841
        "t_",
        type=SimpleNamespace,
        args={"p": env_var("p_", type=SimpleNamespace, args=point_args), "n": env_var("n", type=int)},
    )

    d = env_var("d", type=int)
    exclude_from_description(d)

    e_f_g = env_var("e", type=int), env_var("f", type=int), env_var("g", type=int)
    exclude_from_description(e_f_g)

    assert describe_env_vars() == [
        "A: full description of A",
        "B",
        " P_X: x coordinate",
        " P_Y: y coordinate",
        "point Q next line:",
        " Q_X: x coordinate",
        " Q_Y: y coordinate",
        " T_N",
        "  T_P_X: x coordinate",
        "  T_P_Y: y coordinate",
    ]
