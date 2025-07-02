from datetime import datetime
from typing import Annotated, List

from pydantic import EmailStr
from sqlmodel import Field, Relationship, DateTime
from sqlalchemy import Column, Text

from src.models.enums import UserRoleEnum
from src.models.base import BaseEntity


class User(BaseEntity, table=True):
    __tablename__ = "users"

    # Username fields
    full_name: Annotated[
        str,
        Field(
            default=None,
            max_length=100
        )
    ]

    username: Annotated[
        str,
        Field(
            index=True,
            unique=True,
            nullable=False,
            max_length=50
        )
    ]

    reset_token: Annotated[
        str | None,
        Field(
            default=None,
            index=True,
            max_length=255
        )
    ]

    reset_token_expires: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            )
        )
    ]

    # User status and roles
    role: Annotated[
        str,
        Field(
            default=UserRoleEnum.VIEWER,
            nullable=False
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

    is_commander: Annotated[
        bool,
        Field(
            default=False,
            nullable=False,
            index=True,
        )
    ]

    is_system_user: Annotated[
        bool,
        Field(
            default=False,
            nullable=False
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

    # Email fields
    is_email_verified: Annotated[
        bool,
        Field(
            default=False,
            nullable=False
        )
    ]

    email: Annotated[
        EmailStr, Field(
            index=True,
            unique=True,
            nullable=False,
            max_length=255
        )
    ]

    email_verification_token: Annotated[
        str | None,
        Field(
            default=None,
            index=True,
            max_length=255
        )
    ]

    email_verified_at: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            )
        )
    ]

    # Password reset fields
    hashed_password: Annotated[
        str,
        Field(
            nullable=False,
            max_length=255
        )
    ]

    # Profile and activity
    avatar_url: Annotated[
        str | None,
        Field(
            default=None,
            max_length=512
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
            default=None,
            max_length=50
        )
    ]

    last_login_at: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            )
        )
    ]

    last_login_ip: Annotated[
        str | None,
        Field(
            default=None,
            max_length=45
        )
    ]

    deleted_at: Annotated[
        datetime | None,
        Field(
            default=None,
            sa_column=Column(
                DateTime(timezone=True)
            )
        )
    ]

    # Relationships
    incident_commander: List[
        "IncidentProfile"
    ] = Relationship(
        back_populates="commander"
    )
    timeline_events_owned: List[
        "TimelineEvent"
    ] = Relationship(
        back_populates="owner_user"
    )
    action_items_owned: List[
        "ActionItem"
    ] = Relationship(
        back_populates="owner_user"
    )
    sign_offs: List[
        "SignOff"
    ] = Relationship(
        back_populates="approver_user"
    )
    approvals: List[
        "PostMortemApproval"
    ] = Relationship(
        back_populates="approver_user"
    )
