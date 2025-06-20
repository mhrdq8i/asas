from logging import getLogger
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import List

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.user_crud import CRUDUser
from src.crud.incident_crud import CrudIncident
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
    decode_token,
    create_access_token
)
from src.exceptions.common_exceptions import (
    DuplicateResourceException,
    InvalidOperationException,
    InvalidInputException
)
from src.exceptions.user_exceptions import (
    AuthenticationFailedException,
    UserNotFoundException,
    UserAlreadyDeletedException,
    CannotDeleteActiveCommanderException,
)
from src.core.config import settings
from src.core.celery import celery_app


logger = getLogger(__name__)


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session: AsyncSession = db_session
        self.crud_user = CRUDUser(db_session=self.db_session)
        self.crud_incident = CrudIncident(db_session=self.db_session)

    async def get_user_by_id(self, *, user_id: UUID) -> User:
        """
        Retrieves a user by their ID. Raises an exception if not found.
        """
        user = await self.crud_user.get_user_by_id(user_id=user_id)
        if not user:
            raise UserNotFoundException(identifier=str(user_id))
        return user

    async def get_users_list(
        self,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """
        Retrieves a paginated list of all users.
        """

        return await self.crud_user.get_users(skip=skip, limit=limit)

    async def get_commander_list(self) -> List[User]:
        """
        Retrieves a list of all active users designated as commanders.
        """

        return await self.crud_user.get_commanders()

    async def register_user(self, *, user_in: UserCreate) -> User:
        """
        Creates a new user, checking for uniqueness
        and queuing a verification email.
        """

        existing_user = await self.crud_user.get_user_by_username_or_email(
            username=user_in.username,
            email=user_in.email
        )

        if existing_user:
            detail = f"Username '{user_in.username}' is already registered."\
                if existing_user.username.lower(
                ) == user_in.username.lower() else \
                f"Email '{user_in.email}' is already registered."

            raise DuplicateResourceException(detail=detail)

        hashed_password = get_password_hash(user_in.password)

        user_data = UserCreateInternal(
            **user_in.model_dump(),
            hashed_password=hashed_password
        )

        created_user = await self.crud_user.create_user(user_in=user_data)
        await self.db_session.commit()
        await self.db_session.refresh(created_user)

        try:
            celery_app.send_task(
                "tasks.send_verification_email",
                args=[str(created_user.id)]
            )

            logger.info(
                "Verification email task queued for "
                f"user ID: {created_user.id}"
            )

        except Exception as e:
            logger.error(
                "Failed to queue verification email task for user "
                f"{created_user.id}: {e}", exc_info=True
            )

        return created_user

    async def update_user_profile(
        self,
        *,
        current_user: User,
        user_in: UserUpdate
    ) -> User:
        """
        Updates the profile of the currently authenticated user.
        """

        update_data = user_in.model_dump(exclude_unset=True)

        if not update_data:
            raise InvalidInputException("No fields provided for update.")

        # If email is being updated,
        # check if it's already taken by another user
        if "email" in update_data and update_data[
            "email"
        ] != current_user.email:
            existing_user = await self.crud_user.get_user_by_email(
                email=update_data["email"]
            )

            if existing_user:
                raise DuplicateResourceException(
                    f"Email '{update_data['email']}' is already in use."
                )

        # If username is being updated, check if it's already taken
        if "username" in update_data and update_data[
                "username"
        ] != current_user.username:
            existing_user = await self.crud_user.get_user_by_username(
                username=update_data["username"]
            )

            if existing_user:
                raise DuplicateResourceException(
                    f"Username '{update_data['username']}' is already taken."
                )

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )
        await self.db_session.commit()
        await self.db_session.refresh(updated_user)

        logger.info(
            f"User profile updated for user: {current_user.username}"
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
            raise InvalidInputException("Incorrect current password.")

        if password_in.current_password == password_in.new_password:
            raise InvalidInputException(
                "New password cannot be the same as the old password."
            )

        new_hashed_password = get_password_hash(password_in.new_password)

        update_data = {"hashed_password": new_hashed_password}

        updated_user = await self.crud_user.update_user(
            db_user_to_update=current_user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()

        logger.info(
            f"Password changed successfully for user: {current_user.username}"
        )

        return updated_user

    async def soft_delete_user(
        self,
        *,
        user_to_delete_id: UUID,
        performing_user: User
    ) -> User:
        """
        Soft deletes a user. Only a superuser can perform this action.
        """

        if user_to_delete_id == performing_user.id:
            raise InvalidOperationException(
                "Admins cannot delete their own account."
            )

        user_to_delete = await self.get_user_by_id(user_id=user_to_delete_id)

        if not user_to_delete.is_active:
            raise UserAlreadyDeletedException()

        is_active_commander = await \
            self.crud_incident.is_user_active_commander(
                user_id=user_to_delete.id
            )

        if is_active_commander:
            raise CannotDeleteActiveCommanderException()

        update_data = {
            "is_active": False,
            "is_email_verified": False,
            "is_superuser": False,
            "is_commander": False,
            "role": performing_user.role
        }

        deleted_user = await self.crud_user.update_user(
            db_user_to_update=user_to_delete,
            user_in_update_data=update_data
        )

        await self.db_session.commit()
        await self.db_session.refresh(deleted_user)

        logger.warning(
            f"User '{user_to_delete.username}' (ID: {user_to_delete.id}) "
            f"was soft-deleted by admin '{performing_user.username}'."
        )

        return deleted_user

    async def authenticate_user(
        self,
        *,
        username: str,
        password: str,
        client_ip: str | None = None
    ) -> User:

        user = await self.crud_user.get_user_by_username(
            username=username
        )

        if not user or not verify_password(
            password, user.hashed_password
        ):
            raise AuthenticationFailedException()

        if not user.is_active:
            raise AuthenticationFailedException(
                detail="Inactive user."
            )

        if not user.is_email_verified:
            raise AuthenticationFailedException(
                detail="Email not verified. Please check your inbox."
            )

        update_data = {
            "last_login_at": datetime.now(timezone.utc),
            "last_login_ip": client_ip
        }

        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()
        await self.db_session.refresh(updated_user)

        logger.info(
            f"User '{username}' authenticated successfully "
            f"from IP: {client_ip}"
        )

        return updated_user

    async def request_new_verification_email(
        self,
        *,
        current_user: User
    ) -> str:

        if current_user.is_email_verified:
            raise InvalidOperationException("Email is already verified.")

        try:
            celery_app.send_task(
                "tasks.send_verification_email",
                args=[str(current_user.id)]
            )

            logger.info(
                f"Re-queued verification email for user ID: {current_user.id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to re-queue verification email task: {e}",
                exc_info=True
            )

        message_to_client = (
            "If your account is eligible, "
            "a new verification link has "
            "been sent to your email address."
        )

        return message_to_client

    async def prepare_password_reset_data(
        self,
        *,
        email_in: PasswordResetRequest
    ) -> str:

        user = await self.crud_user.get_user_by_email(email=email_in.email)

        message_to_client = (
            "If an account with this email exists, "
            "a password reset link has been sent."
        )

        if user and user.is_active:
            expires_delta = timedelta(
                minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES
            )

            reset_token = create_access_token(
                subject={
                    "sub": str(user.id),
                    "type": "password_reset"
                },
                expires_delta=expires_delta
            )

            update_data = {
                "reset_token": get_password_hash(reset_token),
                "reset_token_expires": datetime.now(
                    timezone.utc) + expires_delta
            }

            await self.crud_user.update_user(
                db_user_to_update=user,
                user_in_update_data=update_data
            )
            await self.db_session.commit()

            try:
                celery_app.send_task(
                    "tasks.send_password_reset_email",
                    args=[str(user.id),
                          reset_token]
                )

                logger.info(
                    f"Password reset task queued for user: {user.email}"
                )

            except Exception as e:
                logger.error(
                    "Failed to queue password reset "
                    f"task for {user.email}: {e}",
                    exc_info=True
                )

        return message_to_client

    async def confirm_password_reset(
        self,
        *,
        token_in: str,
        new_password_in: PasswordResetConfirm
    ) -> User:

        payload = decode_token(token_in)

        if not payload or payload.get("type") != "password_reset":
            raise InvalidInputException(
                "Invalid or expired password reset token."
            )

        user_id = UUID(payload.get("sub"))

        user = await self.crud_user.get_user_by_id(user_id=user_id)

        if not user or not user.is_active or not user.reset_token \
                or not user.reset_token_expires:
            raise UserNotFoundException(
                "User not found or no pending reset."
            )

        if datetime.now(timezone.utc) > user.reset_token_expires:
            raise InvalidInputException(
                "Password reset token has expired."
            )

        if not verify_password(token_in, user.reset_token):
            raise InvalidInputException(
                "Invalid password reset token."
            )

        new_hashed_password = get_password_hash(
            new_password_in.new_password
        )

        update_data = {
            "hashed_password": new_hashed_password,
            "reset_token": None,
            "reset_token_expires": None
        }

        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()

        return updated_user

    async def confirm_email_verification(self, *, token_in: str) -> User:

        payload = decode_token(token_in)

        if not payload or payload.get("type") != "email_verification":
            raise InvalidInputException(
                "Invalid or expired email verification token."
            )

        user_id = UUID(payload.get("sub"))

        user = await self.crud_user.get_user_by_id(user_id=user_id)

        if not user or not user.is_active or not user.email_verification_token:
            raise InvalidInputException("Invalid token or user state.")

        if not verify_password(token_in, user.email_verification_token):
            raise InvalidInputException("Invalid email verification token.")

        update_data = {
            "is_email_verified": True,
            "email_verification_token": None,
            "email_verified_at": datetime.now(timezone.utc),
        }

        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()

        try:
            # Assuming you will create this
            # task to send a welcome email
            # celery_app.send_task(
            # "tasks.send_welcome_email",
            # args=[str(updated_user.id)]
            # )

            logger.info(
                "Welcome email task can be queued for verified "
                f"user ID: {updated_user.id}"
            )

        except Exception as e:
            logger.error(
                f"Failed to queue welcome email task: {e}",
                exc_info=True
            )

        return updated_user
