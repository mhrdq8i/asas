from typing import List, Annotated

from sqlmodel import Field, Relationship
from pydantic import EmailStr, SecretStr

from app.
from app.models.enums import UserRoleEnum


class User(BaseEntityWithID, table=True):
    username: Annotated[str, Field(index=True, unique=True)]
    full_name: str | None = None
    email: Annotated[EmailStr, Field(index=True, unique=True)]
    hashed_password: Annotated[SecretStr, Field(
        sa_column_kwargs={"nullable": False})
    ]
    is_active: Annotated[bool, Field(default=True)]
    is_superuser: Annotated[bool, Field(default=False)]
    role: Annotated[UserRoleEnum, Field(default=UserRoleEnum.viewer)]

    # Relations
    incidents_commander: List["Incident"] = Relationship(
        back_populates="commander")
    timeline_entries: List["TimelineEntry"] = Relationship(
        back_populates="owner_user")
    action_items: List["ActionItem"] = Relationship(
        back_populates="owner_user")
