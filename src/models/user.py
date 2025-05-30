from datetime import datetime
from typing import Annotated, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship
from sqlalchemy import Column, String, Text

from src.models.base import UserRoleEnum
from src.models.base import BaseEntity


class User(BaseEntity, table=True):
    username: Annotated[
        str,
        Field(
            index=True,
            unique=True,
            nullable=False
        )
    ]
    full_name: Annotated[
        str | None,
        Field(
            default=None
        )
    ]
    email: Annotated[
        EmailStr,
        Field(
            index=True,
            unique=True,
            nullable=False
        )
    ]
    hashed_password: Annotated[
        str,
        Field(
            sa_column=Column(
                String,
                nullable=False
            )
        )
    ]
    is_active: Annotated[
        bool,
        Field(
            default=True,
            nullable=False
        )
    ]
    is_superuser: Annotated[
        bool,
        Field(
            default=False,
            nullable=False
        )
    ]
    role: Annotated[
        UserRoleEnum,
        Field(
            default=UserRoleEnum.viewer,
            nullable=False
        )
    ]
    is_email_verified: Annotated[
        bool,
        Field(
            default=False,
            nullable=False
        )
    ]
    email_verification_token: Annotated[
        str | None,
        Field(
            default=None,
            index=True
        )
    ]
    email_verified_at: Annotated[
        datetime | None,
        Field(
            default=None
        )
    ]
    reset_token: Annotated[
        str | None,
        Field(
            default=None,
            index=True
        )
    ]
    reset_token_expires: Annotated[
        datetime | None,
        Field(
            default=None
        )
    ]
    is_deleted: Annotated[
        bool,
        Field(
            default=False,
            nullable=False,
            index=True
        )
    ]
    deleted_at: Annotated[
        datetime | None,
        Field(
            default=None
        )
    ]
    avatar_url: Annotated[
        str | None,
        Field(
            default=None
        )
    ]
    bio: Annotated[
        str | None,
        Field(
            default=None,
            sa_column=Column(Text)
        )
    ]
    timezone: Annotated[
        str | None,
        Field(
            default=None
        )
    ]
    last_login_at: Annotated[
        datetime | None,
        Field(default=None)
    ]
    last_login_ip: Annotated[
        str | None,
        Field(default=None)
    ]

    incidents_commanded: List["IncidentMetadata"] = Relationship(
        back_populates="commander"
    )
    timeline_events_owned: List["TimelineEvent"] = Relationship(
        back_populates="owner_user"
    )
    action_items_owned: List["ActionItem"] = Relationship(
        back_populates="owner_user"
    )
    sign_offs_made: List["SignOffEntry"] = Relationship(
        back_populates="approver_user"
    )
    post_mortem_approvals_made: List["PostMortemApproval"] = Relationship(
        back_populates="approver_user"
    )
