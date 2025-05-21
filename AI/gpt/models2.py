from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from enum import Enum
from datetime import datetime


# ---- ENUMS ----

class Severity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


# ---- MAIN INCIDENT MODEL ----

class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str
    title: str
    severity: Severity
    status: IncidentStatus
    detected_at: datetime
    detected_by: str
    commander: str
    summary: Optional[str] = None
    business_impact: Optional[str] = None
    root_cause: Optional[str] = None
    postmortem_url: Optional[str] = None

    services: List["IncidentServiceLink"] = Relationship(
        back_populates="incident")
    regions: List["IncidentRegionLink"] = Relationship(
        back_populates="incident")
    timeline: List["TimelineEntry"] = Relationship(back_populates="incident")
    communications: List["CommunicationLog"] = Relationship(
        back_populates="incident")
    action_items: List["ActionItem"] = Relationship(back_populates="incident")


# ---- SERVICE MODEL ----

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    incidents: List["IncidentServiceLink"] = Relationship(
        back_populates="service")


# ---- REGION MODEL ----

class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    incidents: List["IncidentRegionLink"] = Relationship(
        back_populates="region")


# ---- LINK TABLES FOR M:N ----

class IncidentServiceLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    service_id: Optional[int] = Field(
        default=None, foreign_key="service.id", primary_key=True)

    incident: Incident = Relationship(back_populates="services")
    service: Service = Relationship(back_populates="incidents")


class IncidentRegionLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    region_id: Optional[int] = Field(
        default=None, foreign_key="region.id", primary_key=True)

    incident: Incident = Relationship(back_populates="regions")
    region: Region = Relationship(back_populates="incidents")


# ---- TIMELINE ENTRY ----

class TimelineEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    event: str
    owner: str

    incident: Incident = Relationship(back_populates="timeline")


# ---- COMMUNICATION LOG ----

class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    channel: str
    message: str

    incident: Incident = Relationship(back_populates="communications")


# ---- ACTION ITEM ----

class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    owner: str
    task: str
    due_date: datetime
    completed: bool = False

    incident: Incident = Relationship(back_populates="action_items")


# ---- ENUMS ----

class Severity(str, Enum):
    SEV1 = "SEV-1"
    SEV2 = "SEV-2"
    SEV3 = "SEV-3"
    SEV4 = "SEV-4"


class IncidentStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

# ---- User Model ----


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    full_name: str
    hashed_password: str  # فرض می‌کنیم رمزها هش شده هستند
    is_active: bool = True
    is_superuser: bool = False


# ---- MAIN INCIDENT MODEL ----


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: str
    title: str
    severity: Severity
    status: IncidentStatus
    detected_at: datetime
    detected_by: str
    commander: str
    summary: Optional[str] = None
    business_impact: Optional[str] = None
    root_cause: Optional[str] = None
    postmortem_url: Optional[str] = None

    services: List["IncidentServiceLink"] = Relationship(
        back_populates="incident")
    regions: List["IncidentRegionLink"] = Relationship(
        back_populates="incident")
    timeline: List["TimelineEntry"] = Relationship(back_populates="incident")
    communications: List["CommunicationLog"] = Relationship(
        back_populates="incident")
    action_items: List["ActionItem"] = Relationship(back_populates="incident")


# ---- SERVICE MODEL ----

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    incidents: List["IncidentServiceLink"] = Relationship(
        back_populates="service")


# ---- REGION MODEL ----

class Region(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    incidents: List["IncidentRegionLink"] = Relationship(
        back_populates="region")


# ---- LINK TABLES FOR M:N ----

class IncidentServiceLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    service_id: Optional[int] = Field(
        default=None, foreign_key="service.id", primary_key=True)

    incident: Incident = Relationship(back_populates="services")
    service: Service = Relationship(back_populates="incidents")


class IncidentRegionLink(SQLModel, table=True):
    incident_id: Optional[int] = Field(
        default=None, foreign_key="incident.id", primary_key=True)
    region_id: Optional[int] = Field(
        default=None, foreign_key="region.id", primary_key=True)

    incident: Incident = Relationship(back_populates="regions")
    region: Region = Relationship(back_populates="incidents")


# ---- TIMELINE ENTRY ----

class TimelineEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    event: str
    owner_id: int = Field(foreign_key="user.id")
    owner: User = Relationship()

    incident: Incident = Relationship(back_populates="timeline")


# ---- COMMUNICATION LOG ----

class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    channel: str
    message: str
    sender_id: int = Field(foreign_key="user.id")
    sender: User = Relationship()

    incident: Incident = Relationship(back_populates="communications")


# ---- ACTION ITEM ----

class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    task: str
    due_date: datetime
    completed: bool = False
    owner_id: int = Field(foreign_key="user.id")
    owner: User = Relationship()

    incident: Incident = Relationship(back_populates="action_items")
