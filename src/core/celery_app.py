from celery import Celery
from src.core.config import settings

# Add the new task module to the include list
celery_app = Celery(
    "incident_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.notification_tasks"
    ]
)
