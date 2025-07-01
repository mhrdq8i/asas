from asyncio import (
    get_running_loop,
    new_event_loop,
    set_event_loop
)
from logging import getLogger
from uuid import UUID

from src.core.celery import celery_app
from src.exceptions.incident_exceptions import (
    IncidentNotFoundException
)
from src.services.incident_service import (
    IncidentService
)
from src.services.notification_service import (
    NotificationService
)


logger = getLogger(__name__)


async def _send_incident_notification_async(
        incident_id: UUID
):
    """
    Asynchronous helper function
    to send the notification.
    This function creates
    its own database engine
    and session to ensure
    complete isolation between
    task executions in
    different processes.
    """

    logger.info(
        "Starting notification task "
        f"for incident {incident_id}"
    )

    # Create a temporary, isolated engine
    # and session for this task
    from sqlalchemy.ext.asyncio import (
        create_async_engine
    )
    from sqlmodel.ext.asyncio.session import (
        AsyncSession
    )
    from sqlalchemy.orm import sessionmaker
    from src.core.config import settings

    async_db_url = settings.DATABASE_URL

    if not async_db_url:
        logger.critical(
            "DATABASE_URL is not "
            "configured in settings."
        )

        return

    # Create a new engine specifically
    temp_engine = create_async_engine(
        url=async_db_url,
        pool_recycle=3600
    )

    TempSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=temp_engine,
        class_=AsyncSession
    )

    async with TempSessionLocal() as db:

        try:
            # Initialize services with the
            # new isolated database session.
            incident_service = IncidentService(
                db_session=db
            )

            notification_service = NotificationService()

            incident = await \
                incident_service.get_incident_by_id(
                    incident_id=incident_id
                )

            if not incident:
                raise IncidentNotFoundException(
                    "Incident with ID "
                    f"{incident_id} not found."
                )

            await notification_service.send_incident_creation_email(
                incident=incident
            )

            logger.info(
                "Successfully sent notification "
                f"for incident {incident_id}."
            )

        except Exception as e:
            logger.error(
                "Error in notification task "
                f"for incident {incident_id}: {e}",
                exc_info=True
            )
            # Re-raise the exception to
            # mark the Celery task as failed
            raise

        finally:
            # Clean up the engine connections
            # after the task is done.
            await temp_engine.dispose()


@celery_app.task(
    name="tasks.create_incident"
)
def send_incident_notification(
    incident_id: str
):
    """
    Celery task to send a notification
    for a new incident.
    Manages the asyncio event loop
    correctly for long-running workers.
    """

    logger.info(
        "Received incident creation task "
        f"for incident_id: {incident_id}"
    )

    try:
        incident_uuid = UUID(incident_id)

        try:
            loop = get_running_loop()

        except RuntimeError:
            loop = new_event_loop()
            set_event_loop(loop=loop)

        loop.run_until_complete(
            _send_incident_notification_async(
                incident_uuid
            )
        )

    except Exception as e:

        # Log the actual exception
        # with its traceback.
        logger.critical(
            "Execution of incident notification "
            f"task for {incident_id}: {e} failed.",
            exc_info=True
        )
