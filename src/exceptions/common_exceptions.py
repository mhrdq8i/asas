from typing import Any

from fastapi import status

from src.exceptions.base_exceptions import (
    AppException
)


class ResourceNotFoundException(
    AppException
):
    """
    Raised when a requested resource is not found.
    Can be subclassed for more specific not-found errors.
    """

    def __init__(
            self,
            resource_name: str = "Resource",
            identifier: Any = None
    ):
        # Store for potential use in error handler
        self.resource_name = resource_name
        self.identifier = identifier

        detail = f"{resource_name} not found."

        if identifier:
            detail = (
                f"{resource_name} with identifier "
                f"{identifier} not found."
            )

        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND
        )


class DuplicateResourceException(
    AppException
):
    """
    Raised when attempting to create
    a resource that already exists.
    """

    def __init__(
            self,
            detail: str = "Resource already exists"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_409_CONFLICT
        )


class InvalidOperationException(
    AppException
):
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


class InvalidInputException(
    AppException
):
    """
    Raised for invalid input that passes
    Pydantic validation but fails business logic.
    """

    def __init__(
        self,
        detail: str = "Invalid input provided"
    ):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
