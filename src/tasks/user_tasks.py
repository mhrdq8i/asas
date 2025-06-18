import asyncio
from uuid import UUID
from src.core.celery import celery_app
from src.database.session import AsyncSessionLocal
from src.crud.user_crud import CRUDUser
from src.services.notification_service import (
    NotificationService
)
from src.core.email_utils import (
    send_email_verification,
    send_password_reset_email
)


# --- Async Helper for Verification Email ---
async def _send_verification_email_async(user_id: str):
    session = AsyncSessionLocal()
    try:
        from src.services.user_service import UserService
        user_service = UserService(db_session=session)
        (
            user, token, _
        ) = await user_service.prepare_email_verification_data(
            user_id=UUID(user_id)
        )
        if user and token:
            await send_email_verification(
                email_to=user.email,
                username=user.username,
                verification_token=token,
            )
    finally:
        await session.close()


# --- Celery Task for Verification Email ---
@celery_app.task(
    name="tasks.send_verification_email",
    bind=True, max_retries=3
)
def send_verification_email_task(self, user_id: str):
    print(
        f"Executing verification email task for user_id: {user_id}"
    )
    try:
        asyncio.run(
            _send_verification_email_async(user_id)
        )
    except Exception as e:
        print(
            "Error in verification email task for user "
            f"{user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Verification email task for user {user_id} completed."


# --- Async Helper for Welcome Email ---
async def _send_welcome_email_async(user_id: str):
    session = AsyncSessionLocal()
    try:
        user_crud = CRUDUser(db_session=session)
        notification_service = NotificationService()
        user = await user_crud.get_user_by_id(
            user_id=UUID(user_id)
        )
        if user:
            await notification_service.send_welcome_email(
                user=user
            )
    finally:
        await session.close()


# --- Celery Task for Welcome Email ---
@celery_app.task(
    name="tasks.send_welcome_email",
    bind=True, max_retries=3
)
def send_welcome_email_task(self, user_id: str):
    print(
        f"Executing welcome email task for user_id: {user_id}"
    )
    try:
        asyncio.run(
            _send_welcome_email_async(user_id)
        )
    except Exception as e:
        print(
            "Error in welcome email task for user "
            f"{user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Welcome email task for user {user_id} completed."


# --- Async Helper for Password Reset Email ---
async def _send_password_reset_async(user_id: str, token: str):
    session = AsyncSessionLocal()
    try:
        user_crud = CRUDUser(db_session=session)
        user = await user_crud.get_user_by_id(
            user_id=UUID(user_id)
        )
        if user:
            await send_password_reset_email(
                email_to=user.email,
                username=user.username,
                reset_token=token,
            )
    finally:
        await session.close()


# --- Celery Task for Password Reset ---
@celery_app.task(
    name="tasks.send_password_reset_email",
    bind=True, max_retries=3
)
def send_password_reset_email_task(self, user_id: str, token: str):
    print(
        "Executing password reset email task for user_id: "
        f"{user_id}"
    )
    try:
        asyncio.run(
            _send_password_reset_async(user_id, token)
        )
    except Exception as e:
        print(
            "Error in password reset email task for user "
            f"{user_id}: {e}"
        )
        raise self.retry(exc=e, countdown=60)

    return f"Password reset task for user {user_id} completed."
