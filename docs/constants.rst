Constants
==================

Runtime constants for the envolved library

.. py:currentmodule:: basevar

.. py:data:: missing
    :type: object

    Used to indicate that an EnvVar has no default value. Can also be used in :attr:`~basevar.SchemaEnvVar.on_partial`
    to specify that an error should be raised on partial environments.

.. py:data:: as_default
    :type: object

    Used in :attr:`~basevar.SchemaEnvVar.on_partial` to specify that the default should be returned on partial
    environments.

.. py:data:: no_patch
    :type: object

    Used in :attr:`~basevar.EnvVar.monkeypatch` to specify that the EnvVar should not be patched.