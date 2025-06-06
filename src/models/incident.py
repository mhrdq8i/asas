from uuid import UUID
from datetime import (
    datetime,
    date
)
from typing import (
    Optional,
    List,
    Annotated
)

from sqlalchemy.dialects.postgresql import (
    JSONB
)
from sqlalchemy import (
    Column,
    Text
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

    profile: Optional[
        "IncidentProfile"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    impacts: Optional[
        "Impacts"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    shallow_rca: Optional[
        "ShallowRCA"
    ] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
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


class IncidentProfile(BaseEntity, table=True):
    __tablename__ = "incident_profile"

    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            unique=True,
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="profile"
    )

    title: Annotated[
        str,
        Field(
            max_length=255,
            description=(
                "Main incident title"
            )
        )
    ]
    severity: Annotated[
        SeverityLevelEnum,
        Field(
            description=(
                "Severity level of the incident"
            )
        )
    ]
    datetime_detected_utc: Annotated[
        datetime,
        Field(
            sa_column=Column(
                DateTime(timezone=True)
            ),
            description=(
                "Date/Time Detected (UTC)"
            )
        )
    ]
    detected_by: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description=(
                "Source of detection, e.g., "
                "Prometheus Alert or User ID"
            )
        )
    ]
    commander_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="users.id",
            index=True
        )
    ]
    commander: Optional[
        "User"
    ] = Relationship(
        back_populates="incident_commander"
    )
    status: Annotated[
        IncidentStatusEnum,
        Field(
            default=IncidentStatusEnum.OPEN,
            description=(
                "Current status of the incident"
            )
        )
    ]
    summary: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Short description of the incident"
            )
        )
    ]


class AffectedItemBase(BaseEntity):
    name: Annotated[
        str,
        Field(
            max_length=255,
            description=(
                "Name of the affected item"
            )
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            index=True
        )
    ]
    # incident_ref relationship
    # should be defined
    # in concrete classes
    # for specific back_populates


class AffectedService(AffectedItemBase, table=True):
    __tablename__ = "affected_services"

    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="affected_services"
    )


class AffectedRegion(AffectedItemBase, table=True):
    __tablename__ = "affected_regions"

    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="affected_regions"
    )


class Impacts(BaseEntity, table=True):
    __tablename__ = "impacts"

    customer_impact: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Details of customer impact"
            )
        )
    ]
    business_impact: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Details of business impact, e.g., "
                "estimated lost revenue"
            )
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            unique=True,
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="impacts"
    )


class ShallowRCA(BaseEntity, table=True):
    __tablename__ = "shallow_rca"

    what_happened: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Description of what happened"
            )
        )
    ]
    why_it_happened: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(JSONB),
            description=(
                "List of reasons why it happened"
            )
        )
    ]
    technical_causes: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(JSONB),
            description=(
                "List of technical "
                "causes of the incident"
            )
        )
    ]
    detection_mechanisms: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(Text),
            description=(
                "How the incident was detected"
            )
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            unique=True,
            index=True,
            nullable=False
        )
    ]
    incident_ref: Optional["Incident"] = Relationship(
        back_populates="shallow_rca"
    )


class TimelineEvent(BaseEntity, table=True):
    __tablename__ = "timeline_events"

    time_utc: Annotated[
        datetime,
        Field(
            sa_column=Column(
                DateTime(timezone=True)
            ),
            description=(
                "Time of the event in UTC"
            )
        )
    ]
    event_description: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Description of the event"
            )
        )
    ]
    owner_user_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="users.id",
            index=True
        )
    ]
    owner_user: Optional[
        "User"
    ] = Relationship(
        back_populates="timeline_events_owned"
    )
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="timeline_events"
    )


class ResolutionMitigation(BaseEntity, table=True):
    __tablename__ = "resolution_mitigations"

    resolution_time_utc: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            ),
            description=(
                "Time the incident "
                "was resolved in UTC"
            )
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            unique=True,
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="resolution_mitigation"
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

    step_description: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Remediation actions"
            )
        )
    ]
    resolution_mitigation_id: Annotated[
        UUID,
        Field(
            foreign_key="resolution_mitigations.id"
        )
    ]
    resolution_mitigation_ref: Optional[
        "ResolutionMitigation"
    ] = Relationship(
        back_populates="short_term_remediation_steps"
    )


class LongTermPreventativeMeasure(BaseEntity, table=True):
    __tablename__ = "long_term_preventative_measures"

    measure_description: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Description of the "
                "long-term preventative "
                "measure"
            )
        )
    ]
    resolution_mitigation_id: Annotated[
        UUID,
        Field(
            foreign_key="resolution_mitigations.id"
        )
    ]
    resolution_mitigation_ref: Optional[
        "ResolutionMitigation"
    ] = Relationship(
        back_populates="long_term_preventative_measures"
    )


class CommunicationLog(BaseEntity, table=True):
    __tablename__ = "communication_logs"

    time_utc: Annotated[
        datetime,
        Field(
            sa_column=Column(
                DateTime(timezone=True)
            ),
            description=(
                "Time of the communication in UTC"
            )
        )
    ]
    channel: Annotated[
        str,
        Field(
            description="Communication channel",
            max_length=100
        )
    ]
    message: Annotated[
        str,
        Field(
            sa_column=Column(JSONB),
            description=(
                "Content of the communication"
            )
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="communication_logs"
    )


class SignOff(BaseEntity, table=True):
    __tablename__ = "sign_offs"

    role: Annotated[
        str,
        Field(
            description="Role of the approver",
            max_length=100
        )
    ]
    approver_user_id: Annotated[
        UUID,
        Field(
            foreign_key="users.id",
            index=True,
            nullable=False
        )
    ]
    approver_user: "User" = Relationship(
        back_populates="sign_offs"
    )
    date_approved: Annotated[
        date,
        Field(
            description="Date of approval"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            index=True
        )
    ]
    incident_ref: Optional[
        "Incident"
    ] = Relationship(
        back_populates="sign_offs"
    )
