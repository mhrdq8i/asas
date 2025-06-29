import asyncio
import logging
from uuid import UUID

from celery import shared_task

from src.database.session import AsyncSessionLocal
from src.services.incident_service import IncidentService
from src.services.notification_service import NotificationService
from src.exceptions.incident_exceptions import IncidentNotFoundException


logger = logging.getLogger(__name__)


@shared_task
def send_incident_notification(incident_id: str):
    """
    Celery task to send a notification for a new incident.
    """
    # It's better to run async code in a managed event loop within a Celery task
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(_send_notification_async(incident_id))


async def _send_notification_async(incident_id_str: str):
    """
    Asynchronous helper function to send the notification.
    This is where the actual logic resides.
    """
    logger.info(f"Starting notification task for incident {incident_id_str}")
    db = AsyncSessionLocal()
    try:
        incident_id = UUID(incident_id_str)
        incident_service = IncidentService(db)
        notification_service = NotificationService()

        incident = await incident_service.get_incident_by_id(incident_id)
        if not incident:
            raise IncidentNotFoundException(
                f"Incident with ID {incident_id_str} not found.")

        # --- FIX: Removed the unexpected keyword argument 'recipients' ---
        # The 'send_incident_creation_email' method gets recipients from settings internally.
        await notification_service.send_incident_creation_email(
            incident=incident
        )

        logger.info(
            f"Successfully sent notification for incident {incident_id_str}."
        )

    except IncidentNotFoundException as e:
        logger.error(
            f"Error in notification task for incident {incident_id_str}: {e}")
    except Exception as e:
        # Catching generic exceptions to log them properly
        logger.error(
            f"Error in notification task for incident {incident_id_str}: {e}", exc_info=True)
    finally:
        db.close()
