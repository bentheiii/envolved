EnvVar Classes
=============================

.. module:: basevar

.. class:: EnvVar

    This is the base class for all environment variables.

    .. attribute:: default
        :type: T | missing

        The default value of the EnvVar. If this attribute is set to anything other than :attr:`missing`, then it will
        be used as the default value if the environment variable is not set.

    .. attribute:: description
        :type: str | None

        A description of the environment variable. Used when :ref:`describing:Describing Environment Variables`.

    .. attribute:: monkeypatch
        :type: T | missing | no_patch

        If set to anything other than :attr:`no_patch`, then the environment variable will be monkeypatched. Any call to
        :meth:`get` will return the value of this attribute. If set to :attr:`missing`, then calling :meth:`get` will
        raise an :exc:`MissingEnvError` (even if a default is set for the EnvVar). See :ref:`testing_utilities:Testing Utilities` for
        usage examples.

        .. warning::

            This method doesn't change the value within the environment. It only changes the value of the EnvVar.


    .. method:: get()->T

        Return the value of the environment variable. Different subclasses handle this operation differently.


    .. method:: validator(validator: collections.abc.Callable[[T], T]) -> collections.abc.Callable[[T], T]

        Add a validator to the environment variable. When an EnvVar's value is retrieved (using :meth:`get`), all its
        validators will be called in the order they were added (each validator will be called with the previous
        validator's return value). The result of the last validator will be the EnvVar's returned value.

        :param validator: A callable that will be added as a validator.
        :return: The validator, to allow usage of this function as a decorator.

        .. code-block::
            :caption: Using validators to assert that an environment variable is valid.

            connection_timeout_ev = env_var('CONNECTION_TIMEOUT_SECONDS', type=int)

            @connection_timeout_ev.validator
            def timeout_positive(value):
                if value <= 0:
                    raise ValueError('Connection timeout must be positive')
                return value
            # getting the value of the environment variable will now raise an error if the value is not positive

        .. code-block::
            :caption: Using validators to mutate the value of an environment variable.

            title_ev = env_var('TITLE', type=str)

            @title_ev.validator
            def title_capitalized(value):
                return value.capitalize()

            # now the value of title_ev will always be capitalized

        .. warning::
            Even if the validator does not mutate the value, it should still return the original value.

    .. method:: with_prefix(prefix: str) -> EnvVar[T]

        Return a new EnvVar with the parameters but with a given prefix. This method can be used to re-use an env-var
        schema to multiple env-vars.

        :param prefix: The prefix to use.
        :return: A new EnvVar with the given prefix, of the same type as teh envar being used.

    .. method:: patch(value: T | missing) -> typing.ContextManager

        Create a context manager that will monkeypatch the EnvVar to the given value, and then restore the original
        value when the context manager is exited.

        :param value: The value to set the environment variable to see :attr:`monkeypatch`.


.. class:: SingleEnvVar

    An :class:`EnvVar` subclass that interfaces with a single environment variable.

    When the value is retrieved, it will be searched for in the following order:

    #. The environment variable with the name as the :attr:`key` of the EnvVar is considered. If it exists, it will be
       used.
    #. If :attr:`case_sensitive` is ``False``. The environment variables with case-insensitive name as the :attr:`key`
       of the EnvVar is considered. If any exist, they will be used. If multiple exist, an :exc:`RuntimeError` will be
       raised.
    #. The :attr:`default` value of the EnvVar is used, if it exists.
    #. An :exc:`~exceptions.MissingEnvError` is raised.

    .. property:: key
        :type: str

        The name of the environment variable. (read only)

    .. property:: type
        :type: collections.abc.Callable[[str], T]

        The type of the environment variable. (read only)

        .. note::

            This may not necessarily be equal to the ``type`` parameter the EnvVar was created with (see
            :ref:`string_parsing:special parsers`).

    .. attribute:: case_sensitive
        :type: bool

        If set to False, only case-exact environment variables will be considered. Defaults to True.

        .. warning::

            This attribute has no effect on Windows, as all environment variables are always uppercase.

    .. attribute:: strip_whitespaces
        :type: bool

        If set to ``True`` (as is the default), whitespaces will be stripped from the environment variable value before
        it is processed.

.. class:: SchemaEnvVar

    An :class:`EnvVar` subclass that interfaces with a multiple environment variables, combining them into a single
    object.

    When the value is retrieved, all its :attr:`args` are retrieved, and are then used as keyword variables on the
    EnvVar's :attr:`type`.

    .. property:: type
        :type: collections.abc.Callable[..., T]

        The factory callable that will be used to create the object. (read only)

    .. property:: args
        :type: collections.abc.Mapping[str, EnvVar]

        The mapping of keyword arguments to :class:`EnvVar` objects. (read only)

    .. attribute:: on_partial
        :type: T | as_default | missing

        This attribute dictates how the EnvVar should behave when only some of the keys are explicitly present (i.e.
        When only some of the expected environment variables exist in the environment).

        * If set to :data:`as_default`, the EnvVar's :attr:`~EnvVar.default` will be returned.

          .. note::

            The EnvVar's :attr:`default` must not be :data:`missing` if this option is used.

        * If set to :data:`missing`, an :exc:`~exceptions.MissingEnvError` will be raised, even if the EnvVar's
          :attr:`~EnvVar.default` is set.
        * If set to a value, that value will be returned.


