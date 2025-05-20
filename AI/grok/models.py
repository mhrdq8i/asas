from typing import Optional
from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime


# Incident
class IncidentBase(SQLModel):
    title: str
    incident_id: str = Field(unique=True)
    severity: str
    status: str
    detection_time: datetime
    detected_by: str
    description: Optional[str] = None
    affected_services: Optional[str] = None
    regions_affected: Optional[str] = None
    customer_impact: Optional[str] = None
    revenue_impact: Optional[str] = None
    root_cause: Optional[str] = None
    resolution_time: Optional[datetime] = None


class Incident(IncidentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class IncidentCreate(IncidentBase):
    pass


class IncidentRead(IncidentBase):
    id: int
    timelines: List["TimelineRead"] = []
    action_items: List["ActionItemRead"] = []
    communication_logs: List["CommunicationLogRead"] = []


# Timeline Chronology
class TimelineBase(SQLModel):
    timestamp: datetime
    update: str
    owner: str
    incident_id: Optional[int] = Field(foreign_key="incident.id")


class Timeline(TimelineBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class TimelineCreate(TimelineBase):
    pass


class TimelineRead(TimelineBase):
    id: int


# Actions
class ActionItemBase(SQLModel):
    task: str
    owner: str
    due_date: datetime
    status: str
    incident_id: Optional[int] = Field(foreign_key="incident.id")


class ActionItem(ActionItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class ActionItemCreate(ActionItemBase):
    pass


class ActionItemRead(ActionItemBase):
    id: int


# Communication_log
class CommunicationLogBase(SQLModel):
    timestamp: datetime
    channel: str
    message: str
    incident_id: Optional[int] = Field(foreign_key="incident.id")


class CommunicationLog(CommunicationLogBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)


class CommunicationLogCreate(CommunicationLogBase):
    pass


class CommunicationLogRead(CommunicationLogBase):
    id: int
