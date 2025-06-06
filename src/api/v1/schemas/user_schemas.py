from datetime import datetime
from uuid import UUID, uuid4

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

    # Default for UserBase, can be overridden
    is_active: bool = True
    # Default for UserBase, can be overridden
    is_superuser: bool = False

    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None


class UserCreate(UserBase):
    """
    Schema for creating a new user via API.
    Requires a plain password.
    """
    password: str = PydanticField(
        min_length=8,
        description="User password"
    )
    # Default role for new users via API
    role: UserRoleEnum = UserRoleEnum.VIEWER


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


class UserCreateInternal(UserBase):
    """
    Internal schema for creating a user,
    used by CRUD operations.
    Accepts hashed_password
    instead of plain password.
    """
    hashed_password: str

    # Fields that are part of User model
    # but might not be in UserBase,
    # or need specific defaults for internal
    # creation different from API creation.
    # UserCreate (API input) defines role,
    # is_active, is_superuser defaults for API.
    # Here, we ensure they are present for
    # DB creation if not in UserBase.
    # This field must be provided when creating UserCreateInternal instance
    role: UserRoleEnum
    # is_active is in UserBase with default True
    # is_superuser is in UserBase with default False
    is_email_verified: bool = False


class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = PydanticField(min_length=8)
