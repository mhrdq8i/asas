from typing import List, Annotated
from uuid import UUID, uuid4
from datetime import datetime, date
from enum import Enum
from sqlmodel import Field, Relationship, SQLModel


# Enums
class SeverityEnum(str, Enum):
    severity_1 = "Severity Level 1"
    severity_2 = "Severity Level 2"
    severity_3 = "Severity Level 3"
    severity_4 = "Severity Level 4"
    severity_5 = "Severity Level 5"


class StatusEnum(str, Enum):
    open = "Open"
    doing = "Doing"
    resolved = "Resolved"


class UserRoleEnum(str, Enum):
    superadmin = "Super Admin"
    admin = "Admin"
    viewer = "Viewer"


class BaseEntityWithID(SQLModel):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]


# User model for authentication/authorization
class User(BaseEntityWithID, table=True):
    username: Annotated[str, Field(index=True, unique=True)]
    full_name: str | None = None
    email: Annotated[str, Field(index=True, unique=True)]
    hashed_password: str
    is_active: Annotated[bool, Field(default=True)]
    is_superuser: Annotated[bool, Field(default=False)]
    role: Annotated[UserRoleEnum, Field(default=UserRoleEnum.viewer)]

    incidents_commander: List["Incident"] = Relationship(
        back_populates="commander")
    timeline_entries: List["TimelineEntry"] = Relationship(
        back_populates="owner_user")
    action_items: List["ActionItem"] = Relationship(
        back_populates="owner_user")


# Core Incident model
class Incident(BaseEntityWithID, table=True):
    title: str
    severity: SeverityEnum
    date_detected: datetime
    detected_by_id: UUID | None = None
    detected_by_name: str | None = None
    incident_commander_id: Annotated[UUID, Field(foreign_key="user.id")]
    status: StatusEnum
    summary: str
    related_links: str | None = None  # New field

    commander: User = Relationship(back_populates="incidents_commander")
    services: List["ServiceAffected"] = Relationship(back_populates="incident")
    regions: List["RegionAffected"] = Relationship(back_populates="incident")
    customer_impacts: List["CustomerImpact"] = Relationship(
        back_populates="incident")
    business_impacts: List["BusinessImpact"] = Relationship(
        back_populates="incident")
    shallow_rca: "ShallowRCA" | None = Relationship(
        back_populates="incident",
        sa_relationship_kwargs={"uselist": False}
    )
    timeline: List["TimelineEntry"] = Relationship(back_populates="incident")
    communications: List["CommunicationLog"] = Relationship(
        back_populates="incident")
    resolution_time: datetime | None = None
    long_term_measures: str | None = None
    postmortem: "PostMortem" | None = Relationship(
        back_populates="incident",
        sa_relationship_kwargs={"uselist": False}
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.detected_by_id and self.detected_by_name:
            raise ValueError(
                "Only one of detected_by_id or detected_by_name should be set."
            )
        if not self.detected_by_id and not self.detected_by_name:
            raise ValueError(
                "At least one of detected_by_id or detected_by_name must be set."
            )


# Abstract base for all incident-related entities
class BaseIncidentEntity(BaseEntityWithID, table=False):
    incident_id: Annotated[UUID, Field(foreign_key="incident.incident_id")]
    incident: "Incident" = Relationship()


# Affected entities
class ServiceAffected(BaseIncidentEntity, table=True):
    service_name: str
    incident: "Incident" = Relationship(back_populates="services")


class RegionAffected(BaseIncidentEntity, table=True):
    region: str
    incident: "Incident" = Relationship(back_populates="regions")


# Abstract base for impacts, extends incident entity with description
class BaseImpact(BaseIncidentEntity, table=False):
    description: str


class CustomerImpact(BaseImpact, table=True):
    incident: "Incident" = Relationship(back_populates="customer_impacts")


class BusinessImpact(BaseImpact, table=True):
    incident: "Incident" = Relationship(back_populates="business_impacts")


# Shallow root cause analysis
class ShallowRCA(BaseIncidentEntity, table=True):
    unique_shallow: Annotated[bool, Field(
        default=True)]  # enforce single record
    what_happened: str
    why_it_happened: str
    technical_cause: str
    detection_mechanism: str
    incident: "Incident" = Relationship(back_populates="shallow_rca")


# Timeline of events
class TimelineEntry(BaseIncidentEntity, table=True):
    time: datetime
    event: str
    owner_id: Annotated[UUID, Field(foreign_key="user.id")]
    incident: "Incident" = Relationship(back_populates="timeline")
    owner_user: User = Relationship(back_populates="timeline_entries")


# Communication logs
class CommunicationLog(BaseIncidentEntity, table=True):
    time: datetime
    channel: str
    message: str
    incident: "Incident" = Relationship(back_populates="communications")


# Post-mortem details
class PostMortem(BaseIncidentEntity, table=True):
    metadata: str | None = None
    deep_rca: str | None = None
    contributing_factors: str | None = None
    lessons_learned: str | None = None
    approvals: str | None = None
    incident: "Incident" = Relationship(back_populates="postmortem")
    action_items: List["ActionItem"] = Relationship(
        back_populates="postmortem")


# Action items for post-mortem
class ActionItem(BaseEntityWithID, table=True):
    postmortem_id: Annotated[int, Field(foreign_key="postmortem.id")]
    task: str
    owner_id: Annotated[UUID, Field(foreign_key="user.id")]
    due_date: date
    status: StatusEnum
    postmortem: "PostMortem" = Relationship(back_populates="action_items")
    owner_user: User = Relationship(back_populates="action_items")
