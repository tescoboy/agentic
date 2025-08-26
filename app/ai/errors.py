"""AI provider error handling."""


class AIConfigError(Exception):
    """Raised when AI provider is not properly configured."""

    pass


class AIRequestError(Exception):
    """Raised when AI provider returns non-2xx or invalid responses."""

    pass


class AITimeoutError(Exception):
    """Raised when AI provider request times out."""

    pass
