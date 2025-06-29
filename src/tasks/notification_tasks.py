import asyncio
import logging
from uuid import UUID

from src.core.celery import celery_app
from src.exceptions.incident_exceptions import IncidentNotFoundException

logger = logging.getLogger(__name__)


async def _send_notification_async(incident_id_str: str):
    """
    Asynchronous helper function to send the notification.
    """
    # Imports moved inside to prevent Celery startup import cycles.
    from src.database.session import AsyncSessionLocal
    from src.services.incident_service import IncidentService
    from src.services.notification_service import NotificationService

    logger.info(f"Starting notification task for incident {incident_id_str}")

    db = None
    try:
        db = AsyncSessionLocal()
        incident_id = UUID(incident_id_str)
        incident_service = IncidentService(db)
        notification_service = NotificationService()

        incident = await incident_service.get_incident_by_id(
            incident_id=incident_id
        )
        if not incident:
            raise IncidentNotFoundException(
                f"Incident with ID {incident_id_str} not found.")

        await notification_service.send_incident_creation_email(
            incident=incident
        )

        logger.info(
            f"Successfully sent notification for incident {incident_id_str}."
        )
    except IncidentNotFoundException as e:
        logger.error(
            f"Error in notification task for incident {incident_id_str}: {e}"
        )
    except Exception as e:
        logger.error(
            f"Error in notification task for incident {incident_id_str}: {e}",
            exc_info=True
        )
    finally:
        if db:
            # --- FIX: Must await the close() method for an AsyncSession ---
            await db.close()


@celery_app.task(name="src.tasks.notification_tasks")
def send_incident_notification(incident_id: str):
    """
    Celery task to send a notification for a new incident.
    Manages the asyncio event loop correctly.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(_send_notification_async(incident_id))
