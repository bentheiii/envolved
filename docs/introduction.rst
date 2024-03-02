Introduction
===============
Envolved is a python library that makes reading and parsing environment variables easy.

.. code-block::

    from envolved import *

    # specify an environment variable that automatically converts to an int, and defaults to 10
    cache_timeout_env_var = env_var('CACHE_TIMEOUT', type=int, default=10)

    # to retrieve its value we just perform:
    cache_timeout: int = cache_timeout_env_var.get()

    # We can get a little fancier with more advanced environment variables
    @dataclass
    class ConnectionInfo:
        hostname: str
        port: int
        api_token: str
        use_ssl: bool

    # specify an environment variable that automatically converts to a ConnectionInfo, by drawing
    # from multiple environment variables
    connection_info_env_var = env_var('CONNECTION_INFO_', type=ConnectionInfo, args={
        'hostname': env_var('HOSTNAME', type=str),  # note the prefix, we will look for the host
                                                    # name under the environment variable
                                                    # CONNECTION_INFO_HOSTNAME
        'port': inferred_env_var('PORT'),  # you can omit the type of the argument for many classes
        'api_token': env_var('API_TOKEN', type=str, default=None),
        'use_ssl': env_var('USE_SSL', type=bool, default=False)
    })

    # to retrieve its value we just perform:
    connection_info: ConnectionInfo = connection_info_env_var.get()

Envolved cuts down on boilerplate and allows for more reusable code.

.. code-block::

    # If we to accept connection info for another API, we don't need to repeat ourselves

    secondary_connection_info_env_var = connection_info_env_var.with_prefix('SECONDARY_')

    # the hostname for our secondary connection info is now SECONDARY_CONNECTION_INFO_HOSTNAME

