from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Annotated

from sqlalchemy import Column, Text
from sqlmodel import Relationship, Field

from src.models.base import BaseEntity, SeverityLevel, IncidentStatus


class Incident(BaseEntity, table=True):

    incident_metadata: Optional["IncidentMetadata"] = Relationship(
        back_populates="incident_ref",
        sa_relationship_kwargs={"uselist": False}
    )
    impacts: Optional["Impacts"] = Relationship(
        back_populates="incident",
        sa_relationship_kwargs={"uselist": False}
    )
    shallow_rca: Optional["ShallowRCA"] = Relationship(
        back_populates="incident",
        sa_relationship_kwargs={"uselist": False}
    )
    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="incident",
        sa_relationship_kwargs={"uselist": False}
    )
    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="incident", sa_relationship_kwargs={"uselist": False}
    )
    affected_services: List["AffectedService"] = Relationship(
        back_populates="incident"
    )
    affected_regions: List["AffectedRegion"] = Relationship(
        back_populates="incident"
    )
    timeline_events: List["TimelineEvent"] = Relationship(
        back_populates="incident"
    )
    communication_log_entries: List["CommunicationLogEntry"] = Relationship(
        back_populates="incident"
    )
    sign_offs: List["SignOffEntry"] = Relationship(
        back_populates="incident"
    )


class IncidentMetadata(BaseEntity, table=True):

    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            unique=True,
            index=True,
            description="Links to the specific Incident record's id"
        )
    ]
    title: Annotated[
        str,
        Field(
            description="Main incident title"
        )
    ]
    severity: Annotated[
        SeverityLevel, Field(
            description="Severity level of the incident"
        )
    ]
    date_time_detected_utc: Annotated[
        datetime,
        Field(
            description="Date/Time Detected (UTC)"
        )
    ]
    detected_by: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Source of detection, e.g., Prometheus Alert or User ID"
        )
    ]
    commander_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="user.id",
            index=True
        )
    ]
    status: Annotated[
        IncidentStatus,
        Field(
            default=IncidentStatus.OPEN,
            description="Current status of the incident"
        )
    ]
    summary: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Short description of the incident"
        )
    ]

    commander: Optional["User"] = Relationship(
        back_populates="incidents_commanded"
    )
    incident_ref: Optional["Incident"] = Relationship(
        back_populates="incident_metadata"
    )


# --------------- Affects ---------------

class AffectedItemBase(BaseEntity, table=False):
    name: Annotated[
        str,
        Field(
            description="Name of the affected item (e.g., service, region, network)"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            index=True
        )
    ]


class AffectedService(AffectedItemBase, table=True):

    incident: Optional["Incident"] = Relationship(
        back_populates="affected_services"
    )


class AffectedRegion(AffectedItemBase, table=True):

    incident: Optional["Incident"] = Relationship(
        back_populates="affected_regions"
    )


class Impacts(BaseEntity, table=True):

    customer_impact: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Details of customer impact"
        )
    ]
    business_impact: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Details of business impact, e.g., estimated lost revenue"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            unique=True,
            index=True
        )
    ]

    incident: Optional["Incident"] = Relationship(
        back_populates="impacts"
    )


class ShallowRCA(BaseEntity, table=True):

    what_happened: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of what happened"
        )
    ]
    why_it_happened_points: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(Text),
            description="List of reasons why it happened"
        )
    ]
    technical_cause: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(Text),
            description="List of technical causes of the incident"
        )
    ]
    detection_mechanism: Annotated[
        List[str],
        Field(
            default_factory=list,
            sa_column=Column(Text),
            description="How the incident was detected"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            unique=True,
            index=True
        )
    ]

    incident: Optional["Incident"] = Relationship(
        back_populates="shallow_rca"
    )


class TimelineEvent(BaseEntity, table=True):

    time_utc: Annotated[
        datetime,
        Field(
            description="Time of the event in UTC"
        )
    ]
    event_description: Annotated[
        str, Field(
            sa_column=Column(Text),
            description="Description of the event"
        )
    ]
    owner_user_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="user.id",
            index=True
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            index=True
        )
    ]
    incident: Optional["Incident"] = Relationship(
        back_populates="timeline_events"
    )
    owner_user: Optional["User"] = Relationship(
        back_populates="timeline_events_owned"
    )


class ResolutionMitigation(BaseEntity, table=True):

    resolution_time_utc: Annotated[
        datetime | None,
        Field(
            default=None,
            description="Time the incident was resolved in UTC"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            unique=True,
            index=True
        )
    ]

    incident: Optional["Incident"] = Relationship(
        back_populates="resolution_mitigation"
    )
    short_term_remediation_steps: List["RemediationStep"] = Relationship(
        back_populates="resolution_mitigation"
    )
    long_term_preventative_measures: List["LongTermPreventativeMeasure"] = Relationship(
        back_populates="resolution_mitigation"
    )


class RemediationStep(BaseEntity, table=True):

    step_description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the remediation step"
        )
    ]
    resolution_mitigation_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="resolutionmitigation.id"
        )
    ]
    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="short_term_remediation_steps"
    )


class LongTermPreventativeMeasure(BaseEntity, table=True):

    measure_description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the long-term preventative measure"
        )
    ]
    resolution_mitigation_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="resolutionmitigation.id"
        )
    ]

    resolution_mitigation: Optional["ResolutionMitigation"] = Relationship(
        back_populates="long_term_preventative_measures"
    )


class CommunicationLogEntry(BaseEntity, table=True):

    time_utc: Annotated[
        datetime,
        Field(
            description="Time of the communication in UTC"
        )
    ]
    channel: Annotated[
        str, Field(
            description="Communication channel, e.g., Slack, Email, Status Page"
        )
    ]
    message: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Content of the communication"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            index=True
        )
    ]
    incident: Optional["Incident"] = Relationship(
        back_populates="communication_log_entries"
    )


class SignOffEntry(BaseEntity, table=True):

    role: Annotated[
        str,
        Field(
            description="Role of the approver at the time of sign-off"
        )
    ]
    approver_user_id: Annotated[
        UUID,
        Field(
            foreign_key="user.id",
            index=True,
            nullable=False
        )
    ]
    date_approved: Annotated[
        date,
        Field(
            description="Date of approval"
        )
    ]
    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incident.id",
            index=True
        )
    ]

    approver_user: "User" = Relationship(
        back_populates="sign_offs_made"
    )
    incident: Optional["Incident"] = Relationship(
        back_populates="sign_offs"
    )
