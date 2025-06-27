from logging import getLogger
from asyncio import run as async_run

import httpx

from src.core.celery import celery_app
from src.core.config import settings
from src.database.session import AsyncSessionLocal
from src.services.alert_service import AlertService


logger = getLogger(__name__)


@celery_app.task(name="tasks.fetch_and_process_alerts")
def fetch_and_process_alerts():
    """
    A Celery task to fetch alerts from
    Prometheus AlertManager and process them.
    This is a synchronous wrapper for the async implementation.
    """

    logger.info("Starting task: fetch_and_process_alerts.")

    try:
        # Run the asynchronous function to perform the actual work
        async_run(_fetch_and_process_alerts_async())
        logger.info("Finished task: fetch_and_process_alerts.")

    except Exception as e:
        logger.error(
            "An error occurred during the execution of "
            f"fetch_and_process_alerts task: {e}",
            exc_info=True
        )


async def _fetch_and_process_alerts_async():
    """
    Asynchronously fetches alerts,
    processes them,
    and handles database sessions.
    """

    alerts_url = settings.PROMETHEUS_API_URL

    if not alerts_url:
        logger.warning(
            "PROMETHEUS_API_URL is not set. Skipping alert fetching."
        )
        return

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            # The AlertManager API endpoint for
            # alerts is typically /api/v2/alerts
            # The user's .env example has /api/v1/alerts,
            # which is for Prometheus itself.
            # Let's assume the user knows their endpoint.

            response = await client.get(alerts_url)

            # Raise an exception for bad
            # status codes (4xx or 5xx)
            response.raise_for_status()

            alerts_data = response.json()

            # The structure of AlertManager response
            #  can be a list directly, or nested.
            # Assuming the response is a list of alerts.
            # Adjust if your structure differs.
            alerts = alerts_data if isinstance(
                alerts_data, list
            ) else alerts_data.get('data', {}).get('alerts', [])

            if alerts:
                logger.info(
                    f"Fetched {len(alerts)} alerts from AlertManager."
                )

                db_session = AsyncSessionLocal()

                try:
                    alert_service = AlertService(db_session)
                    await alert_service.process_alerts(alerts)

                finally:
                    await db_session.close()

            else:
                logger.info("No active alerts fetched from AlertManager.")

    except httpx.RequestError as e:
        logger.error(
            f"Could not fetch alerts from AlertManager at {alerts_url}: {e}"
        )

    except Exception as e:
        logger.error(
            f"An unexpected error occurred while processing alerts: {e}",
            exc_info=True
        )
