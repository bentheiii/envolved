Constants
==================

Runtime constants for the envolved library

.. py:currentmodule:: envvar

.. py:data:: missing
    :type: object

    Used to indicate that an EnvVar has no default value. Can also be used in :attr:`~envvar.SchemaEnvVar.on_partial`
    to specify that an error should be raised on partial environments.

.. py:data:: as_default
    :type: object

    Used in :attr:`~envvar.SchemaEnvVar.on_partial` to specify that the default should be returned on partial
    environments.

.. py:data:: no_patch
    :type: object

    Used in :attr:`~envvar.EnvVar.monkeypatch` to specify that the EnvVar should not be patched.

.. py:data:: discard
    :type: object

    When returned by child env vars of :class:`~envvar.SchemaEnvVar`, the value, and argument, will be discarded. If
    a positional argument returns this value, all positional arguments after it will also be discarded.