from typing import Any

from fastapi import HTTPException, status


# --- Base Application Exception ---

class AppException(HTTPException):
    """
    Base class for custom application exceptions.
    This allows for a general way to catch application-specific errors.
    """

    def __init__(
        self,
        detail: str | None = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    ):
        self.detail = detail or "An application error occurred."
        self.status_code = status_code
        super().__init__(self.detail)


# --- Authentication / Authorization Exceptions ---

class AuthenticationFailedException(AppException):
    """
    Raised when authentication fails (e.g., incorrect username/password).
    """

    def __init__(
            self,
            detail: str = "Incorrect username or password"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class NotAuthenticatedException(AppException):
    """
    Raised when an operation requires
    authentication but no user is authenticated.
    """

    def __init__(
            self,
            detail: str = "Not authenticated"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class InsufficientPermissionsException(AppException):
    """
    Raised when an authenticated
    user does not have sufficient permissions
    to perform an action.
    """

    def __init__(
            self,
            detail: str = "Insufficient permissions"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )


# --- Resource / Data Related Exceptions ---

class ResourceNotFoundException(AppException):
    """
    Raised when a requested resource is not found.
    Can be subclassed for more specific
    not-found errors (e.g., UserNotFoundException).
    """

    def __init__(
            self,
            resource_name: str = "Resource",
            identifier: Any = None
    ):
        detail = f"{resource_name} not found."
        if identifier:
            detail = f"{resource_name} with identifier '{identifier}' not found."
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class UserNotFoundException(ResourceNotFoundException):
    """
    Raised specifically when a user is not found.
    """

    def __init__(
            self,
            identifier: Any = None
    ):
        super().__init__(
            resource_name="User",
            identifier=identifier
        )


class DuplicateResourceException(AppException):
    """
    Raised when attempting to create a resource that already exists
    (e.g., user with an existing email or username).
    """

    def __init__(
            self,
            detail: str = "Resource already exists"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


# --- Validation / Business Logic Exceptions ---

class InvalidOperationException(AppException):
    """
    Raised when an operation is invalid
    due to business logic constraints.
    """

    def __init__(
            self,
            detail: str = "Invalid operation"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidInputException(AppException):
    """
    Raised for invalid input that passes
    Pydantic validation but fails business logic.
    For Pydantic validation errors,
    FastAPI's RequestValidationError is typically used.
    """

    def __init__(
            self,
            detail: str = "Invalid input provided"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


# --- Configuration Errors (Potentially raised during startup if not handled by Pydantic) ---
# While Pydantic's Settings management usually raises pydantic.ValidationError for config issues,
# you might define a custom one if you have manual checks that could fail.
class ConfigurationError(AppException):
    """
    Raised for application configuration errors.
    """

    def __init__(
            self,
            detail: str = "Application configuration error"
    ):
        # Configuration errors are typically server-side issues, but might prevent startup
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# You can add more specific exceptions as your application grows.
# For example:
# class EmailSendingException(AppException):
#     def __init__(self, detail: str = "Failed to send email"):
#         super().__init__(detail=detail, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
