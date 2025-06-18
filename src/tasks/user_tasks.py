import asyncio
from uuid import UUID
from datetime import timedelta

from src.core.celery import celery_app
from src.database.session import (
    AsyncSessionLocal
)
from src.crud.user_crud import CRUDUser
from src.services.notification_service import (
    NotificationService
)
from src.core.email_utils import (
    send_email_verification,
    send_password_reset_email
)
from src.core.security import (
    create_access_token,
    get_password_hash
)
from src.core.config import settings


# --- Async Helper for Verification Email ---
async def _send_verification_email_async(user_id: str):
    """
    Async helper to generate a token and send an email verification link.
    This contains the core logic and is called by the Celery task.
    """

    session = AsyncSessionLocal()

    try:
        user_crud = CRUDUser(db_session=session)

        user = await user_crud.get_user_by_id(user_id=UUID(user_id))

        if not user or user.is_email_verified:
            status = "already verified" if user \
                and user.is_email_verified else "not found"
            print(
                f"User {user_id} {status}. "
                "Aborting verification email task."
            )

            return

        # Generate the verification token

        expires_delta = timedelta(
            minutes=settings.EMAIL_VERIFY_TOKEN_EXPIRE_MINUTES
        )

        token_payload = {
            "sub": str(user.id),
            "type": "email_verification"
        }

        email_verification_token = create_access_token(
            subject=token_payload,
            expires_delta=expires_delta
        )

        # Store the hash of the token in the DB to validate it later
        update_data = {
            "email_verification_token": get_password_hash(
                email_verification_token
            )
        }

        await user_crud.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        # Must commit the change to the database
        await session.commit()

        # Send the actual email
        await send_email_verification(
            email_to=user.email,
            username=user.username,
            verification_token=email_verification_token,
        )
    finally:
        await session.close()


# --- Celery Task for Verification Email ---
@celery_app.task(
    name="tasks.send_verification_email",
    bind=True, max_retries=3
)
def send_verification_email_task(self, user_id: str):
    """
    Synchronous Celery task wrapper for sending the verification email.
    """

    print(
        f"Executing verification email task for user_id: {user_id}"
    )

    try:
        asyncio.run(_send_verification_email_async(user_id))

    except Exception as e:
        print(
            f"Error in verification email task for user {user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Verification email task for user {user_id} completed."


# --- Async Helper for Welcome Email ---
async def _send_welcome_email_async(user_id: str):
    """
    Async helper to send a welcome email after verification.
    """

    session = AsyncSessionLocal()

    try:
        user_crud = CRUDUser(db_session=session)
        notification_service = NotificationService()
        user = await user_crud.get_user_by_id(user_id=UUID(user_id))

        if user:
            await notification_service.send_welcome_email(user=user)

    finally:
        await session.close()


# --- Celery Task for Welcome Email ---
@celery_app.task(
    name="tasks.send_welcome_email",
    bind=True, max_retries=3
)
def send_welcome_email_task(self, user_id: str):
    """
    Celery task to send a welcome email.
    """

    print(
        f"Executing welcome email task for user_id: {user_id}"
    )

    try:
        asyncio.run(_send_welcome_email_async(user_id))

    except Exception as e:
        print(
            f"Error in welcome email task for user {user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Welcome email task for user {user_id} completed."


# --- Async Helper for Password Reset Email ---
async def _send_password_reset_async(user_id: str, token: str):
    """
    Async helper to send a password reset email.
    """

    session = AsyncSessionLocal()

    try:
        user_crud = CRUDUser(db_session=session)
        user = await user_crud.get_user_by_id(user_id=UUID(user_id))
        if user:
            await send_password_reset_email(
                email_to=user.email,
                username=user.username,
                reset_token=token
            )

    finally:
        await session.close()


# --- Celery Task for Password Reset ---
@celery_app.task(
    name="tasks.send_password_reset_email",
    bind=True, max_retries=3
)
def send_password_reset_email_task(self, user_id: str, token: str):
    """Celery task to send a password reset email."""

    print(
        f"Executing password reset task for user_id: {user_id}"
    )

    try:
        asyncio.run(_send_password_reset_async(user_id, token))

    except Exception as e:
        print(
            f"Error in password reset task for user {user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Password reset task for user {user_id} completed."
