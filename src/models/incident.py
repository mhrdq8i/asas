from uuid import UUID
from datetime import (
    datetime,
    date
)
from typing import (
    Optional,
    List,
    TypeAlias
)

from sqlalchemy import (
    Column,
    Text
)
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
    RolesEnum,
    SeverityLevelEnum,
    IncidentStatusEnum,
    AffectedItemEnum
)
from src.models.user import User
from src.models.postmortem import (
    PostMortem
)

IncidentID: TypeAlias = UUID


class Incident(BaseEntity, table=True):
    __tablename__ = "incidents"

    # --- Mandatory Relationships ---

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

    resolution_mitigation: Optional[
        "ResolutionMitigation"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )

    postmortem: Optional[
        "PostMortem"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )

    # --- List-based Relationships ---

    affected_services: List[
        "AffectedService"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    affected_regions: List[
        "AffectedRegion"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    timeline_events: List[
        "TimelineEvent"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    communication_logs: List[
        "CommunicationLog"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    sign_offs: List[
        "SignOff"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )

    @property
    def is_resolved(self) -> bool:
        return self.resolution_mitigation is not None

    @property
    def has_postmortem(self) -> bool:
        return self.postmortem is not None

    @property
    def status(self) -> IncidentStatusEnum:
        return self.profile.status

    @property
    def is_critical(self) -> bool:
        return self.profile.severity == SeverityLevelEnum.CRITICAL

    class Config:
        """
        arbitrary_types_allowed = True:

        - By default, Pydantic only allows certain
        basic types (str, int, float, etc.)
        - Setting this to True allows the model
        to work with custom Python types
        - This is particularly useful when
        working with types like SQLAlchemy
        models or custom classes.


        json_encoders = {...}

        - This dictionary defines how to serialize
        specific Python types to JSON
        - It's needed because some Python types
        don't have a direct JSON representation
        """
        arbitrary_types_allowed = True
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


# --- Incident Profile ---


class IncidentProfile(BaseEntity, table=True):
    __tablename__ = "incident_profile"

    # One-to-One relationship definition

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="profile"
    )

    # --- Fields ---

    status: IncidentStatusEnum = Field(
        default=IncidentStatusEnum.OPEN
    )

    title: str = Field(max_length=255)

    severity: SeverityLevelEnum

    is_auto_detected: bool = Field(
        default=False
    )

    datetime_detected_utc: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True)
        )
    )

    summary: str = Field(
        default="",
        sa_column=Column(Text)
    )

    commander_id: UUID = Field(
        foreign_key="users.id",
        default=None,
        index=True
    )

    commander: "User" = Relationship(
        back_populates="incident_commander"
    )


# --- Affects ---

class AffectedItem(BaseEntity, table=True):
    __tablename__ = "affected_items"

    # One-to-Many relationship

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )
    incident_ref: "Incident" = Relationship(
        back_populates="affected_items"
    )

    # Fields to define the item itself

    item_type: AffectedItemEnum = Field(
        description=(
            "The type of the affected item "
            "(e.g., Service, Region, Network)."
        )
    )

    description: str = Field(
        default="",
        sa_column=Column(Text),
    )


# --- Resolution & Mitigation ---

class ResolutionMitigation(BaseEntity, table=True):
    __tablename__ = "resolution_mitigations"

    # One-to-One relationship definition

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="resolution_mitigation"
    )

    # --- Fields ---

    resolution_time_utc: datetime = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True)
        )
    )

    short_term_remediation_steps: List[
        str
    ] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
    )

    long_term_preventative_measures: List[
        str
    ] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
    )


# --- Impacts ---

class Impacts(BaseEntity, table=True):
    __tablename__ = "impacts"

    # One-to-One relationship definition

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        unique=True,
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="impacts"
    )

    # --- Fields ---

    customer_impact: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
    )

    business_impact: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
    )


# --- Root Cause Analysis (Shallow RCA) ---

class ShallowRCA(BaseEntity, table=True):
    __tablename__ = "shallow_rca"

    # One-to-One relationship definition

    incident_id: IncidentID = Field(
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
        sa_column=Column(Text)
    )

    why_it_happened: str = Field(
        sa_column=Column(Text)
    )

    technical_causes: str = Field(
        sa_column=Column(Text)
    )

    detection_mechanisms: str = Field(
        sa_column=Column(Text)
    )


# --- Communications Log ---

class CommunicationLog(BaseEntity, table=True):
    __tablename__ = "communication_logs"

    # One-to-Many relationship definition

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="communication_logs"
    )

    # --- Fields ---

    time_utc: datetime = Field(
        sa_column=Column(
            DateTime(timezone=True)
        )
    )

    channel: str = Field(max_length=100)

    message: str = Field(
        sa_column=Column(Text)
    )


# --- Timeline of Events (Chronological Updates) ---

class TimelineEvent(BaseEntity, table=True):
    __tablename__ = "timeline_events"

    # One-to-Many relationship definition

    incident_id: IncidentID = Field(
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
        sa_column=Column(Text)
    )

    owner_user_id: UUID = Field(
        foreign_key="users.id",
        default=None,
        index=True
    )

    owner_user: "User" = Relationship(
        back_populates="timeline_events_owned"
    )


# --- Sign‑Off ---

class SignOff(BaseEntity, table=True):
    __tablename__ = "sign_offs"

    # One-to-Many relationship definition

    incident_id: IncidentID = Field(
        foreign_key="incidents.id",
        index=True,
        nullable=False
    )

    incident_ref: "Incident" = Relationship(
        back_populates="sign_offs"
    )

    # --- Fields ---

    role: RolesEnum = Field(
        nullable=False
    )

    date_approved: date

    approver_user_id: UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False
    )

    approver_user: "User" = Relationship(
        back_populates="sign_offs"
    )
