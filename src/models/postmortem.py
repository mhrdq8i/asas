from uuid import UUID
from datetime import datetime, date
from typing import (
    Annotated,
    Optional,
    List
)

from sqlmodel import (
    Field,
    Relationship,
    DateTime
)
from sqlalchemy import Column, Text

from src.models.base import (
    BaseEntity,
    ActionItemStatusEnum,
    PostMortemApproverRoleEnum
)
# from src.models.incident import Incident
# from src.models.user import User


class PostMortem(BaseEntity, table=True):
    __tablename__ = "postmortems"

    incident_id: Annotated[
        UUID,
        Field(
            foreign_key="incidents.id",
            unique=True,
            index=True,
            nullable=False
        )
    ]
    incident_ref: "Incident" = Relationship(
        back_populates="postmortem"
    )
    metadata: Optional[
        "PostMortemMetadata"
    ] = Relationship(
        back_populates="postmortem_ref",
        sa_relationship_kwargs={
            "uselist": False,
            "cascade": "all, delete-orphan"
        }
    )
    contributing_factors: List[
        "ContributingFactor"
    ] = Relationship(
        back_populates="postmortem_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    lessons_learned: List[
        "LessonLearned"
    ] = Relationship(
        back_populates="postmortem_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    action_items: List[
        "ActionItem"
    ] = Relationship(
        back_populates="postmortem_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )
    approvals: List[
        "PostMortemApproval"
    ] = Relationship(
        back_populates="postmortem_ref",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan"
        }
    )


class PostMortemMetadata(BaseEntity, table=True):
    __tablename__ = "postmortem_metadata"

    id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id",
            unique=True,
            index=True,
            nullable=False
        )
    ]
    postmortem: "PostMortem" = Relationship(
        back_populates="postmortem_metadata"
    )
    status: Annotated[
        str,
        Field(
            description="Status of the post-mortem",
            max_length=50
        )
    ]
    links: Annotated[
        str | None,
        Field(
            default=None,
            description="Link to the detailed postmortem document",
            max_length=512
        )
    ]
    deep_rca: Annotated[
        str | None,
        Field(
            default=None,
            sa_column=Column(Text),
            description="In-depth technical cause from deep RCA"
        )
    ]
    date_completed_utc: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            )
        )
    ]


class ContributingFactor(BaseEntity, table=True):
    __tablename__ = "contributing_factors"

    factor_type: Annotated[
        str,
        Field(
            description="Type of factor",
            max_length=100
        )
    ]
    description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the contributing factor"
        )
    ]
    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id"
        )
    ]
    postmortem_ref: Optional[
        "PostMortem"
    ] = Relationship(
        back_populates="contributing_factors"
    )


class LessonLearned(BaseEntity, table=True):
    __tablename__ = "lessons_learned"

    description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the lesson learned"
        )
    ]
    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id"
        )
    ]
    postmortem_ref: Optional[
        "PostMortem"
    ] = Relationship(
        back_populates="lessons_learned"
    )


class ActionItem(BaseEntity, table=True):
    __tablename__ = "action_items"

    description: Annotated[
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
            foreign_key="users.id",
            index=True
        )
    ]
    owner_user: Optional[
        "User"
    ] = Relationship(
        back_populates="action_items_owned"
    )
    due_date: Annotated[
        date,
        Field(
            description="Due date for the action item"
        )
    ]
    status: Annotated[
        ActionItemStatusEnum,
        Field(
            default=ActionItemStatusEnum.OPEN,
            description="Status of the action item"
        )
    ]
    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id"
        )
    ]
    postmortem_ref: Optional[
        "PostMortem"
    ] = Relationship(
        back_populates="action_items"
    )


class PostMortemApproval(BaseEntity, table=True):
    __tablename__ = "postmortem_approvals"

    role: Annotated[
        PostMortemApproverRoleEnum,
        Field(
            description="Role of the approver",
            default=PostMortemApproverRoleEnum.INCIDENT_LEAD
        )
    ]
    approver_user_id: Annotated[
        UUID,
        Field(
            foreign_key="users.id",
            index=True,
            nullable=False
        )
    ]
    approver_user: "User" = Relationship(
        back_populates="postmortem_approvals"
    )
    approval_date: Annotated[
        date,
        Field(
            description="Date of approval"
        )
    ]
    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id"
        )
    ]
    postmortem_ref: Optional[
        "PostMortem"
    ] = Relationship(
        back_populates="approvals"
    )
