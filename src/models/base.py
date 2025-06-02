from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum
from typing import Annotated

from sqlmodel.sql import func
from sqlmodel import SQLModel, Field, Column, DateTime


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


class BaseEntity(SQLModel):
    id: Annotated[
        UUID,
        Field(
            default_factory=uuid4,
            primary_key=True,
            index=True,
            nullable=False
        )
    ]
    created_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(timezone.utc),
            nullable=False,
            sa_column=Column(
                DateTime(timezone=True),
                server_default=func.now()
            )
        )]
    updated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(timezone.utc),
            nullable=False,
            sa_column=Column(
                DateTime(timezone=True),
                server_default=func.now(),
                onupdate=func.now()
            )
        )]
