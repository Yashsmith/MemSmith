"""MemSmith exception hierarchy."""


class MemSmithError(Exception):
    """Base exception for the package."""


class MemSmithTimeoutError(MemSmithError):
    """Raised when a wait or lock acquisition exceeds its timeout."""


class LockConflictError(MemSmithError):
    """Raised when a lock is already held by another agent."""
