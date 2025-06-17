from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "incident_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "src.tasks.alert_tasks",
        "src.tasks.notification_tasks",
        "src.tasks.user_tasks"
    ]
)
