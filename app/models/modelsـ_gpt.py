from typing import List, Annotated
from uuid import UUID, uuid4
from datetime import datetime, date, timezone
from enum import Enum
from pydantic import EmailStr, SecretStr
from sqlmodel import Field, Relationship, SQLModel

# Enums


class SeverityEnum(str, Enum):
    severity_l1 = "Severity Level 1"
    severity_l2 = "Severity Level 2"
    severity_l3 = "Severity Level 3"
    severity_l4 = "Severity Level 4"
    severity_l5 = "Severity Level 5"


class StatusEnum(str, Enum):
    open = "Open"
    doing = "Doing"
    resolved = "Resolved"


class UserRoleEnum(str, Enum):
    admin = "Admin"
    team = "Team"
    viewer = "Viewer"


# Base with UUID primary key
class BaseEntityID(SQLModel):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]


# Base for incident-related entities
class BaseIncidentEntity(SQLModel, table=False):
    incident_id: Annotated[UUID, Field(foreign_key="incident.id")]
    incident: "Incident" = Relationship()


# Base for postmortem-related entities
class BasePostmortemEntity(SQLModel, table=False):
    postmortem_id: Annotated[UUID, Field(foreign_key="postmortem.id")]
    postmortem: "PostMortem" = Relationship()


# User model
class User(BaseEntityID, table=True):
    username: Annotated[str, Field(index=True, unique=True)]
    full_name: str | None = None
    email: Annotated[EmailStr, Field(index=True, unique=True)]
    hashed_password: Annotated[SecretStr, Field(
        sa_column_kwargs={"nullable": False})]
    is_active: Annotated[bool, Field(default=True)]
    is_superuser: Annotated[bool, Field(default=False)]
    role: Annotated[UserRoleEnum, Field(default=UserRoleEnum.viewer)]

    # Email verification
    is_email_verified: Annotated[bool, Field(default=False)]
    email_verification_token: str | None = None
    email_verified_at: datetime | None = None

    # Password reset
    reset_token: str | None = None
    reset_token_expires: datetime | None = None

    # Soft delete
    is_deleted: Annotated[bool, Field(default=False)]
    deleted_at: datetime | None = None

    # Profile fields
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None

    # Last login
    last_login_at: datetime | None = None
    last_login_ip: str | None = None

    # Relationships
    incidents_commander: List["Incident"] = Relationship(
        back_populates="commander")
    timeline_entries: List["TimelineEntry"] = Relationship(
        back_populates="owner_user")
    action_items: List["ActionItem"] = Relationship(
        back_populates="owner_user")
    approvals: List["Approval"] = Relationship(
        back_populates="approver")
    approved_incidents: List["Incident"] = Relationship(
        back_populates="approvers", link_model="Approval")
    approved_postmortems: List["PostMortem"] = Relationship(
        back_populates="approvers", link_model="Approval")


# Link model for richer related links
class Link(SQLModel):
    title: str
    url: str


# Incident metadata separated as its own model
class IncidentDetails(BaseEntityID, BaseIncidentEntity, table=True):
    title: str
    severity: SeverityEnum
    status: StatusEnum
    summary: str
    long_term_measures: Annotated[List[str] | None, Field(default=None)]
    related_links: Annotated[List[Link] | None, Field(default=None)]
    detected_by_id: Annotated[UUID | None, Field(default=None)]
    detected_by_name: Annotated[str | None, Field(default=None)]
    date_detected: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc))]
    resolution_time: Annotated[datetime | None, Field(default=None)]

    incident: Annotated["Incident", Relationship(back_populates="metadata")]


# Incident model
class Incident(BaseEntityID, table=True):

    metadata: Annotated[IncidentDetails | None, Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False})]

    commander_id: Annotated[UUID, Field(foreign_key="user.id")]

    commander: Annotated[User, Relationship(
        back_populates="incidents_commander")]

    services: List["ServiceAffected"] = Relationship(back_populates="incident")

    regions: List["RegionAffected"] = Relationship(back_populates="incident")

    customer_impacts: List["CustomerImpact"] = Relationship(
        back_populates="incident")

    business_impacts: List["BusinessImpact"] = Relationship(
        back_populates="incident")

    shallow_rca: Annotated["ShallowRCA" | None, Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False})]

    timeline: List["TimelineEntry"] = Relationship(back_populates="incident")

    communications: List["CommunicationLog"] = Relationship(
        back_populates="incident")

    postmortem: Annotated["PostMortem" | None, Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False})]

    approvals: List["Approval"] = Relationship(back_populates="incident")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

# Affected services and regions


class ServiceAffected(BaseEntityID, BaseIncidentEntity, table=True):
    service_name: str
    incident: Annotated["Incident", Relationship(back_populates="services")]


class RegionAffected(BaseEntityID, BaseIncidentEntity, table=True):
    region: str
    incident: Annotated["Incident", Relationship(back_populates="regions")]

# Impacts


class CustomerImpact(BaseEntityID, BaseIncidentEntity, table=True):
    description: str
    incident: Annotated["Incident", Relationship(
        back_populates="customer_impacts")]


class BusinessImpact(BaseEntityID, BaseIncidentEntity, table=True):
    description: str
    incident: Annotated["Incident", Relationship(
        back_populates="business_impacts")]

# Shallow root cause analysis


class ShallowRCA(BaseEntityID, BaseIncidentEntity, table=True):
    what_happened: str
    why_it_happened: str
    technical_cause: str
    detection_mechanism: str
    incident: Annotated["Incident", Relationship(back_populates="shallow_rca")]

# Timeline of events


class TimelineEntry(BaseEntityID, BaseIncidentEntity, table=True):
    time: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc))]
    event: str
    owner_id: Annotated[UUID, Field(foreign_key="user.id")]
    incident: Annotated["Incident", Relationship(back_populates="timeline")]
    owner_user: Annotated[User, Relationship(
        back_populates="timeline_entries")]

# Communication logs


class CommunicationLog(BaseEntityID, BaseIncidentEntity, table=True):
    time: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc))]
    channel: str
    message: str
    incident: Annotated["Incident", Relationship(
        back_populates="communications")]

# Postmortem and its parts


class PostMortem(BaseEntityID, BaseIncidentEntity, table=True):
    incident: Annotated["Incident", Relationship(back_populates="postmortem")]
    approvals: Annotated[List["Approval"],
                         Relationship(back_populates="postmortem")]
    action_items: Annotated[List["ActionItem"],
                            Relationship(back_populates="postmortem")]
    metadata: Annotated["PostmortemMetadata" | None, Relationship(
        back_populates="postmortem", sa_relationship_kwargs={"uselist": False})]
    deep_rca: Annotated["DeepRCA" | None, Relationship(
        back_populates="postmortem", sa_relationship_kwargs={"uselist": False})]
    contributing_factors: Annotated[List["ContributingFactor"], Relationship(
        back_populates="postmortem")]
    lessons_learned: Annotated[List["LessonLearned"],
                               Relationship(back_populates="postmortem")]


class PostmortemMetadata(BasePostmortemEntity, table=True):
    content: str
    postmortem: Annotated[PostMortem, Relationship(back_populates="metadata")]


class DeepRCA(BasePostmortemEntity, table=True):
    content: str
    postmortem: Annotated[PostMortem, Relationship(back_populates="deep_rca")]


class ContributingFactor(BasePostmortemEntity, table=True):
    content: str
    postmortem: Annotated[PostMortem, Relationship(
        back_populates="contributing_factors")]


class LessonLearned(BasePostmortemEntity, table=True):
    content: str
    postmortem: Annotated[PostMortem, Relationship(
        back_populates="lessons_learned")]

# Unified Approval


class Approval(BaseEntityID, table=True):
    incident_id: Annotated[UUID | None, Field(
        default=None, foreign_key="incident.id")]
    postmortem_id: Annotated[UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
    approver_id: Annotated[UUID, Field(foreign_key="user.id")]
    approved_at: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc))]
    comment: Annotated[str | None, Field(default=None)]
    incident: Annotated["Incident" | None,
                        Relationship(back_populates="approvals")]
    postmortem: Annotated["PostMortem" | None,
                          Relationship(back_populates="approvals")]
    approver: Annotated[User, Relationship(back_populates="approvals")]

# Action items


class ActionItem(BasePostmortemEntity, table=True):
    task: str
    owner_id: Annotated[UUID, Field(foreign_key="user.id")]
    due_date: Annotated[date, Field(default_factory=date.today)]
    status: StatusEnum
    postmortem: Annotated[PostMortem, Relationship(
        back_populates="action_items")]
    owner_user: Annotated[User, Relationship(back_populates="action_items")]
