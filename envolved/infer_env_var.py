from envolved.envvar import InferEnvVar, inferred_env_var

__all__ = ["InferEnvVar", "inferred_env_var"]

# this module is to preserved backwards compatibility

AutoTypedEnvVar = InferEnvVar  # alias for backwards compatibility
