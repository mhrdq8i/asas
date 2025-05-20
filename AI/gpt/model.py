from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship


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


class CommunicationLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    timestamp: datetime
    channel: str
    message: str


class ActionItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    incident_id: int = Field(foreign_key="incident.id")
    owner: str
    task: str
    due_date: datetime
    completed: bool = Field(default=False)


class Incident(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    incident_id: str = Field(index=True, unique=True)
    severity: str
    detected_at: datetime
    detected_by: str
    commander: str
    summary: Optional[str] = None
    business_impact: Optional[str] = None
    root_cause: Optional[str] = None
    status: str = Field(default="open")

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


# establish back_populates on child models
TimelineEntry.incident = Relationship(
    back_populates="timeline"
)
CommunicationLog.incident = Relationship(
    back_populates="communications"
)
ActionItem.incident = Relationship(
    back_populates="action_items"
)

# Example: create SQLite engine and tables
if __name__ == "__main__":
    from sqlmodel import create_engine
    engine = create_engine("sqlite:///incidents.db")
    SQLModel.metadata.create_all(engine)
