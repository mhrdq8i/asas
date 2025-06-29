from uuid import UUID
from logging import getLogger
from asyncio import run as async_run

from src.core.config import settings
from src.core.celery import celery_app
from src.database.session import AsyncSessionLocal
from src.crud.incident_crud import CrudIncident
from src.services.notification_service import (
    NotificationService
)


logger = getLogger(__name__)


async def _send_notification_async(
        incident_id_str: str
):
    """
    Asynchronous helper function to
    perform the actual notification logic.
    """

    logger.info(
        "Starting async notification for "
        f"incident: {incident_id_str}"
    )

    db_session = None

    try:
        incident_id = UUID(incident_id_str)

        db_session = AsyncSessionLocal()

        incident_crud = CrudIncident(db_session)

        incident = await incident_crud.get_incident_by_id(
            incident_id=incident_id
        )

        if not incident:
            logger.error(
                f"Incident with ID {incident_id_str} "
                "not found for notification."
            )

            return

        recipients = settings.get_notification_recipients()

        if not recipients:
            logger.warning(
                "No notification recipients "
                "configured. Skipping email."
            )

            return

        notification_service = NotificationService()

        await notification_service.send_incident_notification_email(
            recipients=recipients,
            incident=incident
        )

        logger.info(
            "Successfully sent notification for "
            "incident {incident_id_str}."
        )

    except Exception as e:
        logger.error(
            "Error in notification task for incident "
            f"{incident_id_str}: {e}",
            exc_info=True
        )

    finally:
        if db_session:
            await db_session.close()


@celery_app.task(
    name="tasks.send_incident_notification"
)
def send_incident_notification_task(
        incident_id_str: str
):
    """
    Synchronous Celery task entry point
    for sending incident notifications.
    Uses asyncio.run() for robust
    execution of async code.
    """

    logger.info(
        "Received notification task for "
        f"incident ID: {incident_id_str}"
    )

    try:
        # Use asyncio.run() for consistency
        # and robustness with --pool=solo
        async_run(
            _send_notification_async(
                incident_id_str
            )
        )

    except Exception as e:
        logger.error(
            "Critical error in notification "
            "task runner for incident "
            f"{incident_id_str}: {e}",
            exc_info=True
        )
