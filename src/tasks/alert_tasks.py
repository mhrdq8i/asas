from src.core.celery import celery_app
import logging

logger = logging.getLogger(__name__)

# This is a placeholder for the future task that will check Prometheus.
# We are defining it here to prevent ModuleNotFoundError when starting Celery.


@celery_app.task(name="tasks.check_prometheus_alerts")
async def check_prometheus_alerts():
    """
    Placeholder task to periodically check for alerts from Prometheus.
    The actual implementation will be added in the future.
    """
    logger.info(
        "Executing placeholder task: "
        "check_prometheus_alerts. "
        "No action taken."
    )
    return "Prometheus alert check task is a placeholder."
