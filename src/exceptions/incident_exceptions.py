from typing import Any

from src.exceptions.common_exceptions import (
    ResourceNotFoundException,
    InvalidOperationException,
)
from src.models.incident import (
    IncidentStatusEnum
)


class IncidentNotFoundException(
    ResourceNotFoundException
):
    """
    Raised specifically when an
    incident is not found.
    Inherits from the general
    ResourceNotFoundException.
    """

    def __init__(
            self,
            identifier: Any = None
    ):
        super().__init__(
            resource_name="Incident",
            identifier=identifier
        )


class InvalidStatusTransitionException(
    InvalidOperationException
):
    """
    Raised when an incident status transition
    is not allowed based on business rules.
    """

    def __init__(
            self,
            from_status: IncidentStatusEnum,
            to_status: IncidentStatusEnum
    ):
        self.from_status = from_status
        self.to_status = to_status
        detail = (
            "Cannot transition incident status"
            f"from '{from_status.value}'"
            f" to '{to_status.value}'."
        )
        super().__init__(detail=detail)


class IncidentAlreadyResolvedException(
        InvalidOperationException
):
    """
    Raised when an operation is attempted
    on an already resolved incident.
    """

    def __init__(
            self,
            detail: str = (
                "Operation not permitted"
                "on a resolved incident."
            )
    ):
        super().__init__(detail=detail)
