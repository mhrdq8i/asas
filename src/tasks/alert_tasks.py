import logging
import asyncio
from src.core.celery import celery_app
from src.services.alert_service import AlertService
from src.database.session import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def async_task():
    """
    Asynchronous wrapper for the main task logic.
    """
    logger.info("Async task started. Initializing DB session and service.")
    db_session = None
    try:
        db_session = AsyncSessionLocal()
        alert_service = AlertService(db_session)
        logger.info("Fetching alerts from Alertmanager...")
        active_alerts = await alert_service.fetch_alerts_from_prometheus()

        if not active_alerts:
            logger.info("No active alerts found. Task finished.")
            return

        logger.info(
            f"Successfully fetched {len(active_alerts)} active alert(s). Processing...")
        await alert_service.process_alerts(active_alerts)
        logger.info("Alert processing completed successfully.")

    finally:
        if db_session:
            await db_session.close()
            logger.info("Database session closed.")


@celery_app.task(name="tasks.fetch_and_process_alerts")
def fetch_and_process_alerts():
    """
    Synchronous Celery task that runs the asynchronous logic using asyncio.run(),
    which works reliably with the `--pool=solo` worker configuration.
    """
    logger.info("==================================================")
    logger.info("Starting the scheduled alert processing task.")
    try:
        asyncio.run(async_task())
    except Exception as e:
        logger.error(
            f"An unexpected error occurred in the task runner: {e}", exc_info=True)
    logger.info("==================================================\n")
