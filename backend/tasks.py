from celery_app import celery_app
from core.engine import process_message


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def handle_message(self, chat_id: str, body: str):
    """
    Process an incoming message and send a reply.

    bind=True gives us access to `self` so we can retry on failure.
    max_retries=3 means up to 3 attempts total before giving up.
    Backoff: 5s → 10s → 20s between retries.
    """
    try:
        process_message(chat_id, body)
    except Exception as exc:
        print(f"[task] handle_message failed (attempt {self.request.retries + 1}): {exc}")
        raise self.retry(exc=exc, countdown=5 * (2 ** self.request.retries))
