from uuid import UUID, uuid4
from enum import Enum

from typing import Annotated

from sqlmodel import SQLModel, Field


class IncidentStatus(str, Enum):
    OPEN = "Open"
    DOING = "Doing"
    RESOLVED = "Resolved"


class SeverityLevel(str, Enum):
    CRITICAL = "Sev-1 - Critical"
    HIGH = "Sev-2 - High"
    MEDIUM = "Sev-3 - Medium"
    LOW = "Sev-4 - Low"
    INFORMATIONAL = "Sev-5 - Informational"


class ActionItemStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class UserRoleEnum(str, Enum):
    viewer = "viewer"
    editor = "editor"
    admin = "admin"
    incident_commander = "incident_commander"
    sre = "sre"


class BaseEntity(SQLModel, table=False):
    id: Annotated[
        UUID, Field(
            default_factory=uuid4,
            primary_key=True,
            index=True,
            nullable=False
        )
    ]
