import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from messaging.telegram import TelegramMessenger
from tasks import handle_message

router = APIRouter()
messenger = TelegramMessenger()


@router.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram calls this endpoint for every message sent to the bot.

    Flow:
    1. Validate the request came from Telegram (secret token check)
    2. Parse the update — ignore anything that isn't a text message
    3. Push a job to Celery — return 200 immediately
    4. The Celery worker calls Claude and sends the reply asynchronously
    """
    body_bytes = await request.body()
    headers = dict(request.headers)

    # Validate the secret token header
    if not messenger.validate_request(headers, body_bytes):
        raise HTTPException(status_code=403, detail="Invalid secret token")

    data = await request.json()

    # Only handle messages — ignore edited messages, channel posts, etc.
    if "message" not in data:
        return JSONResponse(content={})

    message = messenger.parse_incoming(data)

    # Ignore empty messages (stickers, photos with no caption, etc.)
    if not message.body:
        return JSONResponse(content={})

    print(f"[webhook] Received from {message.chat_id}: {message.body[:80]}")

    # Handle /start link_CODE — Telegram account linking flow
    if message.body.startswith("/start link_"):
        code = message.body.split("link_", 1)[1].strip()
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.backend_url}/auth/telegram-link/confirm",
                params={"code": code, "chat_id": message.chat_id},
            )
        messenger.send_message(message.chat_id, "✅ Telegram linked! Head back to the Lumi website to continue setup.")
        return JSONResponse(content={})

    # Queue the job — returns immediately
    handle_message.delay(message.chat_id, message.body)

    return JSONResponse(content={})
