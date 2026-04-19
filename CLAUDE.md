# Lumi — Project Context

## What is this?
Lumi is a personal assistant bot that lives in Telegram. You text it like a person — it replies intelligently, remembers things about you, and connects to Gmail, Calendar, and other tools to act on your behalf. Think Poke AI or Tomo AI but built from scratch as a learning project.

The developer (Her Wei) is vibe coding this — move fast, explain things as we go, don't over-engineer.

---

## Current State — Phase 3 (in progress)

**What's working:**
- Telegram webhook receives messages ✅
- Async processing via Celery + Redis ✅
- LLM replies via Gemini 2.5 Flash (REST API, no SDK) ✅
- Groq + Llama 3.3 as fallback, switchable via `LLM_PROVIDER` in `.env` ✅
- Persistent memory via Postgres — conversations survive restarts ✅
- Vector embeddings via `gemini-embedding-001` (768 dims) ✅
- Semantic search — pulls relevant past context before each LLM call ✅
- `./dev.sh` — one command starts everything ✅
- Next.js frontend — landing page + onboarding flow ✅
- Google Sign-In (NextAuth v5 + Google OAuth) ✅
- Telegram account linking (web ↔ Telegram chat_id via link code) ✅
- Google Calendar OAuth + tool use — Lumi can answer calendar questions ✅
- Gmail OAuth + tool use — Lumi can search/read emails ✅ (just added)

**What's not working yet:**
- Notion integration
- Proactive messaging (Lumi can't text first)
- Deployed anywhere (still local + ngrok)

**Known setup requirement:**
- Gmail API + Google Calendar API must be enabled in Google Cloud Console → APIs & Services → Enabled APIs

---

## Tech Stack
- **FastAPI** — webhook server (receives Telegram messages) + auth/OAuth endpoints
- **Celery + Redis** — async task queue (processes messages without blocking)
- **Telegram Bot API** — messaging platform (no SDK, raw httpx calls)
- **LLM** — Gemini 2.5 Flash (default) or Groq + Llama 3.3 (fallback), switchable via `LLM_PROVIDER` in `.env`
- **Gemini function calling** — tool use via REST API for Calendar + Gmail
- **Postgres + pgvector** — persistent message storage + vector similarity search
- **Next.js (App Router)** — frontend landing page + onboarding
- **NextAuth.js v5** — Google Sign-In for the web frontend
- **Python 3.10**
- **Docker** — runs Redis + Postgres locally

## Why these choices?
- Telegram over WhatsApp/SMS: no approval process, free, works Android + iOS, easiest bot API
- Celery: Telegram drops webhooks that take >15s to respond; Celery lets us return 200 immediately and process async
- Postgres + pgvector: one DB for relational + vector search, no separate Pinecone needed
- Gemini via REST (not SDK): the `google-generativeai` SDK breaks in Celery forked workers on Mac due to gRPC. Raw httpx calls work fine.
- Gemini 2.5 Flash: best price/performance. Groq/Llama as free fallback

---

## Monorepo Structure
```
lumi/
├── backend/                    # Python FastAPI server
│   ├── api/
│   │   ├── auth.py             # OAuth endpoints (Telegram link, Google Calendar, Gmail)
│   │   └── webhooks.py         # Telegram webhook endpoint
│   ├── core/
│   │   ├── engine.py           # Main bot logic — memory + LLM + tool use
│   │   ├── embeddings.py       # Gemini embedding API (768-dim vectors)
│   │   └── llm.py              # LLM provider abstraction + chat_with_tools()
│   ├── db/
│   │   ├── connection.py       # psycopg2 connection with pgvector registered
│   │   ├── init_db.py          # Creates tables on startup
│   │   └── repository.py       # DB read/write: users, messages, semantic search
│   ├── integrations/
│   │   ├── google_calendar.py  # Google Calendar API — fetch events, manage tokens
│   │   └── gmail.py            # Gmail API — search/read emails, manage tokens
│   ├── messaging/
│   │   ├── base.py             # Abstract BaseMessenger
│   │   └── telegram.py         # Telegram send/receive/validate
│   ├── celery_app.py
│   ├── tasks.py                # Celery task: handle_message
│   ├── main.py                 # FastAPI entrypoint
│   ├── worker.py               # Celery worker entrypoint
│   ├── config.py               # All settings via pydantic-settings
│   ├── set_telegram_webhook.py
│   ├── requirements.txt
│   └── .env                    # Real secrets — never commit
├── frontend/                   # Next.js app
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── onboarding/page.tsx # Onboarding: link Telegram + Calendar + Gmail
│   │   └── components/
│   │       └── SignInButton.tsx # Google sign-in, Telegram (feature-flagged)
│   └── ...
├── dev.sh                      # One command to start everything
└── docker-compose.yml          # Redis + Postgres with pgvector
```

---

## How to Run (local dev)

```bash
./dev.sh
```

That's it. The script handles everything:
- Starts Docker (Redis + Postgres)
- Starts ngrok, grabs the URL automatically
- Registers the Telegram webhook
- Starts FastAPI (`cd backend && uvicorn main:app`) + Celery with labeled logs

Ctrl+C stops everything cleanly.

**Requires:** Docker running, ngrok installed and authenticated.

---

### Manual startup (separate terminals for logs)

```bash
docker-compose up -d

# Tab 1 — FastAPI
cd ~/Code/lumi/backend && source ../venv/bin/activate && uvicorn main:app --reload --port 8000

# Tab 2 — Celery
cd ~/Code/lumi/backend && source ../venv/bin/activate && celery -A worker worker --loglevel=info

# Tab 3 — ngrok
ngrok http 8000

# Register webhook (once per ngrok restart)
python backend/set_telegram_webhook.py https://YOUR-NGROK-URL.ngrok-free.app

# Tab 4 — Frontend
cd ~/Code/lumi/frontend && npm run dev
```

---

## Key Auth / Integration Details

### Google OAuth credentials
One Google OAuth client is used for both the web sign-in (NextAuth) AND the Calendar/Gmail OAuth.  
`NEXT_PUBLIC_API_URL=http://localhost:8000` points the frontend to the backend.  
Calendar callback: `http://localhost:8000/auth/google-calendar/callback`  
Gmail callback: `http://localhost:8000/auth/gmail/callback`

### Telegram Login Widget
Greyed out on the landing page with a "soon" badge. Fully wired but disabled because Telegram's Login Widget requires a real domain (not localhost).  
**To enable after deploy:**
1. BotFather → `/setdomain` → `@lumi_butlerbot` → enter real domain
2. Set `NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED=true` in production env
3. Implement widget trigger in `SignInButton.tsx` where the TODO comment is

### Gemini Tool Use
`core/llm.py::chat_with_tools()` sends function definitions to Gemini via REST.  
`core/engine.py::_chat_with_integrations()` handles the tool-call round-trip:
1. Call Gemini with available tools
2. If response is a tool_call, execute the function
3. Send tool result back to Gemini for a natural language reply

---

## Known Issues
- ngrok URL changes every restart — `dev.sh` handles this automatically
- Python 3.10 will lose Google SDK support in late 2026 — upgrade to 3.11+ eventually
- Celery deprecation warning about `broker_connection_retry_on_startup` — harmless

---

## Roadmap

### Phase 1 — Bot MVP ✅
### Phase 2 — Persistent Memory ✅
### Phase 3 — Integrations (in progress)
- Google Calendar OAuth + tool use ✅
- Gmail OAuth + tool use ✅
- Web frontend + onboarding ✅

### Phase 4 — Notion Integration
- Add items to Notion inbox via chat

### Phase 5 — Proactive Messaging
- Celery Beat for scheduled messages
- "Remind me every Monday at 9am"

### Phase 6 — Deploy
- Move from ngrok to Railway or Render
- Persistent URL = no more webhook re-registration

---

## Coding Style Notes
- Her Wei is learning — explain what things do as you build them
- Keep it simple and working over clever and broken
- Add comments to non-obvious code
- Don't add features not asked for
- When something breaks, fix the root cause, don't paper over it
