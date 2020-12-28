class MissingEnvError(Exception):
    """
    An exception raised when looking up a missing environment variable without a default.
    """
    pass
