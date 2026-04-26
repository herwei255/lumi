# Lumi — Project Context

## What is this?
Lumi is a personal assistant bot that lives in Telegram. You text it like a person — it replies intelligently, remembers things about you, and connects to Gmail, Calendar, and other tools to act on your behalf. Think Poke AI or Tomo AI but built from scratch as a learning project.

The developer (Her Wei) is vibe coding this — move fast, explain things as we go, don't over-engineer.

---

## Current State — Phase 6 in progress (local)

**What's working:**
- Telegram webhook receives messages ✅
- Async processing via Celery + Redis ✅
- LLM replies via Gemini 2.5 Flash (REST API, no SDK) ✅
- Groq + Llama 3.3 as fallback, switchable via `LLM_PROVIDER` in `.env` ✅
- Persistent memory via Postgres — conversations survive restarts ✅
- Vector embeddings via `gemini-embedding-001` (768 dims) ✅
- Semantic search — pulls relevant past context before each LLM call ✅
- Next.js frontend — landing page + onboarding flow ✅
- Google Sign-In (NextAuth v5 + Google OAuth) ✅
- Telegram Login Widget — sign in via Telegram (requires real domain, feature-flagged) ✅
- Telegram account linking (web ↔ Telegram chat_id via link code) ✅
- Google Calendar OAuth + tool use — Lumi can answer calendar questions ✅
- Gmail OAuth + tool use — Lumi can search/read emails ✅
- Notion OAuth + tool use — add items to any user's own Notion workspace ✅
- Morning briefing — Celery Beat sends daily summary at 9am SGT (1am UTC) ✅
- Custom reminders — "remind me every day at 9am to drink water" → saves to DB → fires via Celery Beat ✅
- User facts memory — explicit (`remember_fact` tool) + auto-extracted after every exchange ✅

**What's not working yet:**
- Cancel reminders via chat
- Deployed anywhere (still local + ngrok; Railway setup started but paused)

**Known setup requirements:**
- Gmail API + Google Calendar API must be enabled in Google Cloud Console → APIs & Services → Enabled APIs
- Notion: create a **Public** integration, add redirect URI, get OAuth client ID + secret → `NOTION_CLIENT_ID` / `NOTION_CLIENT_SECRET` in `.env`
- User's Notion workspace needs a database (Lumi auto-finds one named "Lumi Inbox", falls back to first database)

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
- **Python 3.11** (pinned via `.python-version`)
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
│   │   ├── gmail.py            # Gmail API — search/read emails, manage tokens
│   │   └── notion.py           # Notion API — add pages to inbox database
│   ├── messaging/
│   │   ├── base.py             # Abstract BaseMessenger
│   │   └── telegram.py         # Telegram send/receive/validate
│   ├── celery_app.py           # Celery config + Beat schedule (briefing + reminders)
│   ├── tasks.py                # Celery tasks: handle_message, send_morning_briefings, check_reminders
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
- Starts FastAPI (`cd backend && uvicorn main:app`) + Celery with `--beat` flag (enables scheduler) + labeled logs

Ctrl+C stops everything cleanly.

**Requires:** Docker running, ngrok installed and authenticated.

---

### Manual startup (separate terminals for logs)

```bash
docker-compose up -d

# Tab 1 — FastAPI
cd ~/Code/lumi/backend && source ../venv/bin/activate && uvicorn main:app --reload --port 8000

# Tab 2 — Celery (--beat enables the scheduler for reminders + morning briefing)
cd ~/Code/lumi/backend && source ../venv/bin/activate && celery -A worker worker --beat --loglevel=info

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
Implemented but feature-flagged. Requires a real domain — Telegram won't work on localhost.  
**To enable after deploy:**
1. BotFather → `/setdomain` → `@lumi_butlerbot` → enter real domain
2. Set `NEXT_PUBLIC_TELEGRAM_AUTH_ENABLED=true` in production env

Telegram-only users get a synthetic `google_id` of `tg_<telegram_id>` so the rest of the system works unchanged.

### User Facts Memory
Two layers — `user_facts` table stores key/value facts per user.
- **Explicit**: user says "remember my name is X" → `remember_fact` tool saves it
- **Auto-extracted**: after every exchange, a silent LLM call scans for facts to keep
- Facts are injected into the system prompt so Lumi actually uses them every reply

### Gemini Tool Use
`core/llm.py::chat_with_tools()` sends function definitions to Gemini via REST.  
`core/engine.py::_chat_with_integrations()` handles the tool-call round-trip:
1. Call Gemini with available tools
2. If response is a tool_call, execute the function
3. Send tool result back to Gemini for a natural language reply

---

## Known Issues
- ngrok URL changes every restart — `dev.sh` handles this automatically
- Celery deprecation warning about `broker_connection_retry_on_startup` — harmless
- Gemini tool use: response parts must ALL be scanned for `functionCall` (not just `parts[0]`) — already fixed in `llm.py`
- `toolConfig: {functionCallingConfig: {mode: "AUTO"}}` required in Gemini API call or tools won't fire — already set

---

## Roadmap

### Phase 1 — Bot MVP ✅
### Phase 2 — Persistent Memory ✅
### Phase 3 — Integrations ✅
- Google Calendar OAuth + tool use ✅
- Gmail OAuth + tool use ✅
- Web frontend + onboarding ✅

### Phase 4 — Notion Integration ✅
- Add items to Notion inbox via chat ✅
- OAuth flow — each user connects their own Notion workspace ✅
- Auto-finds "Lumi Inbox" database, falls back to first database ✅

### Phase 5 — Proactive Messaging ✅
- Morning briefing via Celery Beat at 9am SGT ✅
- Custom reminders: "remind me every day at 9am to drink water" ✅
- Reminders stored in DB, fired by `check_reminders` task every minute ✅

### Phase 6 (bonus features, done locally) ✅
- User facts memory — explicit + auto-extracted ✅
- Telegram Login Widget (feature-flagged, needs real domain) ✅
- Notion OAuth (multi-user, each connects own workspace) ✅

### Phase 7 — Polish + Deploy
- Cancel reminders via chat
- Deploy (Railway paused — lumi-web, lumi-worker, lumi-frontend services exist)
- To resume Railway: set DATABASE_URL, REDIS_URL, BACKEND_URL, FRONTEND_URL per service

---

## Coding Style Notes
- Her Wei is learning — explain what things do as you build them
- Keep it simple and working over clever and broken
- Add comments to non-obvious code
- Don't add features not asked for
- When something breaks, fix the root cause, don't paper over it

---

## AI Coding Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
