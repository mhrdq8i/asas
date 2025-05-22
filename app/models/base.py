from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from app.models.user import User
from app.models.incident import Incident
from app.models.postmortem import PostMortem


class BaseEntityID(SQLModel):
    id: Annotated[UUID, Field(default_factory=uuid4, primary_key=True)]


class BaseIncidentEntity(BaseEntityID, table=False):
    incident_id: Annotated[UUID, Field(foreign_key="incident.incident_id")]
    incident: "Incident" = Relationship()


class BasePostmortemEntity(BaseEntityID, table=False):
    content: str
    postmortem_id: Annotated[UUID, Field(
        foreign_key="postmortem.postmortem_id")]
    postmortem: "PostMortem" = Relationship()


# Unified Approval
class Approval(BaseEntityID, table=True):
    approver_id: Annotated[UUID, Field(foreign_key="user.id")]
    approver: Annotated["User", Relationship(
        back_populates="approvals"
    )]
    approved_at: Annotated[datetime, Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )]
    comment: Annotated[str | None, Field(default=None)]
    incident: Annotated[Incident | None,
                        Relationship(back_populates="approvals")]
    incident_id: Annotated[UUID | None, Field(
        default=None, foreign_key="incident.id")]
    postmortem: Annotated["PostMortem" | None,
                          Relationship(back_populates="approvals")]
    postmortem_id: Annotated[UUID | None, Field(
        default=None, foreign_key="postmortem.id")]
