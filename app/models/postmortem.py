from datetime import date
from typing import List, Annotated
from uuid import UUID

from sqlmodel import Field, Relationship

from app.models.enums import StatusEnum
from app.models.base import (
    BaseEntityID,
    BaseIncidentEntity,
    BasePostmortemEntity,
    Approval
)
from app.models.user import User
from app.models.incident import Incident


# Postmortem and its parts
class PostMortem(BaseEntityID, BaseIncidentEntity, table=True):

    incident: Annotated[
        "Incident",
        Relationship(
            back_populates="postmortem"
        )
    ]

    approvals: Annotated[
        List["Approval"],
        Relationship(
            back_populates="postmortem"
        )
    ]

    action_items: Annotated[
        List["ActionItem"],
        Relationship(back_populates="postmortem")
    ]

    metadata: Annotated[
        "PostmortemMetadata" | None, Relationship(
            back_populates="postmortem",
            sa_relationship_kwargs={"uselist": False}
        )
    ]

    deep_rca: Annotated[
        "DeepRCA" | None, Relationship(
            back_populates="postmortem",
            sa_relationship_kwargs={"uselist": False}
        )
    ]

    contributing_factors: Annotated[
        List["ContributingFactor"],
        Relationship(
            back_populates="postmortem"
        )
    ]

    lessons_learned: Annotated[
        List["LessonLearned"],
        Relationship(back_populates="postmortem")
    ]


class PostmortemMetadata(BasePostmortemEntity, table=True):

    postmortem: Annotated[
        PostMortem,
        Relationship(back_populates="metadata")
    ]


class DeepRCA(BasePostmortemEntity, table=True):

    postmortem: Annotated[
        PostMortem,
        Relationship(back_populates="deep_rca")
    ]


class ContributingFactor(BasePostmortemEntity, table=True):

    postmortem: Annotated[
        PostMortem, Relationship(
            back_populates="contributing_factors"
        )
    ]


class LessonLearned(BasePostmortemEntity, table=True):

    postmortem: Annotated[
        PostMortem, Relationship(
            back_populates="lessons_learned"
        )
    ]


# Action items
class ActionItem(BasePostmortemEntity, table=True):

    task: str

    status: StatusEnum

    owner_id: Annotated[
        UUID,
        Field(foreign_key="user.id")
    ]

    due_date: Annotated[
        date,
        Field(default_factory=date.today)
    ]

    postmortem: Annotated[
        PostMortem,
        Relationship(back_populates="action_items")
    ]

    owner_user: Annotated[
        "User",
        Relationship(back_populates="action_items")
    ]
