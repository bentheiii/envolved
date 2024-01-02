Describing Environment Variables
===================================

Another feature of envolved is the ability to describe all EnvVars.

.. code-block::

    cache_time_ev = env_var('CACHE_TIME', type=int, default=3600, description='Cache time, in seconds')
    backlog_size_ev = env_var('BACKLOG_SIZE', type=int, default=100, description='Backlog size')
    logging_params_ev = env_var('LOGSTASH', type=SimpleNamespace, description='Logging parameters',
                                args={
                                    'host': env_var('_HOST', type=str),
                                    'port': env_var('_PORT', type=int),
                                    'level': env_var('_LEVEL', type=int, default=20),
                                })

    print('\n'.join(describe_env_vars()))

    # OUTPUT:
    # BACKLOG_SIZE: Backlog size
    # CACHE_TIME: Cache time, in seconds
    # Logging parameters:
    #   LOGSTASH_HOST
    #   LOGSTASH_LEVEL
    #   LOGSTASH_PORT

.. warning::

    The description feature is still experimental and may change in the future.

.. module:: describe

.. function:: describe_env_vars(**kwargs)->List[str]

    Returns a list of string lines that describe all the EnvVars. All keyword arguments are passed to
    :func:`textwrap.wrap` to wrap the lines.

    .. note::

        This function will include a description of every alive EnvVar. EnvVars defined in functions, for instance, will
        not be included.

Excluding EnvVars from the description
------------------------------------------

In some cases it is useful to exclude some EnvVars from the description. This can be done with the
:func:`exclude_from_description` function.

.. code-block::

    point_args = dict(
        x=env_var('_x', type=int, description='x coordinate'),
        y=env_var('_y', type=int, description='y coordinate')
    )  # point_args is a common argument set that we will provide to other envars.

    origin_ev = env_var('ORIGIN', type=Point, description='Origin point', args=point_args)
    destination_ev = env_var('DESTINATION', type=Point, description='Destination point', args=point_args)

    # but the problem is that now the env-vars defined in the original point_args dict will be included in the
    # description even though we never read them. We exclude them like this:

    exclude_from_description(point_args)

.. function:: exclude_from_description(env_vars: EnvVar | collections.abc.Iterable[EnvVar] | \
                                       collections.abc.Mapping[Any, EnvVar])

    Mark a given EnvVar or collection of EnvVars from the env-var description.

    :param env_vars: A single EnvVar or a collection of EnvVars to exclude from the description, can also be a mapping
                     of EnvVar names to EnvVars.
    :return: `env_vars`, to allow for piping.

.. class:: EnvVarsDescription(env_vars: collections.abc.Iterable[EnvVar] | None)

    A class that allows for more fine-grained control over the description of EnvVars.

    :param env_vars: A collection of EnvVars to describe. If None, all alive EnvVars will be described. If the collection
                     includes two EnvVars, one which is a parent of the other, only the parent will be described.

    .. method:: flat()->FlatEnvVarsDescription

        Returns a flat description of the EnvVars. 
    
    .. method:: nested()->NestedEnvVarsDescription

        Returns a nested description of the EnvVars.

.. class:: FlatEnvVarsDescription

    A flat representation of the EnvVars description. Only single-environment variable EnvVars (or single-environment variable children of envars) will be described.

    .. method:: wrap_sorted(*, unique_keys: bool = True, **kwargs)->List[str]

        Returns a list of string lines that describe the EnvVars, sorted by their environment variable key.

        :param unique_keys: If True, and if any EnvVars share an environment variable key, they will be combined into one description.
        :param kwargs: Keyword arguments to pass to :func:`textwrap.wrap`.
        :return: A list of string lines that describe the EnvVars.
    
    .. method:: wrap_grouped(**kwargs)->List[str]

        Returns a list of string lines that describe the EnvVars, sorted by their environment variable key, but env-vars that are used by the same schema will appear together.

        :param kwargs: Keyword arguments to pass to :func:`textwrap.wrap`.
        :return: A list of string lines that describe the EnvVars.

.. class:: NestedEnvVarsDescription
    
    A nested representation of the EnvVars description. All EnvVars will be described.

    .. method:: wrap(indent_increment: str = ..., **kwargs)->List[str]

        Returns a list of string lines that describe the EnvVars in a tree structure.

        :param indent_increment: The string to use to increment the indentation of the description with each level. If not provided,
         will use the keyword argument "subsequent_indent" from :func:`textwrap.wrap`, if provided. Otherwise, will use a single space.
        :param kwargs: Keyword arguments to pass to :func:`textwrap.wrap`.
        :return: A list of string lines that describe the EnvVars.