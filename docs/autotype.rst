Autotype- Skip specifying the type
====================================

For schema environment variables, you can sometimes skip specifying the type of single environment variable args. When
this happens, the type of the envvar is extracted from the factory's type annotation.

.. code-block:: python

    @dataclass
    class GridSize:
        width: int
        height: int

    grid_size_ev = env_var('GRID', type=GridSize, args=dict(
        width=env_var('_WIDTH'),
        height=env_var('_HEIGHT'),
    ))

    # both GRID_WIDTH and GRID_HEIGHT are parsed as int

Type inference can be performed for the following factory types:

* dataclasses
* annotated named tuples (:class:`typing.NamedTuple`)
* annotated typed dicts (:class:`typing.TypedDict`)
* any class with a type annotated `__init__` or `__new__` method
* any callable with a type annotation