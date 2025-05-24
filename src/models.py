import uuid
from datetime import datetime, date
from typing import List, Annotated, Optional
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship  # type: ignore
from pydantic import EmailStr, SecretStr
from sqlalchemy import Column, Text, String

# --------------- Enums and Literals ---------------


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

# --------------- Base Entity (Not a table itself) ---------------


class BaseEntity(SQLModel):
    id: Annotated[uuid.UUID, Field(
        default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)]

# --------------- User Model ---------------


class User(BaseEntity, table=True):
    username: Annotated[str, Field(index=True, unique=True, nullable=False)]
    full_name: Annotated[str | None, Field(default=None)]
    email: Annotated[EmailStr, Field(index=True, unique=True, nullable=False)]
    hashed_password: Annotated[SecretStr, Field(
        sa_column=Column(String, nullable=False))]
    is_active: Annotated[bool, Field(default=True, nullable=False)]
    is_superuser: Annotated[bool, Field(default=False, nullable=False)]
    role: Annotated[UserRoleEnum, Field(
        default=UserRoleEnum.viewer, nullable=False)]

    is_email_verified: Annotated[bool, Field(default=False, nullable=False)]
    email_verification_token: Annotated[str |
                                        None, Field(default=None, index=True)]
    email_verified_at: Annotated[datetime | None, Field(default=None)]

    reset_token: Annotated[str | None, Field(default=None, index=True)]
    reset_token_expires: Annotated[datetime | None, Field(default=None)]

    is_deleted: Annotated[bool, Field(
        default=False, nullable=False, index=True)]
    deleted_at: Annotated[datetime | None, Field(default=None)]

    avatar_url: Annotated[str | None, Field(default=None)]
    bio: Annotated[str | None, Field(default=None, sa_column=Column(Text))]
    timezone: Annotated[str | None, Field(default=None)]

    last_login_at: Annotated[datetime | None, Field(default=None)]
    last_login_ip: Annotated[str | None, Field(default=None)]

    incidents_commanded: List["IncidentMetadata"] = Relationship(
        back_populates="commander")
    timeline_events_owned: List["TimelineEvent"] = Relationship(
        back_populates="owner_user")
    action_items_owned: List["ActionItem"] = Relationship(
        back_populates="owner_user")
    sign_offs_made: List["SignOffEntry"] = Relationship(
        back_populates="approver_user")
    post_mortem_approvals_made: List["PostMortemApproval"] = Relationship(
        back_populates="approver_user")

# --------------- Main Incident Table ---------------


class Incident(BaseEntity, table=True):
    incident_metadata: Optional["IncidentMetadata"] = Relationship(
        back_populates="incident_ref", sa_relationship_kwargs={"uselist": False}
    )
    impacts: Optional["Impacts"] = Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False}
    )
    shallow_rca: Optional["ShallowRCA"] = Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False}
    )
    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False}
    )
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False}
    )

    affected_services: List["AffectedService"] = Relationship(
        back_populates="incident")
    affected_regions: List["AffectedRegion"] = Relationship(
        back_populates="incident")
    timeline_events: List["TimelineEvent"] = Relationship(
        back_populates="incident")
    communication_log_entries: List["CommunicationLogEntry"] = Relationship(
        back_populates="incident")
    sign_offs: List["SignOffEntry"] = Relationship(back_populates="incident")

# --------------- Incident Metadata ---------------


class IncidentMetadata(BaseEntity, table=True):
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", unique=True, index=True, description="Links to the specific Incident record's id")]
    title: Annotated[str, Field(description="Main incident title")]
    severity: Annotated[SeverityLevel, Field(
        description="Severity level of the incident")]
    date_time_detected_utc: Annotated[datetime, Field(
        description="Date/Time Detected (UTC)")]
    detected_by: Annotated[str, Field(sa_column=Column(
        Text), description="Source of detection, e.g., Prometheus Alert or User ID")]
    commander_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="user.id", index=True)]
    commander: Optional["User"] = Relationship(
        back_populates="incidents_commanded")
    status: Annotated[IncidentStatus, Field(
        default=IncidentStatus.OPEN, description="Current status of the incident")]
    summary: Annotated[str, Field(sa_column=Column(
        Text), description="Short description of the incident")]
    incident_ref: Optional["Incident"] = Relationship(
        back_populates="incident_metadata")

# --------------- Base for Affected Items (Not a table itself) ---------------


class AffectedItemBase(BaseEntity):
    name: Annotated[str, Field(
        description="Name of the affected item (e.g., service, region, network)")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", index=True)]

# --------------- Affects ---------------


class AffectedService(AffectedItemBase, table=True):
    incident: Optional["Incident"] = Relationship(
        back_populates="affected_services")


class AffectedRegion(AffectedItemBase, table=True):
    incident: Optional["Incident"] = Relationship(
        back_populates="affected_regions")

# --------------- Impacts ---------------


class Impacts(BaseEntity, table=True):
    customer_impact: Annotated[str, Field(sa_column=Column(
        Text), description="Details of customer impact")]
    business_impact: Annotated[str, Field(sa_column=Column(
        Text), description="Details of business impact, e.g., estimated lost revenue")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", unique=True, index=True)]
    incident: Optional["Incident"] = Relationship(back_populates="impacts")

# --------------- Root Cause Analysis (Shallow RCA) ---------------


class ShallowRCA(BaseEntity, table=True):
    what_happened: Annotated[str, Field(sa_column=Column(
        Text), description="Description of what happened")]
    why_it_happened_points: Annotated[List[str], Field(default_factory=list, sa_column=Column(
        Text), description="List of reasons why it happened")]  # Explicit sa_column
    technical_cause: Annotated[List[str], Field(default_factory=list, sa_column=Column(
        Text), description="List of technical causes of the incident")]  # Explicit sa_column
    detection_mechanism: Annotated[List[str], Field(default_factory=list, sa_column=Column(
        Text), description="How the incident was detected")]  # Explicit sa_column
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", unique=True, index=True)]
    incident: Optional["Incident"] = Relationship(back_populates="shallow_rca")

# --------------- Timeline of Events ---------------


class TimelineEvent(BaseEntity, table=True):
    time_utc: Annotated[datetime, Field(
        description="Time of the event in UTC")]
    event_description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the event")]
    owner_user_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="user.id", index=True)]
    owner_user: Optional["User"] = Relationship(
        back_populates="timeline_events_owned")
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", index=True)]
    incident: Optional["Incident"] = Relationship(
        back_populates="timeline_events")

# --------------- Resolution & Mitigation ---------------


class ResolutionMitigation(BaseEntity, table=True):
    resolution_time_utc: Annotated[datetime | None, Field(
        default=None, description="Time the incident was resolved in UTC")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", unique=True, index=True)]
    incident: Optional["Incident"] = Relationship(
        back_populates="resolution_mitigation")
    short_term_remediation_steps: List["RemediationStep"] = Relationship(
        back_populates="resolution_mitigation")
    long_term_preventative_measures: List["LongTermPreventativeMeasure"] = Relationship(
        back_populates="resolution_mitigation")


class RemediationStep(BaseEntity, table=True):
    step_description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the remediation step")]
    resolution_mitigation_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="resolutionmitigation.id")]
    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="short_term_remediation_steps")


class LongTermPreventativeMeasure(BaseEntity, table=True):
    measure_description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the long-term preventative measure")]
    resolution_mitigation_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="resolutionmitigation.id")]
    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="long_term_preventative_measures")

# --------------- Communications Log ---------------


class CommunicationLogEntry(BaseEntity, table=True):
    time_utc: Annotated[datetime, Field(
        description="Time of the communication in UTC")]
    channel: Annotated[str, Field(
        description="Communication channel, e.g., Slack, Email, Status Page")]
    message: Annotated[str, Field(sa_column=Column(
        Text), description="Content of the communication")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", index=True)]
    incident: Optional["Incident"] = Relationship(
        back_populates="communication_log_entries")

# --------------- Sign-Off ---------------


class SignOffEntry(BaseEntity, table=True):
    role: Annotated[str, Field(
        description="Role of the approver at the time of sign-off")]
    approver_user_id: Annotated[uuid.UUID, Field(
        foreign_key="user.id", index=True, nullable=False)]
    approver_user: "User" = Relationship(back_populates="sign_offs_made")
    date_approved: Annotated[date, Field(description="Date of approval")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", index=True)]
    incident: Optional["Incident"] = Relationship(back_populates="sign_offs")

# --------------- Post-Mortem Main Table ---------------


class PostMortem(BaseEntity, table=True):
    post_mortem_status: Annotated[str, Field(
        description="Status of the post-mortem, e.g., Completed")]
    document_link: Annotated[str | None, Field(
        default=None, description="Link to the detailed post-mortem document if separate")]
    deep_rca_detailed_technical_cause: Annotated[str, Field(
        sa_column=Column(Text), description="In-depth technical cause from deep RCA")]
    incident_id: Annotated[uuid.UUID, Field(
        foreign_key="incident.id", unique=True, index=True)]
    incident: Optional["Incident"] = Relationship(back_populates="post_mortem")
    contributing_factors: List["ContributingFactor"] = Relationship(
        back_populates="post_mortem")
    lessons_learned: List["LessonLearned"] = Relationship(
        back_populates="post_mortem")
    action_items: List["ActionItem"] = Relationship(
        back_populates="post_mortem")
    approvals: List["PostMortemApproval"] = Relationship(
        back_populates="post_mortem")

# --------------- Post-Mortem Contributing Factors ---------------


class ContributingFactor(BaseEntity, table=True):
    factor_type: Annotated[str, Field(
        description="Type of factor, e.g., Process Gap, Tooling Gap")]
    description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the contributing factor")]
    post_mortem_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="contributing_factors")

# --------------- Post-Mortem Lessons Learned ---------------


class LessonLearned(BaseEntity, table=True):
    lesson_description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the lesson learned")]
    post_mortem_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="lessons_learned")

# --------------- Post-Mortem Action Items ---------------


class ActionItem(BaseEntity, table=True):
    task_description: Annotated[str, Field(sa_column=Column(
        Text), description="Description of the action item task")]
    owner_user_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="user.id", index=True)]
    owner_user: Optional["User"] = Relationship(
        back_populates="action_items_owned")
    due_date: Annotated[date, Field(
        description="Due date for the action item")]
    status: Annotated[ActionItemStatus, Field(
        default=ActionItemStatus.OPEN, description="Status of the action item")]
    post_mortem_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="action_items")

# --------------- Post-Mortem Approvals ---------------


class PostMortemApproval(BaseEntity, table=True):
    role: Annotated[str, Field(
        description="Role of the approver at the time of approval")]
    approver_user_id: Annotated[uuid.UUID, Field(
        foreign_key="user.id", index=True, nullable=False)]
    approver_user: "User" = Relationship(
        back_populates="post_mortem_approvals_made")
    approval_date: Annotated[date, Field(description="Date of approval")]
    post_mortem_id: Annotated[uuid.UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="approvals")


# Forward references update for relationships
User.model_rebuild()
Incident.model_rebuild()
IncidentMetadata.model_rebuild()
AffectedService.model_rebuild()
AffectedRegion.model_rebuild()
Impacts.model_rebuild()
ShallowRCA.model_rebuild()
TimelineEvent.model_rebuild()
ResolutionMitigation.model_rebuild()
RemediationStep.model_rebuild()
LongTermPreventativeMeasure.model_rebuild()
CommunicationLogEntry.model_rebuild()
SignOffEntry.model_rebuild()
PostMortem.model_rebuild()
ContributingFactor.model_rebuild()
LessonLearned.model_rebuild()
ActionItem.model_rebuild()
PostMortemApproval.model_rebuild()
