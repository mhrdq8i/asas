from uuid import UUID
from datetime import (
    datetime,
    date
)
from typing import (
    Optional,
    List
)

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import (
    JSONB
)
from sqlmodel import (
    Relationship,
    Field,
    DateTime
)

from src.models.base import (
    BaseEntity,
    SeverityLevelEnum,
    IncidentStatusEnum
)
from src.models.user import User
from src.models.postmortem import (
    PostMortem
)


class Incident(BaseEntity, table=True):
    __tablename__ = "incidents"

    # --- Mandatory Relationships ---
    # An Incident MUST have these components upon creation.
    profile: "IncidentProfile" = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    impacts: "Impacts" = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    shallow_rca: "ShallowRCA" = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )

    # --- Optional Relationships ---
    # These can be added later in the incident's lifecycle.
    resolution_mitigation: Optional[
        "ResolutionMitigation"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    postmortem: Optional["PostMortem"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )

    # --- List-based Relationships ---
    affected_services: List["AffectedService"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    affected_regions: List["AffectedRegion"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    timeline_events: List["TimelineEvent"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    communication_logs: List["CommunicationLog"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    sign_offs: List["SignOff"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )


# --- Incident Profile ---

class IncidentProfile(BaseEntity, table=True):
    __tablename__ = "incident_profile"

    # One-to-One relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="profile"
    )

    # --- Fields ---
    title: str = Field(max_length=255)
    status: IncidentStatusEnum = Field(
        default=IncidentStatusEnum.OPEN
    )
    severity: SeverityLevelEnum
    datetime_detected_utc: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True)
        )
    )
    detected_by: str = Field(
        sa_column=Column(JSONB)
    )
    summary: str = Field(
        sa_column=Column(JSONB)
    )
    commander_id: UUID = Field(
        default=None,
        index=True,
        foreign_key="users.id"
    )
    commander: "User" = Relationship(
        back_populates="incident_commander"
    )


# --- Affects ---

class AffectedService(BaseEntity, table=True):
    __tablename__ = "affected_services"

    # One-to-Many relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="affected_services"
    )

    # --- Fields ---
    name: str = Field(max_length=255)


class AffectedRegion(BaseEntity, table=True):
    __tablename__ = "affected_regions"

    # One-to-Many relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="affected_regions"
    )

    # --- Fields ---
    name: str = Field(max_length=255)

# --- Resolution & Mitigation ---


class ResolutionMitigation(BaseEntity, table=True):
    __tablename__ = "resolution_mitigations"

    # One-to-One relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="resolution_mitigation"
    )

    # --- Fields ---
    resolution_time_utc: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True)
        )
    )

    short_term_remediation_steps: List[
        "RemediationStep"
    ] = Relationship(
        back_populates="resolution_mitigation_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    long_term_preventative_measures: List[
        "LongTermPreventativeMeasure"
    ] = Relationship(
        back_populates="resolution_mitigation_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )


class RemediationStep(BaseEntity, table=True):
    __tablename__ = "remediation_steps"

    step_description: str = Field(
        sa_column=Column(JSONB)
    )

    resolution_mitigation_id: UUID = Field(
        foreign_key="resolution_mitigations.id"
    )

    resolution_mitigation_ref: "ResolutionMitigation" = Relationship(
        back_populates="short_term_remediation_steps"
    )


class LongTermPreventativeMeasure(BaseEntity, table=True):
    __tablename__ = "long_term_preventative_measures"

    measure_description: str = Field(
        sa_column=Column(JSONB)
    )

    resolution_mitigation_id: UUID = Field(
        foreign_key="resolution_mitigations.id"
    )

    resolution_mitigation_ref: "ResolutionMitigation" = Relationship(
        back_populates="long_term_preventative_measures"
    )


# --- Impacts ---

class Impacts(BaseEntity, table=True):
    __tablename__ = "impacts"

    # One-to-One relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="impacts"
    )

    # --- Fields ---
    customer_impact: str = Field(
        sa_column=Column(JSONB)
    )
    business_impact: str = Field(
        sa_column=Column(JSONB)
    )


# --- Root Cause Analysis (Shallow RCA) ---

class ShallowRCA(BaseEntity, table=True):
    __tablename__ = "shallow_rca"

    # One-to-One relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="shallow_rca"
    )

    # --- Fields ---
    what_happened: str = Field(
        sa_column=Column(JSONB)
    )

    why_it_happened: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )

    technical_causes: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )

    detection_mechanisms: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB)
    )


# --- Communications Log ---

class CommunicationLog(BaseEntity, table=True):
    __tablename__ = "communication_logs"

    # One-to-Many relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="communication_logs"
    )

    # --- Fields ---
    time_utc: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    channel: str = Field(max_length=100)
    message: str = Field(sa_column=Column(JSONB))


# --- Timeline of Events (Chronological Updates) ---

class TimelineEvent(BaseEntity, table=True):
    __tablename__ = "timeline_events"

    # One-to-Many relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="timeline_events"
    )

    # --- Fields ---
    time_utc: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True)
        )
    )

    event_description: str = Field(
        sa_column=Column(JSONB)
    )

    owner_user_id: UUID = Field(
        default=None,
        foreign_key="users.id",
        index=True
    )

    owner_user: "User" = Relationship(
        back_populates="timeline_events_owned")


# --- Sign‑Off ---

class SignOff(BaseEntity, table=True):
    __tablename__ = "sign_offs"

    # One-to-Many relationship definition
    incident_id: UUID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="sign_offs"
    )

    # --- Fields ---
    role: str = Field(max_length=100)

    date_approved: date

    approver_user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False
    )
    approver_user: "User" = Relationship(
        back_populates="sign_offs"
    )
