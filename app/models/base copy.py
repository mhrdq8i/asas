from datetime import datetime, date, timezone
from typing import List, Annotated
from uuid import UUID, uuid4
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel
from pydantic import EmailStr, SecretStr


# Core Incident model
class Incident(BaseEntityWithID, table=True):
    title: str
    severity: SeverityEnum
    time_detected: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    detected_by_id: UUID | None = None
    detected_by_name: str | None = None
    incident_commander_id: Annotated[UUID, Field(foreign_key="user.id")]
    status: StatusEnum
    summary: str
    related_links: str | None = None
    resolution_time: Annotated[datetime | None, Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    long_term_measures: str | None = None

    # Relations
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


# Affected entities
class BaseAffected(BaseIncidentEntity, table=False):
    pass


class ServiceAffected(BaseAffected, table=True):
    service_name: str
    incident: "Incident" = Relationship(back_populates="services")


class RegionAffected(BaseAffected, table=True):
    region: str
    incident: "Incident" = Relationship(back_populates="regions")


# Impact entities
class BaseImpact(BaseIncidentEntity, table=False):
    pass


class CustomerImpact(BaseImpact, table=True):
    incident: "Incident" = Relationship(back_populates="customer_impacts")


class BusinessImpact(BaseImpact, table=True):
    incident: "Incident" = Relationship(back_populates="business_impacts")


# Shallow root cause analysis
class ShallowRCA(BaseIncidentEntity, table=True):
    what_happened: str
    why_it_happened: str
    technical_cause: str
    detection_mechanism: str
    incident: "Incident" = Relationship(back_populates="shallow_rca")


# Timeline of events
class TimelineEntry(BaseIncidentEntity, table=True):
    time: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    event: str
    owner_id: Annotated[UUID, Field(foreign_key="user.id")]
    incident: "Incident" = Relationship(back_populates="timeline")
    owner_user: "User" = Relationship(back_populates="timeline_entries")


# Communication logs
class CommunicationLog(BaseIncidentEntity, table=True):
    time: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    channel: str
    message: str
    incident: "Incident" = Relationship(back_populates="communications")


# Abstract base for all postmortem-related entities
class BasePostmortemEntity(BaseEntityWithID, table=False):
    content: str
    postmortem_id: Annotated[UUID, Field(
        foreign_key="postmortem.postmortem_id")]
    postmortem: "PostMortem" = Relationship()
