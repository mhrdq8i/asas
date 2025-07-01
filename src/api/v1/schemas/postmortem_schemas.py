from uuid import UUID
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.enums import (
    ActionItemStatusEnum,
    FactorTypeEnum,
    PostMortemStatusEnum,
    RolesEnum,
)


# Reusable Schemas for JSON fields

class DeepRCAItem(BaseModel):

    title: str = Field(
        ...,
        description=(
            "The title or category "
            "of the RCA finding."
        )
    )

    analysis: str = Field(
        ...,
        description=(
            "The detailed analysis "
            "for this finding."
        )
    )


# ContributingFactor Schemas

class ContributingFactorBase(BaseModel):

    factor_type: FactorTypeEnum = \
        FactorTypeEnum.UNKNOWN

    description: str


class ContributingFactorCreate(
    ContributingFactorBase
):
    pass


class ContributingFactorUpdate(BaseModel):

    factor_type: Optional[
        FactorTypeEnum
    ] = None

    description: Optional[
        str
    ] = None


class ContributingFactorRead(
    ContributingFactorBase
):

    id: UUID

    class Config:
        from_attributes = True


# ActionItem Schemas

class ActionItemBase(BaseModel):

    description: str

    due_date: date

    status: ActionItemStatusEnum = \
        ActionItemStatusEnum.OPEN

    owner_user_id: Optional[
        UUID
    ] = None


class ActionItemCreate(ActionItemBase):
    pass


class ActionItemUpdate(BaseModel):

    description: Optional[str] = None

    due_date: Optional[date] = None

    status: Optional[
        ActionItemStatusEnum
    ] = None

    owner_user_id: Optional[
        UUID
    ] = None


class ActionItemRead(ActionItemBase):
    id: UUID
    # TODO: Add owner_user details if
    # TODO: needed by creating a UserRead schema

    class Config:
        from_attributes = True


# PostMortemApproval Schemas

class PostMortemApprovalBase(BaseModel):

    role: RolesEnum

    approver_user_id: UUID

    approval_date: date


class PostMortemApprovalCreate(
    PostMortemApprovalBase
):
    pass


class PostMortemApprovalRead(
    PostMortemApprovalBase
):
    id: UUID
    # TODO: Add approver_user details if needed

    class Config:
        from_attributes = True


# PostMortem Schemas

class PostMortemBase(BaseModel):

    status: PostMortemStatusEnum = \
        PostMortemStatusEnum.DRAFT

    links: Optional[str] = None

    deep_rca: List[
        DeepRCAItem
    ] = Field(
        default_factory=list
    )

    lessons_learned: List[
        str
    ] = Field(
        default_factory=list
    )


class PostMortemCreate(BaseModel):

    # Only incident_id is needed
    # to create a draft post-mortem.
    # The rest can be added via update endpoints.
    incident_id: UUID


class PostMortemUpdate(BaseModel):

    status: Optional[
        PostMortemStatusEnum
    ] = None

    links: Optional[str] = None

    deep_rca: Optional[
        List[DeepRCAItem]
    ] = None

    lessons_learned: Optional[
        List[str]
    ] = None


class PostMortemRead(PostMortemBase):

    id: UUID

    incident_id: UUID

    date_completed_utc: Optional[
        datetime
    ]

    created_at: datetime

    updated_at: datetime

    # Nested data

    contributing_factors: List[
        ContributingFactorRead
    ] = []

    action_items: List[
        ActionItemRead
    ] = []

    approvals: List[
        PostMortemApprovalRead
    ] = []

    class Config:
        from_attributes = True
