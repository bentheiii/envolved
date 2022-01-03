Creating EnvVars
=========================================================

.. module:: envvar

.. function:: env_var(key: str, *, type: collections.abc.Callable[[str], T], default: T | missing = missing,\
            description: str | None = None, \
            validators: collections.abc.Iterable[collections.abc.Callable[[T], T]] = (), \
            case_sensitive: bool = False, strip_whitespaces: bool = True) -> basevar.SingleEnvVar[T]

    Creates an EnvVar that reads from one environment variable.

    :param key: The key of the environment variable.
    :param type: A callable to use to parse the string value of the environment variable.
    :param default: The default value of the EnvVar if the environment variable is missing. If unset, an exception will
     be raised if the environment variable is missing.
    :param description: A description of the EnvVar. See :ref:`describing:Describing Environment Variables`.
    :param validators: A list of callables to validate the value of the EnvVar. Validators can be added to the EnvVar
     after it is created with :func:`~basevar.EnvVar.validator`.
    :param case_sensitive: Whether the key of the EnvVar is case sensitive.
    :param strip_whitespaces: Whether to strip whitespaces from the value of the environment variable before parsing it.

.. function:: env_var(key: str, *, type: collections.abc.Callable[..., T], default: T | missing = missing, \
            args: Dict[str, basevar.EnvVar | AutoTypedEnvVar], \
            description: str | None = None,  \
            validators: collections.abc.Iterable[collections.abc.Callable[[T], T]] = (), \
            on_partial: T | missing | as_default = missing) -> basevar.SchemaEnvVar[T]:
    :noindex:

    Creates an EnvVar that reads from multiple environment variables.

    :param key: The key of the environment variable. This will be a common prefix applied to all environment variables.
    :param type: A callable to call with ``args`` to create the EnvVar value.
    :param default: The default value of the EnvVar if the environment variable is missing. If unset, an exception will
     be raised if the environment variable is missing.
    :param args: A dictionary of EnvVars to to retrieve and use as arguments to ``type``. Arguments can be
     :ref:`autotyped <autotype:Autotype- Skip specifying the type>` in some cases.
    :param description: A description of the EnvVar. See :ref:`describing:Describing Environment Variables`.
    :param validators: A list of callables to validate the value of the EnvVar. Validators can be added to the EnvVar
     after it is created with :func:`~basevar.EnvVar.validator`.
    :param on_partial: The value to use if the EnvVar is partially missing. See
     :attr:`~basevar.SchemaEnvVar.on_partial`.