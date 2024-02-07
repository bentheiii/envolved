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

Retrieving EnvVar Values
--------------------------
EnvVars should be retrieved once, preferably at the start of the program or initialization of singletons. This is
important for consistency. While envolved handles environment variables changing from within the python program,
external changes to environment variables are not handled.

.. warning::

    This is especially important when running on python 3.7, where in some cases, the environment variables will have
    to be reloaded on every retrieval.

Common Factories
-----------------
Here are some common types and factories to use when creating a :class:`~envvar.SchemaEnvVar`

* :class:`types.SimpleNamespace`: This will create a namespace with whatever arguments you pass to it.
* :class:`typing.NamedTuple`: A quick and easy way to create an annotated named tuple.
* :class:`typing.TypedDict`: To create type annotated dictionaries.

.. code-block::

    class Point(typing.NamedTuple):
        x: int
        y: int

    origin_ev = env_var('ORIGIN_', type=Point, args={
        'x': inferred_env_var(),
        'y': inferred_env_var(),
    })

    source_ev = env_var('Source_', type=SimpleNamespace, args={
        'x': inferred_env_var(type=int),
        'y': inferred_env_var(type=int),
    })

    # both these will result in a namespace that has ints for x and y

    class PointTD(typing.TypedDict):
        x: int
        y: int

    destination_ev = env_var('ORIGIN_', type=PointTD, args={
        'x': inferred_env_var(),
        'y': inferred_env_var(),
    })

    # this will result in a dict that has ints for keys "x" and "y"

Inferring Schema Parameter Names Without a Schema
--------------------------------------------------

We can actually use :func:`~envvar.inferred_env_var` to infer the name of :class:`~envvar.EnvVar` parameters without a schema. This is useful when
we want to prototype a schema without having to create a schema class.

.. code-block::

    from envolved import ...
    
    my_schema_ev = env_var('FOO_', type=SimpleNamespace, args={
        'x': inferred_env_var(type=int, default=0),
        'y': inferred_env_var(type=string, default='hello'),
    })

    # this will result in a namespace that fills `x` and `y` with the values of `FOO_X`
    # and `FOO_Y` respectively


Note a sticking point here, we have to specify not only the type of the inferred env var, but also the default value.

.. code-block::

    from envolved import ...

    my_schema_ev = env_var('FOO_', type=SimpleNamespace, args={
        'x': inferred_env_var(type=int),  # <-- this code will raise an exception
    })

.. note:: Why is this the behaviour?

    In normal :func:`~envvar.env_var`, not passing a `default` implies that the EnvVar is required, why can't we do the same for :func:`~envvar.inferred_env_var`? We do this to reduce side
    effects when an actual schema is passed in. If we were to assume that the inferred env var is required, then plugging in a schema that has a default value for that parameter would be
    a hard-to-detect breaking change that can have catostraphic consequences. By requiring the default value to be passed in, we force the user to be explicit about the default values,
    ehan it might be inferred.

We can specify that an inferred env var is required by explicitly stating `default=missing`

.. code-block::

    from envolved import ..., missing

    my_schema_ev = env_var('FOO_', type=SimpleNamespace, args={
        'x': inferred_env_var(type=int, default=missing),
        'y': inferred_env_var(type=string, default='hello'),
    })

    # this will result in a namespace that fills `x` with the value of `FOO_X`
    # and will raise an exception if `FOO_X` is not set
