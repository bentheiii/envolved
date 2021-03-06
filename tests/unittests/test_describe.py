from envolved import EnvVar, Schema
from envolved.describe import describe_env_vars


def test_describe():
    a = EnvVar('a', type=str, description='''
    full description of A
    ''')

    Point = Schema(
        x=EnvVar(type=int, description='x coordinate'),
        y=EnvVar(type=int, description='y coordinate')
    )

    p = EnvVar('p_', type=Point)

    q = EnvVar('q_', type=Point, description="""
    point Q
    next line
    """)

    b = EnvVar('b', type=str)

    t = EnvVar('t_', type=Schema(
        p=EnvVar('p_', type=Point),
        n=EnvVar('n', type=int)
    ))

    assert describe_env_vars(initial_indent='', subsequent_indent='\t') == [
        'A: full description of A',
        'B',
        'P:',
        '\tP_X: x coordinate',
        '\tP_Y: y coordinate',
        'Q: point Q next line',
        '\tQ_X: x coordinate',
        '\tQ_Y: y coordinate',
        'T:',
        '\tT_N',
        '\tT_P:',
        '\t\tT_P_X: x coordinate',
        '\t\tT_P_Y: y coordinate',
    ]