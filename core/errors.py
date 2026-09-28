class CoreError(Exception):
    """Base error for the Abqaryno core."""


class InvalidTransition(CoreError):
    """Raised when a state transition is not allowed."""


class MissingInformation(CoreError):
    """Raised when required information is not available."""


class ConflictingInformation(CoreError):
    """Raised when the available information conflicts."""


class InvalidDecision(CoreError):
    """Raised when a decision is incomplete or invalid."""


class CoreStopped(CoreError):
    """Raised when execution reaches a terminal stopped state."""


class CoreCompleted(CoreError):
    """Raised when execution reaches the completed state."""
