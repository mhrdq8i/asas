from uuid import UUID
from datetime import datetime

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

    full_name: str | None = None

    # Default role can be set here or during user creation logic
    # role: UserRoleEnum = UserRoleEnum.viewer
    is_active: bool = True

    is_superuser: bool = False

    # Profile fields - keeping them optional
    avatar_url: str | None = None

    bio: str | None = None

    timezone: str | None = None


class UserCreate(UserBase):
    """
    Schema for creating a new user.
    Requires a password.
    """

    password: str = PydanticField(
        min_length=8,
        description="User password"
    )

    # Default role for new users
    role: UserRoleEnum = UserRoleEnum.viewer


class UserUpdate(BaseModel):
    """
    Schema for updating user information.
    All fields are optional.
    """

    email: EmailStr | None = None

    full_name: str | None = None

    username: str | None = PydanticField(
        default=None,
        min_length=3,
        max_length=50
    )

    password: str | None = PydanticField(
        default=None,
        min_length=8,
        description="New password (if changing)"
    )

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

    # Role should be included in the read model
    role: UserRoleEnum

    created_at: datetime

    updated_at: datetime

    # Assuming this comes from the DB model
    is_email_verified: bool = False

    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


# --- Schema for internal use, e.g.,
# when creating user in DB with hashed_password ---
# This is not directly exposed via API
# but used by CRUD/Service layer.
class UserCreateInternal(UserCreate):
    """
    Internal schema for creating a user,
    used by CRUD operations.
    It includes all necessary fields,
    including potentially pre-processed ones.
    """

    # CRUD will receive the hashed password
    hashed_password: str

    is_active: bool = True

    is_superuser: bool = False

    is_email_verified: bool = False


class UserUpdatePassword(BaseModel):

    current_password: str

    new_password: str = PydanticField(
        min_length=8
    )
