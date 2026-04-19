import httpx

from config import settings
from messaging.base import BaseMessenger, IncomingMessage

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


class TelegramMessenger(BaseMessenger):
    """
    Telegram Bot API messenger.

    Incoming: Telegram POSTs JSON updates to our webhook URL.
    Outgoing: We call the sendMessage API endpoint.

    No third-party library needed — the Telegram Bot API is simple REST.
    """

    def validate_request(self, headers: dict, body: bytes) -> bool:
        """
        Telegram passes the secret_token we set during webhook registration
        in the X-Telegram-Bot-Api-Secret-Token header.
        In DEBUG mode this check is skipped.
        """
        if settings.debug:
            return True
        if not settings.telegram_secret_token:
            return True  # No secret configured — skip check
        incoming = headers.get("x-telegram-bot-api-secret-token", "")
        return incoming == settings.telegram_secret_token

    def parse_incoming(self, data: dict) -> IncomingMessage:
        """
        Extract chat_id and message text from a Telegram Update object.

        Telegram Update shape:
        {
          "update_id": 123,
          "message": {
            "chat": { "id": 456 },
            "text": "Hello!"
          }
        }
        """
        message = data.get("message", {})
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()
        return IncomingMessage(
            chat_id=chat_id,
            body=text,
            platform="telegram",
            raw=data,
        )

    def send_message(self, chat_id: str, body: str) -> None:
        """
        Send a message via the Telegram Bot API.
        Splits messages longer than 4096 characters (Telegram's limit).
        """
        chunks = _split_message(body, limit=4096)
        with httpx.Client() as client:
            for chunk in chunks:
                client.post(
                    f"{TELEGRAM_API}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk},
                    timeout=10,
                )

    def empty_response(self) -> dict:
        """Telegram expects a 200 OK with an empty JSON body."""
        return {}


def _split_message(text: str, limit: int = 4096) -> list[str]:
    """Split a long message into chunks within the platform character limit."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks
