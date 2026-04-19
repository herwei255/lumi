"""
One-time script to register your ngrok URL as the Telegram webhook.

Run this every time your ngrok URL changes (i.e. every time you restart ngrok):

    python set_telegram_webhook.py https://abc123.ngrok-free.app
"""

import sys
import httpx
from config import settings


def set_webhook(ngrok_url: str):
    webhook_url = f"{ngrok_url}/webhook/telegram"
    api_url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook"

    payload = {"url": webhook_url}
    if settings.telegram_secret_token:
        payload["secret_token"] = settings.telegram_secret_token

    response = httpx.post(api_url, json=payload)
    result = response.json()

    if result.get("ok"):
        print(f"✓ Webhook set to: {webhook_url}")
    else:
        print(f"✗ Failed: {result}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python set_telegram_webhook.py https://your-ngrok-url.ngrok-free.app")
        sys.exit(1)
    set_webhook(sys.argv[1])
