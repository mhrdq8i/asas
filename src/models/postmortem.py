from uuid import UUID
from datetime import datetime, date
from typing import (
    Annotated,
    Optional,
    List
)

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import (
    Field,
    Relationship,
    DateTime
)

from src.models.base import (
    BaseEntity,
    ActionItemStatusEnum,
    RolesEnum
)


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

    profile: Optional[
        "PostMortemProfile"
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


class PostMortemProfile(BaseEntity, table=True):
    __tablename__ = "postmortem_profile"

    postmortem_ref: "PostMortem" = Relationship(
        back_populates="profile"
    )
    post_mortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id",
            unique=True,
            index=True,
            nullable=False,
            description=(
                "Foreign key to the main"
                "postmortems table, "
                "establishing a 1-to-1 link."
            )
        )
    ]
    status: Annotated[
        str,
        Field(
            description=(
                "Status of the post-mortem"
            ),
            max_length=50
        )
    ]
    links: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Link to the detailed"
                "postmortem document"
            ),
            max_length=512
        )
    ]
    deep_rca: Annotated[
        str | None,
        Field(
            default=None,
            sa_column=Column(JSONB),
            description=(
                "In-depth technical "
                "cause from deep RCA"
            )
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
            sa_column=Column(JSONB),
            description=(
                "Contributing factors"
            )
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
            sa_column=Column(JSONB),
            description=(
                "Lesson learned from"
                "the incident"
            )
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
            sa_column=Column(JSONB),
            description=(
                "Action items"
            )
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
            description=(
                "Due date for the "
                "action item"
            )
        )
    ]
    status: Annotated[
        ActionItemStatusEnum,
        Field(
            default=ActionItemStatusEnum.OPEN,
            description=(
                "Status of the "
                "action item"
            )
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
        RolesEnum,
        Field(
            default=(
                RolesEnum.SRE_LEAD
            ),
            description=(
                "Role of the approver"
            )
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
        back_populates="approvals"
    )
    approval_date: Annotated[
        date,
        Field(
            description=(
                "Date of approval"
            )
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
