from uuid import UUID
from datetime import datetime, date
from typing import (
    Annotated,
    Optional,
    List,
    Dict
)

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import (
    Field,
    Relationship,
    DateTime
)

# Import enums from the dedicated file
from src.models.enums import (
    ActionItemStatusEnum,
    RolesEnum,
    FactorTypeEnum,
    PostMortemStatusEnum
)
from src.models.base import BaseEntity

# Forward declaration to avoid circular imports
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.incident import Incident
    from src.models.user import User


class PostMortem(BaseEntity, table=True):
    __tablename__ = "postmortems"

    status: Annotated[
        PostMortemStatusEnum,
        Field(
            default=PostMortemStatusEnum.DRAFT,
            description="Status of the post-mortem"
        )
    ]

    links: Annotated[
        Optional[str],
        Field(
            default=None,
            max_length=512,
            description=(
                "Link to the detailed "
                "postmortem document"
            ),
        )
    ]

    lessons_learned: Annotated[
        Optional[str],
        Field(
            default=None,
            sa_column=Column(Text),
            description=(
                "The lessons that learned from the incident"
            )
        )
    ]

    deep_rca: Annotated[
        List[Dict[str, str]],
        Field(
            default_factory=list,
            sa_column=Column(JSONB),
            description=(
                "Detailed root cause analysis, "
                "structured. e.g. "
                "[{'title': '...', 'analysis': '...'}]"
            )
        )
    ]

    date_completed_utc: Annotated[
        Optional[datetime],
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            ),
            description=(
                "The UTC datetime when the "
                "post-mortem was marked as completed"
            )
        )
    ]

    # --- Relationships ---

    # One-to-One relationship with Incident

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

    # One-to-Many relationships to child tables

    contributing_factors: List[
        "ContributingFactor"
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


class ContributingFactor(BaseEntity, table=True):
    __tablename__ = "contributing_factors"

    """
    A structured factor that contributed to the incident,
    identified during post-mortem.
    """

    factor_type: Annotated[
        FactorTypeEnum,
        Field(
            default=FactorTypeEnum.UNKNOWN,
            description="The category of the contributing factor."
        )
    ]

    description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Detailed description of the contributing factor."
        )
    ]

    # Many-to-One relationship with PostMortem

    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id",
            nullable=False
        )
    ]

    postmortem_ref: "PostMortem" = Relationship(
        back_populates="contributing_factors"
    )


class ActionItem(BaseEntity, table=True):
    __tablename__ = "action_items"

    """
    A specific, actionable task to prevent future incidents.
    """

    description: Annotated[
        str,
        Field(
            sa_column=Column(Text),
            description="Description of the action to be taken"
        )
    ]

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

    # Many-to-One relationship with PostMortem

    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id",
            nullable=False
        )
    ]

    postmortem_ref: "PostMortem" = Relationship(
        back_populates="action_items"
    )

    # Optional relationship to a
    # User who owns the action item

    owner_user_id: Annotated[
        Optional[UUID],
        Field(
            foreign_key="users.id",
            default=None,
            index=True
        )
    ]

    owner_user: Optional[
        "User"
    ] = Relationship(
        back_populates="action_items_owned"
    )


class PostMortemApproval(BaseEntity, table=True):
    __tablename__ = "postmortem_approvals"

    role: Annotated[
        RolesEnum,
        Field(
            description=(
                "Role of the approver "
                "(e.g., SRE Lead, Department Head)"
            )
        )
    ]
    approval_date: Annotated[
        date,
        Field(
            description="Date of approval"
        )
    ]

    # Many-to-One relationship with PostMortem

    postmortem_id: Annotated[
        UUID,
        Field(
            foreign_key="postmortems.id",
            nullable=False
        )
    ]

    postmortem_ref: "PostMortem" = Relationship(
        back_populates="approvals"
    )

    # Relationship to the User who approved it

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
