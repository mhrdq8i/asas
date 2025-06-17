import asyncio
from src.core.celery_app import celery_app
from src.database.session import AsyncSessionLocal
from src.services.incident_service import IncidentService
from src.services.notification_service import NotificationService
from uuid import UUID


@celery_app.task(name="tasks.send_incident_notification")
def send_incident_notification_task(incident_id: str):
    async def _run_async():
        session = AsyncSessionLocal()
        incident_service = IncidentService(db_session=session)
        notification_service = NotificationService()

        try:
            incident = await incident_service.get_incident_by_id(
                incident_id=UUID(incident_id)
            )
            await notification_service.send_incident_creation_email(
                incident=incident
            )
        except Exception as e:
            print(f"Error in notification task: {e}")
            raise
        finally:
            await session.close()

    asyncio.run(_run_async())

    return f"Notification for incident {incident_id} completed."
