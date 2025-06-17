import asyncio
from uuid import UUID
from src.core.celery import celery_app
from src.database.session import AsyncSessionLocal
from src.crud.incident_crud import CrudIncident
from src.services.notification_service import NotificationService


async def _send_notification_async(incident_id: str):
    """
    The actual async logic for sending the notification.
    This helper function contains all the await calls.
    """
    session = AsyncSessionLocal()
    try:
        incident_crud = CrudIncident(db_session=session)
        notification_service = NotificationService()

        # Fetch the full incident object using the CRUD layer
        incident = await incident_crud.get_incident_by_id(
            incident_id=UUID(incident_id)
        )

        if not incident:
            print(f"Incident with ID {incident_id} not found. Aborting.")
            return

        # Send the notification
        await notification_service.send_incident_creation_email(
            incident=incident
        )
    finally:
        # Ensure the session is always closed.
        await session.close()


@celery_app.task(
    name="tasks.send_incident_notification",
    bind=True, max_retries=3
)
def send_incident_notification_task(self, incident_id: str):
    """
    Synchronous Celery task that wraps the async logic.
    This pattern is compatible with all Celery workers,
    including the default one,
    and prevents event loop conflicts.
    """
    print(
        "Executing synchronous wrapper for notification "
        f"task: {incident_id}"
    )
    try:
        # Run the async helper function in a new event loop for each task
        asyncio.run(
            _send_notification_async(incident_id)
        )
    except Exception as e:
        print(
            f"Error in notification task for incident {incident_id}: {e}"
        )
        countdown_seconds = 60 * (self.request.retries + 1)
        raise self.retry(
            exc=e, countdown=countdown_seconds
        )

    return f"Notification task for incident {incident_id} completed."
