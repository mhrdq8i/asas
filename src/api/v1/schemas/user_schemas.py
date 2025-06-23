from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    EmailStr,
    Field as PydanticField
)

from src.models.user import UserRoleEnum


class UserBase(BaseModel):
    """
    Base schema for user attributes,
    shared by create and read schemas.
    """

    email: EmailStr

    username: str = PydanticField(
        min_length=3,
        max_length=50
    )

    full_name: str
    # role is not in UserBase,
    # will be added in specific
    # schemas if needed or UserRead

    is_active: bool = True
    is_superuser: bool = False
    is_commander: bool = False
    is_system_user: bool = False

    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None


class UserCreate(UserBase):
    """
    Schema for creating a new user via API.
    Requires a plain password.
    """
    role: UserRoleEnum = UserRoleEnum.VIEWER
    password: str = PydanticField(
        min_length=8,
        description="User password"
    )
    is_system_user: bool = PydanticField(
        default=False,
        exclude=True
    )
    is_superuser: bool = PydanticField(
        default=False,
        exclude=True
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user information.
    All fields are optional.
    """
    email: EmailStr | None = None
    full_name: str
    username: str | None = PydanticField(
        default=None,
        min_length=3,
        max_length=50
    )
    # Password update should be handled
    # by a dedicated endpoint and schema

    is_active: bool | None = None
    is_superuser: bool | None = None
    role: UserRoleEnum | None = None
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None


class UserRead(UserBase):
    """
    Schema for returning user information to the client.
    Excludes sensitive data like passwords.
    """
    id: UUID
    # Role should be included
    # in the read model
    role: UserRoleEnum
    created_at: datetime | None = None
    updated_at: datetime | None = None
    # Value will come from
    # the DB model instance
    is_email_verified: bool
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


class MinimalUserRead(BaseModel):
    username: str
    full_name: str
    is_commander: bool
    role: UserRoleEnum


class UserCreateInternal(UserBase):
    """
    Internal schema for creating a user, used by CRUD operations.
    Accepts hashed_password and can set system user status.
    """
    hashed_password: str
    role: UserRoleEnum

    # Logic: a system user is
    # considered verified by default.
    @property
    def is_email_verified(self) -> bool:
        return self.is_system_user


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = PydanticField(min_length=8)
