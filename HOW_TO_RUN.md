# How to Run Lumi — Phase 1

## What you need
- Python 3.12+
- Docker Desktop (for Redis)
- ngrok account — ngrok.com (free)
- Anthropic API key — console.anthropic.com
- Telegram account

---

## Step 1 — Create your Telegram bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Follow the prompts — give it a name ("Lumi") and a username (e.g. `lumi_mybot`)
4. BotFather gives you a token like `123456789:AAFxxx...` — save this

---

## Step 2 — Install dependencies

```bash
cd /Users/hw/Code/lumi
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 3 — Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:
- `ANTHROPIC_API_KEY` — from console.anthropic.com → API Keys
- `TELEGRAM_BOT_TOKEN` — the token from BotFather
- `TELEGRAM_SECRET_TOKEN` — make up any random string, e.g. `lumi-secret-2024`
- Leave `DEBUG=true` for now

---

## Step 4 — Start Redis

```bash
docker-compose up -d
```

Check it's running: `docker ps` — should show a redis container.

---

## Step 5 — Start the FastAPI server

Terminal 1:
```bash
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

---

## Step 6 — Start the Celery worker

Terminal 2:
```bash
source venv/bin/activate
celery -A worker worker --loglevel=info
```

---

## Step 7 — Expose with ngrok

Terminal 3:
```bash
ngrok http 8000
```

Copy the `Forwarding` URL, e.g. `https://abc123.ngrok-free.app`

---

## Step 8 — Register the webhook with Telegram

```bash
source venv/bin/activate
python set_telegram_webhook.py https://abc123.ngrok-free.app
```

You should see: `✓ Webhook set to: https://abc123.ngrok-free.app/webhook/telegram`

---

## Step 9 — Test it

Open Telegram, find your bot by its username, and send it a message.
You should get a reply within a few seconds.

Watch Terminal 1 (FastAPI) and Terminal 2 (Celery) for logs.

---

## Every time you restart ngrok

Your ngrok URL changes each restart (on the free plan). Re-run the webhook script:
```bash
python set_telegram_webhook.py https://NEW-URL.ngrok-free.app
```

---

## Troubleshooting

**No reply:**
- Check Celery terminal for errors
- Make sure ngrok is still running
- Re-run `set_telegram_webhook.py` with your current ngrok URL

**`pydantic_settings` / settings error on startup:**
- Make sure your `.env` file exists and all required fields are filled in

**Redis connection error:**
- Run `docker-compose up -d` to restart Redis
