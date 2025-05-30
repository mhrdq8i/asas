from pydantic import BaseModel, EmailStr, Field as PydanticField
import uuid
from datetime import datetime

from ....models.user import UserRoleEnum  # Corrected relative import path


class UserBase(BaseModel):
    """
    Base schema for user attributes, shared by create and read schemas.
    """
    email: EmailStr
    username: str = PydanticField(min_length=3, max_length=50)
    full_name: str | None = None
    # role is not in UserBase, will be added in specific schemas if needed or UserRead
    is_active: bool = True  # Default for UserBase, can be overridden
    is_superuser: bool = False  # Default for UserBase, can be overridden

    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None


# --- Schema for User Creation (Input from API) ---
class UserCreate(UserBase):
    """
    Schema for creating a new user via API. Requires a plain password.
    """
    password: str = PydanticField(min_length=8, description="User password")
    role: UserRoleEnum = UserRoleEnum.viewer  # Default role for new users via API


# --- Schema for User Update (Input from API - example, can be expanded) ---
class UserUpdate(BaseModel):
    """
    Schema for updating user information. All fields are optional.
    """
    email: EmailStr | None = None
    full_name: str | None = None
    username: str | None = PydanticField(
        default=None, min_length=3, max_length=50)
    # Password update should be handled by a dedicated endpoint and schema
    is_active: bool | None = None
    is_superuser: bool | None = None
    role: UserRoleEnum | None = None
    avatar_url: str | None = None
    bio: str | None = None
    timezone: str | None = None


# --- Schema for Reading User Information (Output to API) ---
class UserRead(UserBase):
    """
    Schema for returning user information to the client.
    Excludes sensitive data like passwords.
    """
    id: uuid.UUID
    role: UserRoleEnum  # Role should be included in the read model
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_email_verified: bool  # Value will come from the DB model instance
    last_login_at: datetime | None = None

    class Config:
        from_attributes = True


# --- Schema for internal use by service/CRUD layer to create user in DB ---
class UserCreateInternal(UserBase):  # Inherits from UserBase
    """
    Internal schema for creating a user, used by CRUD operations.
    Accepts hashed_password instead of plain password.
    """
    hashed_password: str  # This is now the password field for internal creation

    # Fields that are part of User model but might not be in UserBase,
    # or need specific defaults for internal creation different from API creation.
    # UserCreate (API input) defines role, is_active, is_superuser defaults for API.
    # Here, we ensure they are present for DB creation if not in UserBase.
    role: UserRoleEnum  # This field must be provided when creating UserCreateInternal instance
    # is_active is in UserBase with default True
    # is_superuser is in UserBase with default False
    is_email_verified: bool = False  # Default for new users internally


# Schema for updating password by the user themselves
class UserUpdatePassword(BaseModel):
    current_password: str
    new_password: str = PydanticField(min_length=8)
