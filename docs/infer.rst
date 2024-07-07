Inferred Env Vars
====================================

.. currentmodule:: envvar

For schema environment variables, you can sometimes skip specifying the type, default, or even name of single
environment variable args by using :func:`inferred_env_var`. When this happens, the missing values of the envvar are
extracted from the factory's type annotation.

.. code-block:: python

    @dataclass
    class GridSize:
        width: int
        height: int = 10
        diagonal: bool = False

    grid_size_ev = env_var('GRID_', type=GridSize, args=dict(
        width=inferred_env_var('WIDTH'),  # GRID_WIDTH will be parsed as int
        height=inferred_env_var('HEIGHT'),  # GRID_HEIGHT will be parsed as int, and will have
                                            # default 10
        diagonal=inferred_env_var(),  # GRID_DIAGONAL will be parsed as bool, and will have 
                                      # default False
    ))

Type inference can be performed for the following factory types:

* dataclasses
* annotated named tuples (:class:`typing.NamedTuple`)
* annotated typed dicts (:class:`typing.TypedDict`)
* any class with a type annotated `__init__` or `__new__` method
* any callable with a type annotation

.. function:: inferred_env_var(key: str | None = None, *, type: Callable[[str], T] = ...,\
                               default: T | missing | as_default | discard = as_default, **kwargs) -> InferEnvVar

    Create an inferred env var that can be filled in by a parent :class:`~envvar.SchemaEnvVar` factory's type
    annotation to create a :class:`~envvar.SingleEnvVar`.

    :param key: The environment variable key to use. If unspecified, the name of the argument key will be used (the
                argument must be keyword argument in this case).
    :param type: The type to use for parsing the environment variable. If unspecified, the type will be inferred from
                 the parent factory's type annotation.
    :param default: The default value to use if the environment variable is not set. If unspecified, the default will
                    be inferred from the parent factory.
    :param kwargs: All other parameters are passed to :func:`~envvar.env_var`.

.. class:: InferEnvVar

    An inference env var that will be converted to a :class:`~envvar.SingleEnvVar` by a parent
    :class:`~envvar.SchemaEnvVar`.

    .. method:: validator(validator: collections.abc.Callable[[T], T]) -> collections.abc.Callable[[T], T]

        Add a validator to the resulting :class:`~envvar.SingleEnvVar`.

.. py:currentmodule:: envvar

There is also a legacy method to create inferred env vars, which is deprecated and will be removed in a future version.

.. function:: env_var(key: str, **kwargs) -> InferEnvVar[T]
    :noindex:

    Create an inferred env var that infers only the type.

Overriding Inferred Attributes in Annotation
----------------------------------------------------

Attributes inferred by :func:`inferred_env_var` can be overridden by specifying the attribute in the type annotation metadata with :data:`typing.Annotated`, and :class:`Env`.

.. code-block:: python

    from typing import Annotated
    from envolved import Env, inferred_env_var, env_var

    @dataclass
    class GridSize:
        width: int
        height: Annotated[int, Env(default=5)] = 10  # GRID_HEIGHT will have default 5
        diagonal: Annotated[bool, Env(key='DIAG')] = False  # GRID_DIAG will be parsed as bool

    grid_size_ev = env_var('GRID_', type=GridSize, args=dict(
        width=inferred_env_var(),  # GRID_WIDTH will be parsed as int
        height=inferred_env_var(),  # GRID_HEIGHT will be parsed as int, and will have
                                    # default 5
        diagonal=inferred_env_var(),  # GRID_DIAG will be parsed as bool, and will have 
                                      # default False
    ))

.. currentmodule:: factory_spec

.. class:: Env(*, key = ..., default = ..., type = ...)

    Metadata class to override inferred attributes in a type annotation.
    
    :param key: The environment variable key to use.
    :param default: The default value to use if the environment variable is not set.
    :param type: The type to use for parsing the environment variable.

Automatic Argument Inferrence
------------------------------------

When using :func:`~envvar.env_var` to create schema environment variables, it might be useful to automatically infer the arguments from the type's argument annotation altogether. This can be done by supplying ``args=...`` to the :func:`~envvar.env_var` function.

.. code-block:: python

    @dataclass
    class GridSize:
        width: Annotated[int, Env(key='WIDTH')]
        height: Annotated[int, Env(key='HEIGHT', default=5)]
        diagonal: Annotated[bool, Env(key='DIAG', default=False)]

    grid_size_ev = env_var('GRID_', type=GridSize, args=...)
    # this will be equivalent to
    grid_size_ev = env_var('GRID_', type=GridSize, args=dict(
        width=inferred_env_var('WIDTH'),
        height=inferred_env_var('HEIGHT', default=5),
        diagonal=inferred_env_var('DIAG', default=False),
    ))

Note that only parameters annotated with :data:`typing.Annotated` and :class:`Env` will be inferred, all others will be ignored.

.. code-block:: python

    @dataclass
    class GridSize:
        width: Annotated[int, Env(key='WIDTH')]
        height: Annotated[int, Env(key='HEIGHT', default=5)] = 10
        diagonal: bool = False

    grid_size_ev = env_var('GRID_', type=GridSize, args=...)
    # only width and height will be used as arguments in the env var

Arguments can be annotated with an empty :class:`Env` to allow them to be inferred as well.

.. code-block:: python

    @dataclass
    class GridSize:
        width: Annotated[int, Env(key='WIDTH')]
        height: Annotated[int, Env(key='HEIGHT', default=5)]
        diagonal: Annotated[bool, Env(key='DIAG')] = False

    grid_size_ev = env_var('GRID_', type=GridSize, args=...)
    # now all three arguments will be used as arguments in the env var