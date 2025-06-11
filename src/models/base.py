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
    UNKNOWN = "Unknown"


class SeverityLevelEnum(str, Enum):
    CRITICAL = "Sev1-Critical"
    HIGH = "Sev2-High"
    MEDIUM = "Sev3-Medium"
    LOW = "Sev4-Low"
    INFORMATIONAL = "Sev5-Informational"


class ActionItemStatusEnum(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class UserRoleEnum(str, Enum):
    SRE = "sre"
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    INCIDENT_COMMANDER = "incident_commander"


class RolesEnum(str, Enum):
    QA_LEAD = "QA Lead"
    SRE_LEAD = "SRE Lead"
    BE_LEAD = "Back-end Lead"
    FE_LEAD = "Front-end Lead"
    DEVOPS_LEAD = "DevOps Lead"
    PRODUCT_OWNER = "Product Owner"
    DEPARTMENT_HEAD = "Department Head"
    ENGINEERING_MANAGER = "Engineering Manager"


class AffectedItemEnum(str, Enum):
    API = "API"
    DATABASE = "Database"
    INFRASTRUCTURE = "Infrastructure"
    NETWORK = "Network"
    APPLICATION = "Application"
    CUSTOMER_DATA = "Customer Data"
    SECURITY = "Security"
    EXTERNAL_SERVICE = "External Service"


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
