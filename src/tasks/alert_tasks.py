from asyncio import (
    get_running_loop,
    new_event_loop,
    set_event_loop
)
from logging import getLogger

from src.core.celery import celery_app


logger = getLogger(__name__)


async def _fetch_and_process_alerts_async():
    """
    Asynchronous helper for
    fetching and processing alerts.
    """
    # Imports are moved inside to prevent
    # Celery startup import cycles.
    from src.database.session import AsyncSessionLocal
    from src.services.alert_service import AlertService

    logger.info("Starting alert processing task.")
    db = None

    try:
        db = AsyncSessionLocal()
        alert_service = AlertService(db_session=db)

        # Fetch active alerts from Alertmanager
        active_alerts = await \
            alert_service.fetch_alerts_from_prometheus()

        # Process alerts
        if active_alerts:
            await alert_service.process_alerts(
                alerts=active_alerts
            )
            logger.info(
                "Successfully processed "
                f"{len(active_alerts)} alerts."
            )

        else:
            logger.info(
                "No active alerts to process."
            )

    except Exception as e:
        logger.error(
            "An error occurred during "
            f"alert processing: {e}",
            exc_info=True
        )

    finally:
        if db:
            # Ensure the async session
            # is closed properly
            await db.close()


@celery_app.task(
    name="tasks.fetch_and_process_alerts"
)
def fetch_and_process_alerts():
    """
    Celery task to fetch alerts
    from Alertmanager and process them.
    Manages the asyncio event loop
    correctly to avoid "different loop" errors.
    """

    try:
        # Get the current running event loop,
        # which is what Celery/SQLAlchemy use.
        loop = get_running_loop()

    # If no loop is running (
    # e.g., in some test environments),
    # create one.
    except RuntimeError:
        loop = new_event_loop()
        set_event_loop(loop=loop)

    # Run the async helper function
    # within the correct event loop.
    loop.run_until_complete(
        _fetch_and_process_alerts_async()
    )
