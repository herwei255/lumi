"""
Google Calendar integration.

Fetches events using stored OAuth tokens.
Handles token refresh automatically when the access token expires.
"""

from datetime import datetime, timezone, timedelta

import httpx

from db.connection import get_connection


def get_tokens(google_id: str) -> dict | None:
    """Return stored Google OAuth tokens for a user, or None if not connected."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT access_token, refresh_token, expires_at FROM oauth_tokens WHERE google_id = %s AND provider = 'google_calendar'",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if not row:
        return None
    return {"access_token": row[0], "refresh_token": row[1], "expires_at": row[2]}


def refresh_access_token(google_id: str, refresh_token: str, client_id: str, client_secret: str) -> str:
    """Exchange a refresh token for a new access token and update the DB."""
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    access_token = data["access_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE oauth_tokens SET access_token = %s, expires_at = %s WHERE google_id = %s AND provider = 'google_calendar'",
        (access_token, expires_at, google_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return access_token


def get_calendar_events(google_id: str, days_ahead: int = 7) -> list[dict]:
    """
    Fetch upcoming calendar events for a user.
    Returns a list of event dicts with title, start, end, location.
    """
    from config import settings

    tokens = get_tokens(google_id)
    if not tokens:
        return []

    access_token = tokens["access_token"]

    # Refresh if expired
    if tokens["expires_at"] and tokens["expires_at"] < datetime.now(timezone.utc):
        access_token = refresh_access_token(
            google_id, tokens["refresh_token"],
            settings.google_client_id, settings.google_client_secret,
        )

    time_min = datetime.now(timezone.utc).isoformat()
    time_max = (datetime.now(timezone.utc) + timedelta(days=days_ahead)).isoformat()

    resp = httpx.get(
        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
        headers={"Authorization": f"Bearer {access_token}"},
        params={
            "timeMin": time_min,
            "timeMax": time_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 20,
        },
        timeout=10.0,
    )
    resp.raise_for_status()

    events = []
    for item in resp.json().get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})
        events.append({
            "title": item.get("summary", "Untitled"),
            "start": start.get("dateTime") or start.get("date", ""),
            "end": end.get("dateTime") or end.get("date", ""),
            "location": item.get("location", ""),
            "description": item.get("description", ""),
        })
    return events


def get_google_id_for_chat(chat_id: str) -> str | None:
    """Look up the google_id linked to a Telegram chat_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT google_id FROM web_users WHERE telegram_chat_id = %s",
        (chat_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None
