from logging import getLogger
from uuid import UUID
from datetime import (
    datetime,
    timedelta,
    timezone
)

from sqlmodel.ext.asyncio.session import AsyncSession

from src.crud.user_crud import CRUDUser
from src.models.user import User
from src.api.v1.schemas.user_schemas import (
    UserCreate,
    UserCreateInternal
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
    UserNotFoundException
)
from src.core.config import settings
from src.core.celery import celery_app


logger = getLogger(__name__)


class UserService:
    def __init__(self, db_session: AsyncSession):
        self.db_session: AsyncSession = db_session
        self.crud_user = CRUDUser(db_session=self.db_session)

    async def register_user(self, *, user_in: UserCreate) -> User:
        """
        Creates a new user and queues a verification email task via Celery.
        """

        existing_user = await self.crud_user.get_user_by_username_or_email(
            username=user_in.username, email=user_in.email
        )

        if existing_user:
            raise DuplicateResourceException(
                detail="Username or email is already registered."
            )

        hashed_password = get_password_hash(user_in.password)
        user_data = UserCreateInternal(
            **user_in.model_dump(),
            hashed_password=hashed_password
        )

        created_user = await self.crud_user.create_user(
            user_in=user_data
        )
        await self.db_session.commit()

        try:
            celery_app.send_task(
                "tasks.send_verification_email",
                args=[str(created_user.id)]
            )

            logger.info(
                "Verification email task queued for user ID: "
                f"{created_user.id}"
            )

        except Exception as e:
            logger.error(
                "Failed to queue verification email task for user "
                f"{created_user.id}: {e}",
                exc_info=True
            )

        return created_user

    async def request_new_verification_email(
        self,
        *,
        current_user: User
    ) -> str:
        """
        Checks if a new verification email can be sent and queues the task.
        """

        if current_user.is_email_verified:
            raise InvalidOperationException(
                detail="Email is already verified."
            )

        try:
            celery_app.send_task(
                "tasks.send_verification_email",
                args=[str(current_user.id)]
            )

            logger.info(
                f"Re-queued verification email for user ID: {current_user.id}"
            )

        except Exception as e:
            logger.error(f"Failed to re-queue verification email task: {e}")

        return (
            "If your account is eligible, "
            "a new verification link has been "
            "sent to your email address."
        )

    async def prepare_password_reset_data(
        self,
        *,
        email_in: PasswordResetRequest
    ) -> str:
        """
        Prepares data for password reset,
        queues the email task,
        and returns a message.
        """

        user = await self.crud_user.get_user_by_email(
            email=email_in.email
        )

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
                    timezone.utc
                ) + expires_delta,
            }

            await self.crud_user.update_user(
                db_user_to_update=user,
                user_in_update_data=update_data
            )

            await self.db_session.commit()

            try:
                celery_app.send_task(
                    "tasks.send_password_reset_email",
                    args=[str(user.id), "dummy_token"]
                )

                logger.info(
                    f"Password reset task queued for user: {user.email}"
                )

            except Exception as e:
                logger.error(
                    f"Failed to queue password reset task for "
                    f"{user.email}: {e}", exc_info=True
                )

        return message_to_client

    async def confirm_password_reset(
        self,
        *,
        token_in: str,
        new_password_in: PasswordResetConfirm
    ) -> User:
        """
        Confirms the password reset using a token and new password.
        """

        payload = decode_token(token_in)

        if not payload or payload.get(
            "type"
        ) != "password_reset":
            raise InvalidInputException(
                detail="Invalid or expired password reset token."
            )

        user_id = UUID(payload.get("sub"))

        user = await self.crud_user.get_user_by_id(
            user_id=user_id
        )

        if not user or not user.is_active \
                or not user.reset_token or not user.reset_token_expires:

            raise UserNotFoundException(
                detail="User not found or no pending reset."
            )

        if datetime.now(timezone.utc) > user.reset_token_expires:

            raise InvalidInputException(
                detail="Password reset token has expired."
            )

        if not verify_password(token_in, user.reset_token):
            raise InvalidInputException(
                detail="Invalid password reset token."
            )

        new_hashed_password = get_password_hash(new_password_in.new_password)

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

    async def confirm_email_verification(
        self,
        *,
        token_in: str
    ) -> User:
        """
        Verifies a user's email based on the
        token and queues a welcome email task.
        """

        payload = decode_token(token_in)

        if not payload or payload.get(
            "type"
        ) != "email_verification":
            raise InvalidInputException(
                detail="Invalid or expired email verification token."
            )

        user_id = UUID(payload.get("sub"))

        user = await self.crud_user.get_user_by_id(user_id=user_id)

        if not user or not user.is_active \
                or not user.email_verification_token:

            raise InvalidInputException(
                detail="Invalid token or user state."
            )

        if not verify_password(token_in, user.email_verification_token):
            raise InvalidInputException(
                detail="Invalid email verification token."
            )

        update_data = {
            "is_email_verified": True,
            "email_verification_token": None,
            "email_verified_at": datetime.now(timezone.utc)
        }

        updated_user = await self.crud_user.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        await self.db_session.commit()

        try:
            celery_app.send_task(
                "tasks.send_welcome_email",
                args=[str(updated_user.id)]
            )

            logger.info(
                "Welcome email task queued for verified "
                f"user ID: {updated_user.id}"
            )

        except Exception as e:
            logger.error(f"Failed to queue welcome email task: {e}")

        return updated_user

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

        return updated_user
