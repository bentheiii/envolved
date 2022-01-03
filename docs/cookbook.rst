Cookbook
=============
EnvVar variable
-----------------
EnvVars are best defined as global variables (so they will be included in the
:ref:`description <describing:Describing Environment Variables>`). Also, to differentiate the environment variables and
their eventually retrieved values, we should end the name of the EnvVar variables with the suffix ``_ev``.

.. code-block::

    board_size_ev : EnvVar[int] = env_var('BOARD_SIZE', type=int, default=8)

    ...

    class MyApp:
        def __init__(...):
            ...
            self.board_size = board_size_ev.get()
            ...

Common Factories
-----------------
Here are some common types and factories to use when creating a :class:`~basevar.SchemaEnvVar`

* :class:`types.SimpleNamespace`: This will create a namespace with whatever arguments you pass to it.
* :class:`typing.NamedTuple`: A quick and easy way to create an annotated named tuple.
* :class:`typing.TypedDict`: To create type annotated dictionaries.

.. code-block::

    class Point(typing.NamedTuple):
        x: int
        y: int

    origin_ev = env_var('ORIGIN', type=Point, args={
        'x': env_var('_X'),
        'y': env_var('_Y')
    })

    source_ev = env_var('Source', type=SimpleNamespace, args={
        'x': env_var('_X', type=int),
        'y': env_var('_Y', type=int)
    })

    # both these will result in a namespace that has ints for x and y

    class PointTD(typing.TypedDict):
        x: int
        y: int

    destination_ev = env_var('ORIGIN', type=PointTD, args={
        'x': env_var('_X'),
        'y': env_var('_Y')
    })

    # this will result in a dict that has ints for keys "x" and "y"