"""KeepCloud exception classes."""


class KCError(Exception):
    """Generic errors."""

    def __init__(self, msg):
        Exception.__init__(self)
        self.msg = msg

    def __str__(self):
        return self.msg


class KCConfigError(KCError):
    """Config related errors."""
    pass


class KCRuntimeError(KCError):
    """Generic runtime errors."""
    pass


class KCArgumentError(KCError):
    """Argument related errors."""
    pass
