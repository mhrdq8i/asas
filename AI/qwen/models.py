from datetime import datetime
from typing import List, Optional
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

# Enums


class Severity(str, Enum):
    SEV1 = "Sev 1 (Critical)"
    SEV2 = "Sev 2 (High)"
    SEV3 = "Sev 3 (Medium)"
    SEV4 = "Sev 4 (Low)"


class IncidentStatus(str, Enum):
    INVESTIGATING = "Investigating"
    IDENTIFIED = "Identified"
    MITIGATED = "Mitigated"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class ActionType(str, Enum):
    IMMEDIATE = "Immediate"
    LONG_TERM = "Long-Term"


class CommunicationChannel(str, Enum):
    SLACK = "Slack"
    EMAIL = "Email"
    STATUS_PAGE = "Status Page"


class TaskStatus(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    IN_PROGRESS = "In Progress"

# Core Models


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    severity: Severity
    status: IncidentStatus = IncidentStatus.INVESTIGATING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={
                                 "onupdate": datetime.utcnow})

    # Relationships
    affected_services: List["AffectedService"] = Relationship(
        back_populates="incident")
    impact_analysis: Optional["ImpactAnalysis"] = Relationship(
        back_populates="incident")
    root_cause: Optional["RootCause"] = Relationship(back_populates="incident")
    corrective_actions: List["CorrectiveAction"] = Relationship(
        back_populates="incident")
    communications: List["CommunicationLog"] = Relationship(
        back_populates="incident")
    tasks: List["PostIncidentTask"] = Relationship(back_populates="incident")


class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True)
    incidents: List["AffectedService"] = Relationship(back_populates="service")


class AffectedService(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    service_id: Optional[int] = Field(
        default=None, foreign_key="service.id", primary_key=True)
    region: str
    customers_impacted: int

    # Relationships
    incident: Optional[Incident] = Relationship(
        back_populates="affected_services")
    service: Optional[Service] = Relationship(back_populates="incidents")


class ImpactAnalysis(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    service_metrics: dict = Field(sa_type=JSON)
    customer_impact: str
    financial_impact: Optional[float] = None

    # Relationships
    incident: Optional[Incident] = Relationship(
        back_populates="impact_analysis")


class RootCause(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    primary_cause: str
    contributing_factors: str

    # Relationships
    incident: Optional[Incident] = Relationship(back_populates="root_cause")


class CorrectiveAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    description: str
    action_type: ActionType
    status: TaskStatus = TaskStatus.PENDING
    due_date: datetime

    # Relationships
    incident: Optional[Incident] = Relationship(
        back_populates="corrective_actions")


class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    audience: str
    channel: CommunicationChannel
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    incident: Optional[Incident] = Relationship(
        back_populates="communications")


class PostIncidentTask(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    description: str
    owner: str
    due_date: datetime
    status: TaskStatus = TaskStatus.PENDING

    # Relationships
    incident: Optional[Incident] = Relationship(back_populates="tasks")
