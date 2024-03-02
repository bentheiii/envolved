EnvVars
=========================================================

.. module:: envvar

.. function:: env_var(key: str, *, type: collections.abc.Callable[[str], T],\
            default: T | missing | discard | Factory[T] = missing,\
            description: str | collections.abc.Sequence[str] | None = None, \
            validators: collections.abc.Iterable[collections.abc.Callable[[T], T]] = (), \
            case_sensitive: bool = False, strip_whitespaces: bool = True) -> envvar.SingleEnvVar[T]

    Creates an EnvVar that reads from one environment variable.

    :param key: The key of the environment variable.
    :param type: A callable to use to parse the string value of the environment variable.
    :param default: The default value of the EnvVar if the environment variable is missing. If unset, an exception will
     be raised if the environment variable is missing. The default can also be a :class:`~envvar.Factory` to specify a default factory, 
     or :attr:`~envvar.discard` to indicate to parent :class:`SchemaEnvVars <envvar.SchemaEnvVar>` that this env var should be discarded from the
     arguments if it is missing.
    :param description: A description of the EnvVar. See :ref:`describing:Describing Environment Variables`.
    :param validators: A list of callables to validate the value of the EnvVar. Validators can be added to the EnvVar
     after it is created with :func:`~envvar.EnvVar.validator`.
    :param case_sensitive: Whether the key of the EnvVar is case sensitive.
    :param strip_whitespaces: Whether to strip whitespaces from the value of the environment variable before parsing it.

.. function:: env_var(key: str, *, type: collections.abc.Callable[..., T], \
            default: T | missing | discard | Factory[T] = missing, \
            args: dict[str, envvar.EnvVar | InferEnvVar] = ..., \
            pos_args: collections.abc.Sequence[envvar.EnvVar | InferEnvVar] = ..., \
            description: str | collections.abc.Sequence[str] | None = None,\
            validators: collections.abc.Iterable[collections.abc.Callable[[T], T]] = (), \
            on_partial: T | missing | as_default | discard = missing) -> envvar.SchemaEnvVar[T]
    :noindex:

    Creates an EnvVar that reads from multiple environment variables.

    :param key: The key of the environment variable. This will be a common prefix applied to all environment variables.
    :param type: A callable to call with ``pos_args`` and ``args`` to create the EnvVar value.
    :param default: The default value of the EnvVar if the environment variable is missing. If unset, an exception will
     be raised if the environment variable is missing. The default can also be a :class:`~envvar.Factory` to specify a default factory, 
     or :attr:`~envvar.discard` to indicate to parent :class:`SchemaEnvVars <envvar.SchemaEnvVar>` that this env var should be discarded from the
     arguments if it is missing.
    :param pos_args: A sequence of EnvVars to to retrieve and use as positional arguments to ``type``. Arguments can be
     :ref:`inferred <infer:Inferred Env Vars>` in some cases.
    :param args: A dictionary of EnvVars to to retrieve and use as arguments to ``type``. Arguments can be
     :ref:`inferred <infer:Inferred Env Vars>` in some cases.
    :param description: A description of the EnvVar. See :ref:`describing:Describing Environment Variables`.
    :param validators: A list of callables to validate the value of the EnvVar. Validators can be added to the EnvVar
     after it is created with :func:`~envvar.EnvVar.validator`.
    :param on_partial: The value to use if the EnvVar is partially missing. See :attr:`~envvar.SchemaEnvVar.on_partial`.

.. class:: EnvVar

    This is the base class for all environment variables.

    .. attribute:: default
        :type: T | missing | discard | envvar.Factory[T]

        The default value of the EnvVar. If this attribute is set to anything other than :attr:`missing`, then it will
        be used as the default value if the environment variable is not set. If set to :attr:`discard`, then the
        value will not be used as an argument to parent :class:`SchemaEnvVars <SchemaEnvVar>`.

    .. attribute:: description
        :type: str| collections.abc.Sequence[str] | None

        A description of the environment variable. Used when :ref:`describing:Describing Environment Variables`. Can also be
        set to a sequence of strings, in which case each string will be a separate paragraph in the description.

    .. attribute:: monkeypatch
        :type: T | missing | no_patch | discard

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
        :return: A new EnvVar with the given prefix, of the same type as the envar being used.

    .. method:: patch(value: T | missing | discard) -> typing.ContextManager

        Create a context manager that will monkeypatch the EnvVar to the given value, and then restore the original
        value when the context manager is exited.

        :param value: The value to set the environment variable to see :attr:`monkeypatch`.


.. class:: SingleEnvVar

    An :class:`EnvVar` subclass that interfaces with a single environment variable.

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

    .. method:: get(**kwargs)->T

        Return the value of the environment variable. The value will be searched for in the following order:

        #. The environment variable with the name as the :attr:`key` of the EnvVar is considered. If it exists, it will be
           used.

        #. If :attr:`case_sensitive` is ``False``. Environment variables with case-insensitive names equivalent to
           :attr:`key` of the EnvVar is considered. If any exist, they will be used. If multiple exist, a
           :exc:`RuntimeError` will be raised.

        #. The :attr:`~EnvVar.default` value of the EnvVar is used, if it exists. If the :attr:`~EnvVar.default` is an instance of
           :class:`~envvar.Factory`, the factory will be called (without arguments) to create the value of the EnvVar.

        #. A :exc:`~exceptions.MissingEnvError` is raised.

        :param kwargs: Additional keyword arguments to pass to the :attr:`type` callable.
        :return: The value of the retrieved environment variable.

        .. code-block::
            :caption: Using SingleEnvVar to fetch a value from an environment variable, with additional keyword arguments.

            from dataclasses import dataclass

            def parse_users(value: str, *, reverse: bool=False) -> list[str]:
                return sorted(value.split(','), reverse=reverse)

            users_ev = env_var("USERNAMES", type=parse_users)

            if desc:
                users = users_ev.get(reverse=True)  # will return a list of usernames sorted in reverse order
            else:
                users = users_ev.get()  # will return a list of usernames sorted in ascending order


.. class:: SchemaEnvVar

    An :class:`EnvVar` subclass that interfaces with a multiple environment variables, combining them into a single
    object.

    When the value is retrieved, all its :attr:`args` and :attr:`pos_args` are retrieved, and are then used as keyword variables on the
    EnvVar's :attr:`type`.

    Users can also supply keyword arguments to the :meth:`get` method, which will be supplied to the :attr:`type` in addition/instead of
    the child EnvVars.

    .. property:: type
        :type: collections.abc.Callable[..., T]

        The factory callable that will be used to create the object. (read only)

    .. property:: args
        :type: collections.abc.Mapping[str, EnvVar]

        The mapping of keyword arguments to :class:`EnvVar` objects. (read only)

    .. property:: pos_args
        :type: typing.Sequence[EnvVar]

        The sequence of positional arguments to the :attr:`type` callable. (read only)

    .. attribute:: on_partial
        :type: T | as_default | missing | discard | envvar.Factory[T]

        This attribute dictates how the EnvVar should behave when only some of the keys are explicitly present (i.e.
        When only some of the expected environment variables exist in the environment).

        * If set to :data:`as_default`, the EnvVar's :attr:`~EnvVar.default` will be returned.

          .. note::

            The EnvVar's :attr:`~EnvVar.default` must not be :data:`missing` if this option is used.

        * If set to :data:`missing`, a :exc:`~exceptions.MissingEnvError` will be raised, even if the EnvVar's
          :attr:`~EnvVar.default` is set.
        * If set to :class:`~envvar.Factory`, the factory will be called to create the value of the EnvVar.
        * If set to a value, that value will be returned.

    .. method:: get(**kwargs)->T

        Return the value of the environment variable. The value will be created by calling the :attr:`type` callable
        with the values of all the child EnvVars as keyword arguments, and the values of the ``kwargs`` parameter as
        additional keyword arguments.

        :param kwargs: Additional keyword arguments to pass to the :attr:`type` callable.
        :return: The value of the environment variable.

        .. code-block::
            :caption: Using SchemaEnvVar to create a class from multiple environment variables, with additional keyword arguments.

            from dataclasses import dataclass

            @dataclass
            class User:
                name: str
                age: int
                height: int

            user_ev = env_var("USER_", type=User,
                              args={'name': env_var('NAME', type=str),
                                    'age': env_var('AGE', type=int)})

            user_ev.get(age=20, height=168) # will return a User object with the name taken from the environment variables,
            # but with the age and height overridden by the keyword arguments.

.. class:: Factory(callback: collections.abc.Callable[[], T])

    A wrapped around a callable, indicating that the callable should be used as a factory for creating objects, rather than
    as a normal object.

    .. attribute:: callback
        :type: collections.abc.Callable[[], T]

        The callable that will be used to create the object.