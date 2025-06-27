from typing import Any
from uuid import UUID

from src.exceptions.common_exceptions import (
    ResourceNotFoundException,
    InvalidOperationException,
    DuplicateResourceException
)


class PostMortemNotFoundException(
    ResourceNotFoundException
):
    """
    Raised specifically when a post-mortem is not found.
    """

    def __init__(self, identifier: Any = None):
        super().__init__(
            resource_name="PostMortem",
            identifier=identifier
        )


class PostMortemAlreadyExistsException(
    DuplicateResourceException
):
    """
    Raised when attempting to create a post-mortem
    for an incident that already has one.
    """

    def __init__(self, incident_id: UUID):
        detail = (
            "A post-mortem already exists for "
            f"incident with ID '{incident_id}'."
        )
        super().__init__(detail=detail)


class IncidentNotResolvedException(
    InvalidOperationException
):
    """
    Raised when trying to create a post-mortem
    for an incident that is not yet resolved.
    """

    def __init__(self, incident_id: UUID):
        detail = (
            "Cannot create post-mortem. "
            "Incident with ID "
            f"'{incident_id}' "
            "is not yet resolved."
        )
        super().__init__(detail=detail)
