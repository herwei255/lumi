# Lumi

A personal assistant that lives in your Telegram. Text it like a person — it remembers you, connects to your calendar, email, and Notion, and can proactively remind you of things.

Built as a learning project by Her Wei.

---

## What it does

- **Replies intelligently** via Gemini 2.5 Flash (or Groq/Llama as fallback)
- **Remembers you** — stores conversation history + extracts facts (your name, preferences, etc.) automatically
- **Google Calendar** — "what do I have tomorrow?" → pulls your real events
- **Gmail** — "any emails from my boss?" → searches your inbox
- **Notion** — "add this to my inbox" → creates a page in your Notion workspace
- **Reminders** — "remind me every day at 9am to drink water" → fires via Telegram
- **Morning briefing** — daily summary of your calendar + unread emails at 9am SGT

---

## Tech stack

| Layer | Tech |
|---|---|
| Bot platform | Telegram Bot API (raw httpx, no SDK) |
| Backend | FastAPI + Python 3.11 |
| Task queue | Celery + Redis |
| Scheduler | Celery Beat (reminders + morning briefing) |
| LLM | Gemini 2.5 Flash via REST (default) or Groq/Llama 3.3 |
| Tool use | Gemini function calling (Calendar, Gmail, Notion, Reminders, Memory) |
| Database | Postgres + pgvector |
| Vector search | pgvector cosine similarity (768-dim Gemini embeddings) |
| Frontend | Next.js 16 (App Router) |
| Auth | NextAuth v5 — Google OAuth + Telegram Login Widget |
| Local tunnel | ngrok |

**Why Gemini via REST (not SDK)?** The `google-generativeai` SDK uses gRPC which breaks in Celery forked workers on Mac. Raw httpx calls work fine.

---

## Architecture

```
User texts Lumi on Telegram
        ↓
FastAPI webhook receives message → returns 200 immediately
        ↓
Celery task queue (async, so Telegram doesn't time out)
        ↓
engine.py:
  1. Load user's stored facts (name, prefs, etc.) → inject into system prompt
  2. Load recent messages + semantic search for relevant past context
  3. Call Gemini with available tools (Calendar, Gmail, Notion, Reminders, Memory)
  4. If Gemini calls a tool → execute it → send result back → get final reply
  5. Save messages to Postgres with vector embeddings
  6. Auto-extract new facts from the exchange (silent background LLM call)
  7. Send reply via Telegram
```

---

## Memory system

Lumi has two layers of memory:

**1. Conversation history** — every message stored in Postgres with a 768-dim embedding. Before each reply, Lumi pulls the last 10 messages + up to 5 semantically similar older messages.

**2. User facts** — structured key/value facts (`name: Her Wei`, `lives in: Singapore`). Two ways facts get saved:
- **Explicit**: user says "remember my name is X" → Lumi calls `remember_fact` tool
- **Auto-extracted**: after every exchange, a silent LLM call scans for facts worth keeping

Facts are injected at the top of the system prompt so Lumi actually uses them.

---

## Project structure

```
lumi/
├── backend/
│   ├── api/
│   │   ├── auth.py             # OAuth flows: Telegram link, Google Calendar, Gmail, Notion
│   │   └── webhooks.py         # Telegram webhook endpoint
│   ├── core/
│   │   ├── engine.py           # Main bot logic: memory + LLM + tool use + fact extraction
│   │   ├── embeddings.py       # Gemini embedding API (768-dim vectors)
│   │   └── llm.py              # LLM abstraction: chat() + chat_with_tools()
│   ├── db/
│   │   ├── connection.py       # psycopg2 + pgvector connection
│   │   ├── init_db.py          # Creates all tables on startup (idempotent)
│   │   └── repository.py       # DB read/write: messages, facts, semantic search
│   ├── integrations/
│   │   ├── google_calendar.py  # Google Calendar API — fetch events, token refresh
│   │   ├── gmail.py            # Gmail API — search/read emails, token refresh
│   │   └── notion.py           # Notion API — add pages to user's workspace
│   ├── messaging/
│   │   └── telegram.py         # Telegram send/receive/validate
│   ├── celery_app.py           # Celery config + Beat schedule
│   ├── tasks.py                # Tasks: handle_message, send_morning_briefings, check_reminders
│   ├── main.py                 # FastAPI entrypoint
│   ├── config.py               # All settings via pydantic-settings + .env
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── onboarding/page.tsx # Connect Telegram + Calendar + Gmail + Notion
│   │   └── components/
│   │       └── SignInButton.tsx # Google sign-in + Telegram Login Widget
│   └── auth.ts                 # NextAuth config (Google + Telegram credentials)
├── dev.sh                      # One command starts everything
├── docker-compose.yml          # Redis + Postgres with pgvector
└── CLAUDE.md                   # Full project context for AI assistants
```

---

## Local development

### Prerequisites

- Docker Desktop running
- ngrok installed and authenticated (`ngrok config add-authtoken YOUR_TOKEN`)
- Python 3.11, Node 20

### First time setup

```bash
# Clone and set up Python env
git clone https://github.com/herwei255/lumi.git
cd lumi
python3.11 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Set up frontend
cd frontend && npm install && cd ..

# Copy env template and fill in your secrets
cp backend/.env.example backend/.env

# Copy frontend env
cp frontend/.env.example frontend/.env.local
```

### Run

```bash
./dev.sh
```

That's it. The script:
1. Starts Docker (Redis + Postgres)
2. Starts ngrok, grabs the URL
3. Registers the Telegram webhook
4. Starts FastAPI + Celery with `--beat` (enables scheduler)

Frontend (Next.js) runs separately:
```bash
cd frontend && npm run dev
```

### Environment variables

**`backend/.env`**
```env
# LLM
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key          # optional fallback

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_SECRET_TOKEN=any_random_string  # for webhook validation

# Infrastructure
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://lumi:lumi@localhost:5432/lumi

# Google OAuth (one client for Calendar + Gmail)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Notion OAuth
NOTION_CLIENT_ID=your_notion_client_id
NOTION_CLIENT_SECRET=your_notion_client_secret

# URLs (override in production)
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

DEBUG=true
```

**`frontend/.env.local`**
```env
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
NEXTAUTH_SECRET=any_random_string
NEXTAUTH_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Enable Telegram Login Widget (requires real domain + BotFather /setdomain)
NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED=false
```

---

## Integrations setup

### Google Calendar + Gmail
1. Go to [Google Cloud Console](https://console.cloud.google.com) → create a project
2. Enable **Google Calendar API** and **Gmail API**
3. Create OAuth 2.0 credentials (Web application)
4. Add redirect URIs:
   - `http://localhost:8000/auth/google-calendar/callback`
   - `http://localhost:8000/auth/gmail/callback`
5. Add test users under OAuth consent screen while in testing mode

### Notion
1. Go to [notion.so/profile/integrations](https://notion.so/profile/integrations) → New integration
2. Set type to **Public**
3. Add redirect URI: `http://localhost:8000/auth/notion/callback`
4. Copy OAuth client ID and secret → add to `backend/.env`
5. Users connect their own workspace via the onboarding flow — Lumi auto-finds a database named **"Lumi Inbox"** (falls back to first database found)

### Telegram bot
1. Message `@BotFather` → `/newbot` → follow prompts
2. Copy the token → `TELEGRAM_BOT_TOKEN` in `.env`
3. `dev.sh` auto-registers the webhook on every start

### Telegram Login Widget (for web sign-in)
Requires a real domain (not localhost).
1. `@BotFather` → `/setdomain` → your domain
2. Set `NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED=true` in frontend env

---

## Gotchas

- **Gemini tool use**: response parts must ALL be scanned for `functionCall` (not just `parts[0]`). `toolConfig: {functionCallingConfig: {mode: "AUTO"}}` is required.
- **Ghost Celery workers**: if tools aren't being called, check for old workers with `ps aux | grep celery` and kill them.
- **ngrok URL changes on restart** — `dev.sh` re-registers the webhook automatically.
- **Celery + Mac gRPC**: don't use `google-generativeai` SDK in Celery workers — use raw httpx instead.

---

## Roadmap

- [x] Telegram bot MVP
- [x] Persistent memory (Postgres + pgvector)
- [x] Google Calendar integration
- [x] Gmail integration
- [x] Web frontend + onboarding
- [x] Notion integration (OAuth, multi-user)
- [x] Morning briefing (Celery Beat)
- [x] Custom reminders
- [x] User facts memory (explicit + auto-extracted)
- [x] Telegram Login Widget
- [ ] Cancel reminders via chat
- [ ] Deploy (Railway / Render)
