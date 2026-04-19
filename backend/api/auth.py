"""
Auth endpoints:
- Telegram account linking (web ↔ Telegram chat_id)
- Google Calendar OAuth (connect calendar to a web account)
"""

import secrets
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel

from config import settings
from db.connection import get_connection

router = APIRouter()

GOOGLE_CALENDAR_SCOPES = "https://www.googleapis.com/auth/calendar.readonly"
GOOGLE_GMAIL_SCOPES = "https://www.googleapis.com/auth/gmail.readonly"


def _calendar_callback_url() -> str:
    return f"{settings.backend_url}/auth/google-calendar/callback"


def _gmail_callback_url() -> str:
    return f"{settings.backend_url}/auth/gmail/callback"


# ── Telegram linking ──────────────────────────────────────────────────────────

class LinkRequest(BaseModel):
    google_id: str


@router.post("/telegram-link")
async def create_telegram_link(body: LinkRequest):
    """Generate a one-time link code for connecting Telegram to a web account."""
    code = secrets.token_urlsafe(16)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS web_users (
            id               SERIAL PRIMARY KEY,
            google_id        TEXT UNIQUE NOT NULL,
            email            TEXT,
            telegram_chat_id TEXT,
            created_at       TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute("""
        INSERT INTO web_users (google_id) VALUES (%s)
        ON CONFLICT (google_id) DO NOTHING
    """, (body.google_id,))
    cur.execute("""
        CREATE TABLE IF NOT EXISTS telegram_link_tokens (
            code       TEXT PRIMARY KEY,
            google_id  TEXT NOT NULL,
            used       BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW()
        )
    """)
    cur.execute(
        "INSERT INTO telegram_link_tokens (code, google_id) VALUES (%s, %s)",
        (code, body.google_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return JSONResponse({"code": code})


@router.get("/telegram-status")
async def telegram_status(google_id: str):
    """Check if a web user already has a linked Telegram account."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT telegram_chat_id FROM web_users WHERE google_id = %s",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    linked = bool(row and row[0])
    return JSONResponse({"linked": linked})


@router.get("/telegram-link/{code}")
async def check_telegram_link(code: str):
    """Frontend polls this to check if Telegram linking completed."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT used FROM telegram_link_tokens WHERE code = %s", (code,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return JSONResponse({"linked": False})
    return JSONResponse({"linked": row[0]})


@router.post("/telegram-link/confirm")
async def confirm_telegram_link(code: str, chat_id: str):
    """Called by the Telegram bot when it receives /start link_CODE."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT google_id FROM telegram_link_tokens WHERE code = %s AND used = FALSE",
        (code,),
    )
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return JSONResponse({"ok": False, "error": "invalid or already used code"})

    google_id = row[0]
    cur.execute(
        "UPDATE web_users SET telegram_chat_id = %s WHERE google_id = %s",
        (chat_id, google_id),
    )
    cur.execute("UPDATE telegram_link_tokens SET used = TRUE WHERE code = %s", (code,))
    conn.commit()
    cur.close()
    conn.close()
    return JSONResponse({"ok": True})


# ── Google Calendar OAuth ─────────────────────────────────────────────────────

@router.get("/google-calendar")
async def google_calendar_connect(google_id: str):
    """
    Start the Google Calendar OAuth flow.
    Redirects the user to Google's consent screen.
    We pass google_id as state so we know who to save tokens for on callback.
    """
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _calendar_callback_url(),
        "response_type": "code",
        "scope": GOOGLE_CALENDAR_SCOPES,
        "access_type": "offline",   # gets us a refresh_token
        "prompt": "consent",         # always show consent so we always get refresh_token
        "state": google_id,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/google-calendar/callback")
async def google_calendar_callback(code: str, state: str):
    """
    Google redirects here after the user approves Calendar access.
    Exchange the code for tokens and save them to Postgres.
    """
    google_id = state

    # Exchange auth code for tokens
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": _calendar_callback_url(),
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token", "")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

    # Save tokens to DB
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id            SERIAL PRIMARY KEY,
            google_id     TEXT NOT NULL,
            provider      TEXT NOT NULL,
            access_token  TEXT,
            refresh_token TEXT,
            expires_at    TIMESTAMPTZ,
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(google_id, provider)
        )
    """)
    cur.execute("""
        INSERT INTO oauth_tokens (google_id, provider, access_token, refresh_token, expires_at)
        VALUES (%s, 'google_calendar', %s, %s, %s)
        ON CONFLICT (google_id, provider)
        DO UPDATE SET access_token = EXCLUDED.access_token,
                      refresh_token = EXCLUDED.refresh_token,
                      expires_at = EXCLUDED.expires_at
    """, (google_id, access_token, refresh_token, expires_at))
    conn.commit()
    cur.close()
    conn.close()

    # Redirect back to onboarding with success flag
    return RedirectResponse(f"{settings.frontend_url}/onboarding?calendar=connected")


@router.get("/google-calendar/status")
async def google_calendar_status(google_id: str):
    """Check if a user has connected Google Calendar."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM oauth_tokens WHERE google_id = %s AND provider = 'google_calendar'",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return JSONResponse({"connected": row is not None})


# ── Gmail OAuth ───────────────────────────────────────────────────────────────

@router.get("/gmail")
async def gmail_connect(google_id: str):
    """Start the Gmail OAuth flow."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": _gmail_callback_url(),
        "response_type": "code",
        "scope": GOOGLE_GMAIL_SCOPES,
        "access_type": "offline",
        "prompt": "consent",
        "state": google_id,
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/gmail/callback")
async def gmail_callback(code: str, state: str):
    """Exchange auth code for Gmail tokens and store them."""
    google_id = state

    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": _gmail_callback_url(),
            "grant_type": "authorization_code",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    access_token = data["access_token"]
    refresh_token = data.get("refresh_token", "")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS oauth_tokens (
            id            SERIAL PRIMARY KEY,
            google_id     TEXT NOT NULL,
            provider      TEXT NOT NULL,
            access_token  TEXT,
            refresh_token TEXT,
            expires_at    TIMESTAMPTZ,
            created_at    TIMESTAMPTZ DEFAULT NOW(),
            UNIQUE(google_id, provider)
        )
    """)
    cur.execute("""
        INSERT INTO oauth_tokens (google_id, provider, access_token, refresh_token, expires_at)
        VALUES (%s, 'gmail', %s, %s, %s)
        ON CONFLICT (google_id, provider)
        DO UPDATE SET access_token = EXCLUDED.access_token,
                      refresh_token = EXCLUDED.refresh_token,
                      expires_at = EXCLUDED.expires_at
    """, (google_id, access_token, refresh_token, expires_at))
    conn.commit()
    cur.close()
    conn.close()

    return RedirectResponse(f"{settings.frontend_url}/onboarding?gmail=connected")


@router.get("/gmail/status")
async def gmail_status(google_id: str):
    """Check if a user has connected Gmail."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM oauth_tokens WHERE google_id = %s AND provider = 'gmail'",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return JSONResponse({"connected": row is not None})
