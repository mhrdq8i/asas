from typing import Any

from fastapi import status

from src.exceptions.base_exceptions import AppException
from src.exceptions.common_exceptions import (
    ResourceNotFoundException,
    InvalidOperationException,
)


class AuthenticationFailedException(AppException):
    """
    Raised when authentication fails
    (e.g., incorrect username/password, inactive user).
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
    Raised when an authenticated user
    does not have sufficient permissions
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


class UserNotFoundException(ResourceNotFoundException):
    """
    Raised specifically when a user is not found.
    Allows for a custom detail message.
    """

    # FIX: Added 'detail' parameter to allow custom messages.

    def __init__(
            self,
            identifier: Any = None,
            detail: str | None = None
    ):
        super().__init__(
            resource_name="User",
            identifier=identifier
        )
        if detail:
            # If a custom detail is provided,
            # override the default message.
            self.detail = detail


class UserAlreadyDeletedException(InvalidOperationException):
    """
    Raised when an operation is attempted
    on an already soft-deleted user.
    """

    def __init__(
            self,
            detail: str = "User is already soft-deleted."
    ):
        super().__init__(detail=detail)


class CannotDeleteActiveCommanderException(InvalidOperationException):
    """
    Raised when attempting to delete a user
    who is an active incident commander.
    """

    def __init__(
            self,
            detail: str = (
                "User is an active incident "
                "commander and cannot be deleted."
            )
    ):
        super().__init__(detail=detail)
