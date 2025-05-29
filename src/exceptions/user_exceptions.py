from typing import Any

from fastapi import status

from src.exceptions.base_exceptions import (
    AppException
)
from src.exceptions.common_exceptions import (
    ResourceNotFoundException
)


class AuthenticationFailedException(
    AppException
):
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


class InsufficientPermissionsException(
    AppException
):
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


class UserNotFoundException(
    ResourceNotFoundException
):
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
