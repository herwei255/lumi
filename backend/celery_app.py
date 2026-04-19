from celery import Celery
from config import settings

# Create the Celery app — this module is imported by both the
# webhook server (to queue tasks) and the worker (to execute them).
celery_app = Celery(
    "lumi",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["tasks"],  # tells Celery where to find our task definitions
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)
