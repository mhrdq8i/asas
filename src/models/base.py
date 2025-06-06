from datetime import datetime, timezone
from uuid import UUID, uuid4
from enum import Enum
from typing import Annotated

from sqlalchemy.sql import func
from sqlmodel import SQLModel, Field, DateTime


class IncidentStatusEnum(str, Enum):
    OPEN = "Open"
    DOING = "Doing"
    RESOLVED = "Resolved"


class SeverityLevelEnum(str, Enum):
    CRITICAL = "Sev-1 - Critical"
    HIGH = "Sev-2 - High"
    MEDIUM = "Sev-3 - Medium"
    LOW = "Sev-4 - Low"
    INFORMATIONAL = "Sev-5 - Informational"


class ActionItemStatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class UserRoleEnum(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    INCIDENT_COMMANDER = "incident_commander"
    SRE = "sre"


class RolesEnum(str, Enum):
    INCIDENT_LEAD = "Incident Lead"
    ENGINEERING_MANAGER = "Engineering Manager"
    PRODUCT_OWNER = "Product Owner"
    SRE_LEAD = "SRE Lead"
    QA_LEAD = "QA Lead"
    DEPARTMENT_HEAD = "Department Head"


class BaseEntity(SQLModel):
    """
    It provides common fields for other table models.
    """
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
            # This is for Pydantic validation
            nullable=False,
            # Specify SQLAlchemy type
            sa_type=DateTime(timezone=True),
            # Pass nullable to Column
            sa_column_kwargs={
                "server_default": func.now(),
                "nullable": False
            }
        )]
    updated_at: Annotated[
        datetime,
        Field(
            default_factory=lambda: datetime.now(timezone.utc),
            # This is for Pydantic validation
            nullable=False,
            # Specify SQLAlchemy type
            sa_type=DateTime(timezone=True),
            # Pass nullable to Column
            sa_column_kwargs={
                "server_default": func.now(),
                "onupdate": func.now(),
                "nullable": False
            }
        )]
