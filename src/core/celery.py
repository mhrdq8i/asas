from celery import Celery
from src.core.config import settings

# Initialize Celery
celery_app = Celery(
    "incident_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Add the new tasks module to the include list
    include=[
        "src.tasks.alert_tasks",
        "src.tasks.notification_tasks",
        "src.tasks.user_tasks"
    ]
)

# Configure Celery to use UTC timezone
celery_app.conf.timezone = 'UTC'

# Add the periodic task schedule (Celery Beat)
celery_app.conf.beat_schedule = {
    'fetch-alerts-periodically': {
        'task': 'tasks.fetch_and_process_alerts',
        'schedule': float(
            settings.ALERT_CHECK_INTERVAL_SECONDS
        )
    }
}

celery_app.conf.update(
    result_expires=3600,
)

if __name__ == '__main__':
    celery_app.start()
