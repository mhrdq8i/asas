from uuid import UUID
from datetime import datetime, date
from typing import Annotated, Optional, List

from sqlmodel import Field, Relationship
from sqlalchemy import Column, Text

from src.models.base import BaseEntity, ActionItemStatus


class PostMortem(BaseEntity, table=True):
    post_mortem_status: Annotated[
        str,
        Field(
            description="Status of the post-mortem, e.g., Completed"
        )
    ]
    document_link: Annotated[
        str | None,
        Field(
            default=None,
            description="Link to the detailed post-mortem document if separate"
        )
    ]
    deep_rca_detailed_technical_cause: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="In-depth technical cause from deep RCA"
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
        back_populates="post_mortem"
    )
    contributing_factors: List["ContributingFactor"] = Relationship(
        back_populates="post_mortem"
    )
    lessons_learned: List["LessonLearned"] = Relationship(
        back_populates="post_mortem"
    )
    action_items: List["ActionItem"] = Relationship(
        back_populates="post_mortem"
    )
    approvals: List["PostMortemApproval"] = Relationship(
        back_populates="post_mortem"
    )


class ContributingFactor(BaseEntity, table=True):
    factor_type: Annotated[
        str,
        Field(
            description="Type of factor, e.g., Process Gap, Tooling Gap"
        )
    ]
    description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the contributing factor"
        )
    ]
    post_mortem_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="postmortem.id"
        )
    ]

    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="contributing_factors"
    )


class LessonLearned(BaseEntity, table=True):
    lesson_description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the lesson learned"
        )
    ]
    post_mortem_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="postmortem.id"
        )
    ]

    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="lessons_learned"
    )


class ActionItem(BaseEntity, table=True):
    task_description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the action item task"
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
    due_date: Annotated[
        date,
        Field(
            description="Due date for the action item"
        )
    ]
    status: Annotated[
        ActionItemStatus,
        Field(
            default=ActionItemStatus.OPEN,
            description="Status of the action item"
        )
    ]
    post_mortem_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="postmortem.id"
        )
    ]

    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="action_items"
    )
    owner_user: Optional["User"] = Relationship(
        back_populates="action_items_owned"
    )


class PostMortemApproval(BaseEntity, table=True):
    role: Annotated[
        str,
        Field(
            description="Role of the approver at the time of approval"
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
    approval_date: Annotated[
        date,
        Field(
            description="Date of approval"
        )
    ]
    post_mortem_id: Annotated[
        UUID | None,
        Field(
            default=None,
            foreign_key="postmortem.id"
        )
    ]

    post_mortem: Optional["PostMortem"] = Relationship(
        back_populates="approvals"
    )
    approver_user: "User" = Relationship(
        back_populates="post_mortem_approvals_made"
    )
