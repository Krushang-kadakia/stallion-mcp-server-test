class StallionMCPError(Exception):
    """Base exception for Stallion MCP Server errors."""
    pass


class AuthenticationRequiredError(StallionMCPError):
    """Raised when an API requiring authentication is called without a valid session or token."""
    pass


class ProjectContextRequiredError(StallionMCPError):
    """Raised when an API requiring a projectToken is called before switching to a project context."""
    pass


class BackendAPIError(StallionMCPError):
    """Raised when the backend API returns an error response."""
    def __init__(self, status_code: int, message: str, details: str | None = None):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(f"Backend API Error ({status_code}): {message}")


class MutatingOperationForbiddenError(StallionMCPError):
    """Raised when an attempt to invoke a mutating endpoint is made."""
    pass
