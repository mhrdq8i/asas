from uuid import UUID
from typing import List
from datetime import datetime, timedelta, timezone

from sqlmodel.ext.asyncio.session import AsyncSession  # type: ignore

from src.crud.crud_user import CRUDUser
from src.models.user import User
from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserCreateInternal,
    UserUpdate,
    UserUpdatePassword
)
from src.api.v1.schemas.auth_schemas import (
    PasswordResetRequest,
    PasswordResetConfirm
)
from src.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_token
)
from src.exceptions.common_exceptions import (
    DuplicateResourceException,
    InvalidOperationException,
    InvalidInputException,
)
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    InsufficientPermissionsException,
    UserNotFoundException,

)
from src.core.config import settings


class UserService:
    """
    Service layer for user-related business logic.
    """

    def __init__(self, db_session: AsyncSession):
        self.db_session: AsyncSession = db_session
        self.crud_user = CRUDUser(
            db_session=self.db_session
        )

    async def register_user(self, *, user_in: UserCreate) -> User:
        """
        Registers a new user.
        """
        existing_user_by_username = await self.crud_user.get_user_by_username(
            username=user_in.username
        )
        if existing_user_by_username:
            raise DuplicateResourceException(
                detail=f"Username '{user_in.username}' is already registered.")

        existing_user_by_email = await self.crud_user.get_user_by_email(
            email=user_in.email
        )
        if existing_user_by_email:
            raise DuplicateResourceException(
                detail=f"Email '{user_in.email}' is already registered."
            )

        hashed_password = get_password_hash(user_in.password)

        user_create_internal_data = UserCreateInternal(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            is_active=True,
            is_superuser=user_in.is_superuser,
            avatar_url=user_in.avatar_url,
            bio=user_in.bio,
            timezone=user_in.timezone,
            is_email_verified=False
        )

        created_user = await self.crud_user.db_create_user(
            user_in=user_create_internal_data
        )
        # TODO: Optionally, trigger email verification process here
        # await self.request_email_verification_token(created_user)
        return created_user

    async def authenticate_user(
        self,
        *,
        username: str,
        password: str,
        client_ip: str | None = None
    ) -> User:
        """
        Authenticates a user.
        Returns the user object if authentication is successful, otherwise raises an exception.
        Optionally updates last_login_ip.
        """
        user = await self.crud_user.get_user_by_username(
            username=username
        )
        if not user:
            raise AuthenticationFailedException()

        if not verify_password(
            password,
            user.hashed_password
        ):
            raise AuthenticationFailedException()

        if not user.is_active:
            raise AuthenticationFailedException(
                detail="Inactive user.\
                      Please verify your email or contact support."
            )

        update_data = {"last_login_at": datetime.now(timezone.utc)}
        if client_ip:
            update_data["last_login_ip"] = client_ip

        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )
        return updated_user

    async def get_user_by_id(
            self,
            *,
            user_id: UUID
    ) -> User:
        """
        Retrieves a user by ID. Raises UserNotFoundException if not found.
        """
        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )
        if not user:
            raise UserNotFoundException(
                identifier=str(user_id)
            )

        return user

    async def get_user_profile(
        self,
        *,
        current_user: User
    ) -> User:
        """
        Returns the profile of the currently authenticated user.
        """

        return current_user

    async def update_user_profile(
            self,
            *,
            current_user: User,
            user_in: UserUpdate
    ) -> User:
        """
        Updates the profile of the currently authenticated user.
        """
        update_data = user_in.model_dump(
            exclude_unset=True
        )

        if "email" in update_data and update_data[
            "email"
        ] != current_user.email:
            existing_user = await self.crud_user.get_user_by_email(
                email=update_data["email"]
            )
            if existing_user and existing_user.id != current_user.id:
                raise DuplicateResourceException(
                    detail="Email already registered by another user."
                )
            update_data["is_email_verified"] = False

        if "username" in update_data and update_data[
            "username"
        ] != current_user.username:
            existing_user = await self.crud_user.get_user_by_username(
                username=update_data["username"]
            )
            if existing_user and existing_user.id != current_user.id:
                raise DuplicateResourceException(
                    detail="Username already taken by another user."
                )

        if "password" in update_data:
            del update_data["password"]

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user, user_in_update_data=update_data
        )

        return updated_user

    async def change_password(
            self,
            *,
            current_user: User,
            password_in: UserUpdatePassword
    ) -> User:
        """
        Changes the password for the currently authenticated user.
        """
        if not verify_password(
            password_in.current_password,
            current_user.hashed_password
        ):
            raise AuthenticationFailedException(
                detail="Incorrect current password."
            )

        if password_in.current_password == password_in.new_password:
            raise InvalidInputException(
                detail="New password cannot be the\
                      same as the current password."
            )

        new_hashed_password = get_password_hash(
            password_in.new_password
        )
        update_data = {
            "hashed_password": new_hashed_password
        }

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )

        return updated_user

    async def request_password_reset(
            self,
            *,
            email_in: PasswordResetRequest
    ) -> str:
        """
        Initiates a password reset process for a user by email.
        """
        user = await self.crud_user.get_user_by_email(
            email=email_in.email
        )
        if not user or not user.is_active:
            print(
                f"Password reset requested for email: {email_in.email}. User found: {bool(user)}, Active: {user.is_active if user else 'N/A'}")

            return "If an account with this email exists and is active, a password reset link has been sent."

        password_reset_token_expire_minutes = getattr(
            settings,
            'PASSWORD_RESET_TOKEN_EXPIRE_MINUTES',
            15
        )

        reset_token_payload = {
            "sub": str(user.id),
            "type": "password_reset",
            "email": user.email
        }
        reset_token = create_access_token(
            subject=reset_token_payload,
            expires_delta=timedelta(
                minutes=password_reset_token_expire_minutes)
        )

        update_data = {
            "reset_token": get_password_hash(reset_token),
            "reset_token_expires": datetime.now(
                timezone.utc
            ) + timedelta(
                minutes=password_reset_token_expire_minutes
            )
        }
        await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        print(
            f"TODO: Send password reset email to {user.email} with token: {reset_token}")

        return "If your email is registered and active,\
              you will receive a password reset link shortly."

    async def confirm_password_reset(
            self,
            *,
            token_in: str,
            new_password_in: PasswordResetConfirm
    ) -> User:
        """
        Resets a user's password using a valid reset token.
        """
        payload = decode_token(token_in)
        if not payload or payload.get(
            "type"
        ) != "password_reset":
            raise InvalidInputException(
                detail="Invalid or expired password reset token\
                      (type or payload error)."
            )

        user_id_str = payload.get("sub")
        token_email = payload.get("email")

        if not user_id_str:
            raise InvalidInputException(
                detail="Invalid token payload (missing subject)."
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidInputException(
                detail="Invalid user identifier format in token."
            )

        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )
        if not user or not user.is_active:
            raise UserNotFoundException(
                detail="User not found, inactive, or token mismatch."
            )

        if token_email and user.email.lower() != token_email.lower():
            raise InvalidInputException(
                detail="Token does not match user email."
            )

        if not user.reset_token or not user.reset_token_expires:
            raise InvalidInputException(
                detail="No pending password reset for this user or token already used."
            )

        if datetime.now(timezone.utc) > user.reset_token_expires:
            await self.crud_user.update_user(
                db_user_to_update=user,
                user_in_update_data={
                    "reset_token": None,
                    "reset_token_expires": None
                }
            )
            raise InvalidInputException(
                detail="Password reset token has expired."
            )

        if not verify_password(
            token_in,
            user.reset_token
        ):
            raise InvalidInputException(
                detail="Invalid password reset token (verification failed)."
            )

        new_hashed_password = get_password_hash(
            new_password_in.new_password
        )
        update_data = {
            "hashed_password": new_hashed_password,
            "reset_token": None,
            "reset_token_expires": None,
            "is_email_verified": True
        }
        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        return updated_user

    async def request_email_verification_token(
            self,
            *,
            current_user: User
    ) -> str:
        """
        Generates an email verification token for the currently authenticated user
        and (conceptually) sends an email.
        """
        if current_user.is_email_verified:
            raise InvalidOperationException(
                detail="Email is already verified."
            )
        if not current_user.is_active:
            raise InvalidOperationException(
                detail="Cannot verify email for an inactive user."
            )

        email_verify_token_expire_minutes = getattr(
            settings,
            'EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES',
            1440
        )

        verify_token_payload = {
            "sub": str(current_user.id),
            "type": "email_verification",
            "email": current_user.email
        }
        email_verification_token = create_access_token(
            subject=verify_token_payload,
            expires_delta=timedelta(
                minutes=email_verify_token_expire_minutes
            )
        )

        update_data = {
            "email_verification_token": get_password_hash(
                email_verification_token
            )
        }
        # You might want to add
        # email_verification_token_expires_at
        # to User model if needed
        await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )

        print(
            f"TODO: Send email verification to {current_user.email} with token: {email_verification_token}")

        return "An email verification link has been sent to your email address."

    async def confirm_email_verification(
        self,
        *,
        token_in: str
    ) -> User:
        """
        Verifies a user's email using a valid verification token.
        """
        payload = decode_token(token_in)
        if not payload or payload.get(
            "type"
        ) != "email_verification":
            raise InvalidInputException(
                detail="Invalid or expired email verification token\
                      (type or payload error)."
            )

        user_id_str = payload.get("sub")
        token_email = payload.get("email")

        if not user_id_str:
            raise InvalidInputException(
                detail="Invalid token payload (missing subject)."
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidInputException(
                detail="Invalid user identifier format in token."
            )

        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )
        if not user:
            raise UserNotFoundException(
                detail="User not found or token mismatch."
            )

        if user.is_email_verified:
            return user

        if not user.email_verification_token:
            raise InvalidInputException(
                detail="No pending email verification for\
                      this user or token already used/invalid."
            )

        if not verify_password(
            token_in,
            user.email_verification_token
        ):
            raise InvalidInputException(
                detail="Invalid email verification token."
            )

        # Check if token_email exists before lower()
        if token_email and user.email.lower() != token_email.lower():
            raise InvalidInputException(
                detail="Token email mismatch during verification."
            )

        update_data = {
            "is_email_verified": True,
            "email_verification_token": None,
            "email_verified_at": datetime.now(timezone.utc),
            "is_active": True
        }
        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        return updated_user

    async def soft_delete_user(
            self,
            *,
            user_to_delete_id: UUID,
            performing_user: User
    ) -> User:
        """
        Soft deletes a user account.
        """
        user_to_delete = await self.get_user_by_id(
            user_id=user_to_delete_id
        )

        if user_to_delete.id != performing_user.id and not performing_user.is_superuser:
            raise InsufficientPermissionsException()

        if user_to_delete.is_deleted:
            raise InvalidOperationException(
                detail="User is already soft-deleted."
            )

        print(
            f"Placeholder: Check if user {user_to_delete_id} is an active incident commander would happen here.")
        # is_commander = await self.crud_incident.is_user_active_commander(user_id=user_to_delete.id)
        # if is_commander:
        #     raise InvalidOperationException(detail="User is an active incident commander and cannot be deleted.")

        update_data = {
            "is_deleted": True,
            "deleted_at": datetime.now(timezone.utc),
            "is_active": False
        }
        deleted_user = await self.crud_user.update_user(
            db_user_to_update=user_to_delete,
            user_in_update_data=update_data
        )

        return deleted_user

    async def get_users_list(
            self,
            *,
            skip: int = 0,
            limit: int = 100
    ) -> List[User]:
        """
        Retrieves a list of users (e.g., for admin panel).
        """
        return await self.crud_user.get_users(
            skip=skip,
            limit=limit
        )
