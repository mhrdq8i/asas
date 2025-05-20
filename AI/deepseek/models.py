from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

# Enums


class IncidentStatus(str, Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    MITIGATED = "mitigated"


class SeverityLevel(str, Enum):
    SEV0 = "sev0"
    SEV1 = "sev1"
    SEV2 = "sev2"
    SEV3 = "sev3"

# Base Models


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    team: str

# Core Incident Model


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)
    status: IncidentStatus = Field(default=IncidentStatus.ACTIVE)
    severity: SeverityLevel
    detection_time: datetime = Field(default_factory=datetime.utcnow)
    resolved_time: Optional[datetime] = None
    reported_by: str  # Could be user ID or system name

    # Relationships
    timelines: List["IncidentTimeline"] = Relationship(
        back_populates="incident")
    impacts: List["ImpactAnalysis"] = Relationship(back_populates="incident")
    resolutions: List["Resolution"] = Relationship(back_populates="incident")
    postmortems: List["PostMortem"] = Relationship(back_populates="incident")

# Timeline Model


class IncidentTimeline(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    update_description: str
    owner: str  # User ID or team name

    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id")
    incident: Optional[Incident] = Relationship(back_populates="timelines")

# Impact Analysis Model


class ImpactAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    scope_description: str
    business_impact: str
    root_cause: Optional[str] = None

    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id")
    incident: Optional[Incident] = Relationship(back_populates="impacts")

# Resolution Model


class Resolution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    mitigation_steps: str
    resolution_time: datetime = Field(default_factory=datetime.utcnow)
    verified_by: str  # User ID

    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id")
    incident: Optional[Incident] = Relationship(back_populates="resolutions")

# Post-Mortem Model


class PostMortem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    root_cause_analysis: str
    contributing_factors: str
    lessons_learned: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id")
    incident: Optional[Incident] = Relationship(back_populates="postmortems")
    action_items: List["ActionItem"] = Relationship(
        back_populates="postmortem")

# Action Item Model


class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    owner: str  # User ID or team name
    due_date: datetime
    status: str = Field(default="open")  # open/in-progress/closed

    postmortem_id: Optional[int] = Field(
        default=None, foreign_key="postmortem.id")
    postmortem: Optional[PostMortem] = Relationship(
        back_populates="action_items")

# Create all tables


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Example Usage
if __name__ == "__main__":
    from sqlmodel import create_engine
    engine = create_engine("sqlite:///incidents.db")
    create_db_and_tables()
