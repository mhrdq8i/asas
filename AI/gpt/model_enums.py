
from sqlalchemy import Column, Enum as SqlEnum
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import List, Optional
from enum import Enum


# Enums for static value sets
type SeverityType = str, Enum


class Severity(str, Enum):
    Sev1 = "Sev-1"
    Sev2 = "Sev-2"
    Sev3 = "Sev-3"
    Sev4 = "Sev-4"


class IncidentStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


# Association tables
class IncidentServiceLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True
    )
    service_id: Optional[int] = Field(
        default=None, foreign_key="service.id", primary_key=True
    )


class IncidentRegionLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True
    )
    region_id: Optional[int] = Field(
        default=None, foreign_key="region.id", primary_key=True
    )


# Core models
class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    incidents: List["Incident"] = Relationship(
        back_populates="services", link_model=IncidentServiceLink
    )


class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    incidents: List["Incident"] = Relationship(
        back_populates="regions", link_model=IncidentRegionLink
    )


class TimelineEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    event: str
    owner: str
    incident: Optional["Incident"] = Relationship(back_populates="timeline")


class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    channel: str
    message: str
    incident: Optional["Incident"] = Relationship(
        back_populates="communications")


class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    owner: str
    task: str
    due_date: datetime
    completed: bool = Field(default=False)
    incident: Optional["Incident"] = Relationship(
        back_populates="action_items")


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    incident_id: str = Field(index=True, unique=True)
    severity: Severity = Field(
        sa_column=Column(SqlEnum(Severity)), default=Severity.Sev1
    )
    status: IncidentStatus = Field(
        sa_column=Column(SqlEnum(IncidentStatus)), default=IncidentStatus.open
    )
    detected_at: datetime
    detected_by: str
    commander: str
    summary: Optional[str] = None
    business_impact: Optional[str] = None
    root_cause: Optional[str] = None

    services: List[Service] = Relationship(
        back_populates="incidents", link_model=IncidentServiceLink
    )
    regions: List[Region] = Relationship(
        back_populates="incidents", link_model=IncidentRegionLink
    )
    timeline: List[TimelineEntry] = Relationship(back_populates="incident")
    communications: List[CommunicationLog] = Relationship(
        back_populates="incident")
    action_items: List[ActionItem] = Relationship(back_populates="incident")


# Example: create SQLite engine and tables
if __name__ == "__main__":
    from sqlmodel import create_engine
    engine = create_engine("sqlite:///incidents.db")
    SQLModel.metadata.create_all(engine)
