from asyncio import run as async_run
from logging import getLogger
from src.core.celery import celery_app
from src.database.session import AsyncSessionLocal
from src.services.alert_service import AlertService


logger = getLogger(__name__)


async def _check_alerts_async():
    """
    Async helper function to contain
    the actual logic for checking alerts.
    """

    session = AsyncSessionLocal()

    try:
        alert_service = AlertService(db_session=session)
        await alert_service.process_prometheus_alerts()

    finally:
        await session.close()


@celery_app.task(name="tasks.check_prometheus_alerts")
def check_prometheus_alerts_task():
    """
    Celery task that periodically checks for new alerts from Prometheus.
    It's a synchronous wrapper around the async logic.
    """

    logger.info(
        "Executing Celery task: check_prometheus_alerts_task"
    )

    try:
        async_run(_check_alerts_async())

    except Exception as e:
        # This task should not retry aggressively as it's a periodic check.
        # Logging the error is sufficient.

        logger.error(
            "An error occurred during the execution of "
            f"check_prometheus_alerts_task: {e}",
            exc_info=True
        )

    return_msg = "Prometheus alert check task finished."

    return return_msg
