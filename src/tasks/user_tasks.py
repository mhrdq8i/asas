from uuid import UUID
from logging import getLogger
from datetime import timedelta
from asyncio import run as async_run

from src.core.celery import (
    celery_app
)
from src.database.session import (
    AsyncSessionLocal
)
from src.crud.user_crud import (
    CrudUser
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


# NOTE: The welcome email logic was
# missing from notification_service,
# so the welcome task is commented
# out in user_service.
# It can be added back later.


logger = getLogger(__name__)


async def _send_verification_email_async(
        user_id: str
):

    session = AsyncSessionLocal()

    try:
        user_crud = CrudUser(
            db_session=session
        )

        user = await user_crud.get_user_by_id(
            user_id=UUID(user_id)
        )

        if not user or user.is_email_verified:
            status = "already verified" if user \
                and user.is_email_verified else "not found"

            logger.warning(
                f"User {user_id} {status}. "
                "Aborting verification email task."
            )

            return

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

        update_data = {
            "email_verification_token": get_password_hash(
                email_verification_token
            )
        }

        await user_crud.update_user(
            db_user_to_update=user,
            user_in_update_data=update_data
        )

        await session.commit()

        await send_email_verification(
            email_to=user.email,
            username=user.username,
            verification_token=email_verification_token
        )

        logger.info(
            "Successfully sent verification "
            f"email to user {user.id}"
        )

    finally:
        await session.close()


@celery_app.task(
    name="tasks.send_verification_email",
    bind=True,
    max_retries=3
)
def send_verification_email_task(
    self,
    user_id: str
):

    logger.info(
        "Executing verification "
        "email task for user_id: "
        f"{user_id} (Try "
        f"{self.request.retries})"
    )

    try:
        async_run(
            _send_verification_email_async(
                user_id
            )
        )

    except Exception as e:

        logger.error(
            "Error in verification "
            "email task for user "
            f"{user_id}: {e}",
            exc_info=True
        )

        raise self.retry(
            exc=e,
            countdown=60
        )

    return (
        "Verification email task for "
        f"user {user_id} completed."
    )


async def _send_password_reset_async(
        user_id: str,
        token: str
):

    session = AsyncSessionLocal()

    try:
        user_crud = CrudUser(
            db_session=session
        )

        user = await user_crud.get_user_by_id(
            user_id=UUID(user_id)
        )

        if user:
            await send_password_reset_email(
                email_to=user.email,
                username=user.username,
                reset_token=token
            )

            logger.info(
                "Successfully sent password reset "
                f"email to user {user.id}"
            )

    finally:
        await session.close()


@celery_app.task(
    name="tasks.send_password_reset_email",
    bind=True,
    max_retries=3
)
def send_password_reset_email_task(
    self,
    user_id: str,
    token: str
):

    logger.info(
        "Executing password "
        "reset task for user_id: "
        f"{user_id} (Try "
        f"{self.request.retries})"
    )

    try:
        async_run(
            _send_password_reset_async(
                user_id,
                token
            )
        )

    except Exception as e:

        logger.error(
            "Error in password "
            "reset task for user "
            f"{user_id}: {e}",
            exc_info=True
        )

        raise self.retry(
            exc=e,
            countdown=60
        )

    return (
        "Password reset task for "
        f"user {user_id} completed."
    )
