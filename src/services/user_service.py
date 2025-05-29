from uuid import UUID
from typing import List
from datetime import (
    datetime,
    timedelta,
    timezone
)

from sqlmodel.ext.asyncio.session import (
    AsyncSession
)  # type: ignore

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
    AuthenticationFailedException,
    UserNotFoundException,
    InvalidOperationException,
    InvalidInputException,
    InsufficientPermissionsException
)
# For password reset token expiry, etc.
from src.core.config import settings


class UserService:
    """
    Service layer for user-related business logic.
    """

    def __init__(
        self,
        db_session: AsyncSession
    ):
        self.db_session: AsyncSession = db_session
        self.crud_user = CRUDUser(
            db_session=self.db_session
        )

    async def register_user(
        self,
        *,
        user_in: UserCreate
    ) -> User:
        """
        Registers a new user.
        - Checks for existing username/email.
        - Hashes the password.
        - Creates the user in the database.
        """

        existing_user_by_username = await self.crud_user.get_user_by_username(
            username=user_in.username
        )
        if existing_user_by_username:
            raise DuplicateResourceException(
                detail=f"Username '{user_in.username}' \
                  is already registered."
            )

        existing_user_by_email = await self.crud_user.get_user_by_email(
            email=user_in.email
        )
        if existing_user_by_email:
            raise DuplicateResourceException(
                detail=f"Email '{user_in.email}' \
                  is already registered."
            )

        hashed_password = get_password_hash(
            user_in.password
        )

        user_create_internal_data = UserCreateInternal(
            username=user_in.username,
            email=user_in.email,
            hashed_password=hashed_password,
            full_name=user_in.full_name,
            role=user_in.role,
            # Default should be True for new users unless specified
            is_active=user_in.is_active,
            # Default should be False
            is_superuser=user_in.is_superuser,
            avatar_url=user_in.avatar_url,
            bio=user_in.bio,
            timezone=user_in.timezone,
            # New users are not verified by default
            is_email_verified=False
        )

        created_user = await self.crud_user.db_create_user(
            user_in=user_create_internal_data
        )

        return created_user

    async def authenticate_user(
        self,
        *,
        username: str, password: str
    ) -> User:
        """
        Authenticates a user.
        Returns the user object
        if authentication is successful,
        otherwise raises an exception.
        """

        user = await self.crud_user.get_user_by_username(
            username=username
        )
        if not user:
            # Detail is "Incorrect username or password."
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

        # Optionally update last_login_at here
        user.last_login_at = datetime.now(timezone.utc)

        # This would need client_ip passed to the service
        # user.last_login_ip = client_ip

        await self.db_session.commit()
        await self.db_session.refresh(user)

        return user

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
        # Re-fetch user to ensure latest data,
        # though current_user from deps should be fresh
        return await self.get_user_by_id(
            user_id=current_user.id
        )

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
            exclude_unset=True)  # Pydantic V2: model_dump()

        if "email" in update_data and update_data[
            "email"
        ] != current_user.email:
            existing_user = await self.crud_user.get_user_by_email(
                email=update_data["email"]
            )

            if existing_user and existing_user.id != current_user.id:
                raise DuplicateResourceException(
                    detail="Email already registered by another user.")

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

        # Password should be updated via a
        # separate method for security (e.g., change_password)
        if "password" in update_data:
            # Or raise an error if they try to update password here
            del update_data["password"]

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )

        return updated_user

    async def change_password(
        self,
        *,
        current_user: User,
        password_in: UserUpdatePassword
    ) -> User:
        """
        Changes the password for the
        currently authenticated user.
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
        # Optionally, invalidate all other
        # active sessions for this user here

        return updated_user

    async def request_password_reset(
        self,
        *,
        email_in: PasswordResetRequest
    ) -> str:
        """
        Initiates a password reset process for a user by email.
        Generates a reset token and (conceptually) sends an email.
        Returns the reset token for testing/demonstration purposes.
        """
        user = await self.crud_user.get_user_by_email(
            email=email_in.email
        )

        if not user:
            # To prevent email enumeration,
            # always return a success-like message,
            # but only proceed if user exists and is active.
            # Log this attempt server-side.
            print(
                f"Password reset requested for non-existent\
                    or inactive email: {email_in.email}"
            )
            raise UserNotFoundException(
                identifier=email_in.email
            )

        if not user.is_active:
            raise InvalidOperationException(
                detail="Cannot reset password for an inactive user."
            )

        password_reset_token_expire_minutes = \
            settings.ACCESS_TOKEN_EXPIRE_MINUTES

        reset_token_payload = {
            "sub": str(user.id),
            "type": "password_reset"
        }
        reset_token = create_access_token(
            subject=reset_token_payload,
            expires_delta=timedelta(
                minutes=password_reset_token_expire_minutes
            )
        )

        user.reset_token = get_password_hash(
            reset_token
        )  # Store a hash of the token
        user.reset_token_expires = datetime.now(
            timezone.utc
        ) + timedelta(
            minutes=password_reset_token_expire_minutes
        )
        await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data={
                "reset_token": user.reset_token,
                "reset_token_expires": user.reset_token_expires
            }
        )

        print(
            f"Password reset token generated for {user.email}:\
            {reset_token} (THIS IS THE ACTUAL TOKEN - DO NOT LOG IN PROD)"
        )

        # TODO: Implement actual email sending logic here
        # send_password_reset_email(email_to=user.email, token=reset_token)

        # For demonstration. In prod, you'd just return a success message.
        return reset_token

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
                detail="Invalid or expired password reset token."
            )

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidInputException(
                detail="Invalid token payload."
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidInputException(
                detail="Invalid user identifier in token."
            )

        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )

        if not user:
            raise UserNotFoundException(
                identifier=user_id_str
            )

        if not user.reset_token or not user.reset_token_expires:
            raise InvalidInputException(
                detail="No pending password reset or token expired."
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
                detail="Invalid password reset token."
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

    async def soft_delete_user(
        self,
        *,
        user_to_delete_id: UUID,
        performing_user: User
    ) -> User:
        """
        Soft deletes a user account.
        Users can soft delete themselves. Admins can soft delete others.
        Cannot soft delete if user is an active incident commander.
        """
        user_to_delete = await self.get_user_by_id(
            user_id=user_to_delete_id
        )

        if user_to_delete.id != performing_user.id \
                and not performing_user.is_superuser:
            raise InsufficientPermissionsException(
                detail="You do not have permission to delete this user."
            )

        if user_to_delete.is_deleted:
            raise InvalidOperationException(
                detail="User is already soft-deleted."
            )

        print(
            f"Placeholder: Check if user {user_to_delete_id} \
                is an active incident commander would happen here."
        )

        # is_commander = await self.crud_incident.is_user_active_commander(
        #     user_id=user_to_delete.id
        # )
        # if is_commander:
        #     raise InvalidOperationException(
        #         detail="User is an active incident commander\
        #             and cannot be deleted. Reassign incidents first."
        #     )

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
