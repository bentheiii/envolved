from types import SimpleNamespace

from envolved import env_var
from envolved.describe import describe_env_vars, exclude_from_description


def test_describe():
    a = env_var('a', type=str, description='''
    full description of A
    ''')  # noqa: F841

    Point_args = dict(
        x=env_var('x', type=int, description='x coordinate'),
        y=env_var('y', type=int, description='y coordinate')
    )
    exclude_from_description(Point_args)

    p = env_var('p_', type=SimpleNamespace, args=Point_args)  # noqa: F841

    q = env_var('q_', type=SimpleNamespace, args=Point_args, description="""
    point Q
    next line
    """)  # noqa: F841

    b = env_var('b', type=str)  # noqa: F841

    t = env_var('t_', type=SimpleNamespace, args=dict(  # noqa: F841
        p=env_var('p_', type=SimpleNamespace, args=Point_args),
        n=env_var('n', type=int)
    ))

    d = env_var('d', type=int)
    exclude_from_description(d)

    e_f_g = env_var('e', type=int), env_var('f', type=int), env_var('g', type=int)
    exclude_from_description(e_f_g)

    assert describe_env_vars(initial_indent='', subsequent_indent='\t') == [
        'A: full description of A',
        'B',
        '',
        '\tP_X: x coordinate',
        '\tP_Y: y coordinate',
        'point Q next line:',
        '\tQ_X: x coordinate',
        '\tQ_Y: y coordinate',
        '',
        '\tT_N',
        '\t\tT_P_X: x coordinate',
        '\t\tT_P_Y: y coordinate',
    ]
