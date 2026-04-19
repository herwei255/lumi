"""
Celery worker entry point.

Run with:
    celery -A worker worker --loglevel=info
"""

from celery_app import celery_app
import tasks  # noqa: F401 — importing registers the tasks with Celery

if __name__ == "__main__":
    celery_app.start()
