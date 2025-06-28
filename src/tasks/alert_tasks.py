import logging
from src.core.celery import celery_app
from src.services.alert_service import AlertService
from src.database.session import AsyncSession


logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.fetch_and_process_alerts")
def fetch_and_process_alerts():
    """
    A periodic Celery task that fetches
    alerts from Prometheus Alertmanager
    and processes them to create
    incidents if necessary.
    """
    print("==================================================")
    logger.info("Starting the scheduled alert processing task.")

    db_session = None
    try:
        # Initialize a new database session for this task.
        db_session = AsyncSession()
        alert_service = AlertService(db_session)
        logger.info(
            "Successfully initialized database session and alert service.")

        # Fetch active alerts from the configured Alertmanager endpoint.
        logger.info("Fetching alerts from Alertmanager...")
        active_alerts = alert_service.fetch_alerts_from_prometheus()

        if not active_alerts:
            logger.info("No active alerts found. Task finished.")
            print("==================================================")
            return "Task completed: No alerts to process."

        logger.info(
            f"Successfully fetched {len(active_alerts)} active alert(s).")

        # Hand over the alerts to the service layer for processing.
        # This includes filtering and incident creation logic.
        logger.info(
            "Handing over alerts to the alert_service for processing...")
        alert_service.process_alerts(active_alerts)

        logger.info("Alert processing completed successfully.")

    except Exception as e:
        logger.error(
            f"An unexpected error occurred during the task: {e}",
            exc_info=True
        )

    finally:
        # Always close the database session to release the connection.
        if db_session:
            db_session.close()
            logger.info("Database session closed.")
        print("==================================================\n")

    return "Alert fetching and processing task finished."
