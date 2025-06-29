from celery import Celery
from src.core.config import settings


# Initialize Celery
celery_app = Celery(
    "incident_management_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.alert_tasks",
        "src.tasks.user_tasks",
        "src.tasks.incident_tasks",
    ],
)

# Optional configuration.
celery_app.conf.update(
    result_expires=3600,
)

# --- CRUCIAL PART FOR PERIODIC TASKS ---
# This dictionary tells Celery Beat
# what tasks to run and when.
celery_app.conf.beat_schedule = {
    # A descriptive name for the scheduled task
    'fetch-alerts-periodically': {
        # The full path to the task function
        'task': 'tasks.fetch_and_process_alerts',
        # The interval is read from your .env file
        'schedule': settings.ALERT_CHECK_INTERVAL_SECONDS,
    },
}


if __name__ == "__main__":
    celery_app.start()
