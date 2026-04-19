"""
Gmail integration — read/search emails for a connected user.
"""

import base64
from datetime import datetime, timezone, timedelta

import httpx

from config import settings
from db.connection import get_connection


def _get_gmail_token(google_id: str) -> str | None:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT access_token, refresh_token, expires_at FROM oauth_tokens WHERE google_id = %s AND provider = 'gmail'",
        (google_id,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    access_token, refresh_token, expires_at = row
    if expires_at and datetime.now(timezone.utc) >= expires_at:
        access_token = _refresh_token(google_id, refresh_token)

    return access_token


def _refresh_token(google_id: str, refresh_token: str) -> str:
    resp = httpx.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    resp.raise_for_status()
    data = resp.json()

    access_token = data["access_token"]
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=data.get("expires_in", 3600))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE oauth_tokens SET access_token = %s, expires_at = %s WHERE google_id = %s AND provider = 'gmail'",
        (access_token, expires_at, google_id),
    )
    conn.commit()
    cur.close()
    conn.close()
    return access_token


def search_emails(google_id: str, query: str = "in:inbox", max_results: int = 5) -> list[dict]:
    """
    Search the user's Gmail and return a list of email summaries.
    query: Gmail search query (same syntax as the Gmail search box)
    """
    token = _get_gmail_token(google_id)
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: get message IDs matching the query
    list_resp = httpx.get(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
        headers=headers,
        params={"q": query, "maxResults": max_results},
    )
    if list_resp.status_code != 200:
        print(f"[gmail] list error: {list_resp.status_code} {list_resp.text[:200]}")
        return []

    messages = list_resp.json().get("messages", [])
    if not messages:
        return []

    # Step 2: fetch each message's metadata
    results = []
    for msg in messages:
        detail_resp = httpx.get(
            f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
            headers=headers,
            params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
        )
        if detail_resp.status_code != 200:
            continue

        detail = detail_resp.json()
        headers_list = detail.get("payload", {}).get("headers", [])
        header_map = {h["name"]: h["value"] for h in headers_list}

        snippet = detail.get("snippet", "")

        results.append({
            "id": msg["id"],
            "subject": header_map.get("Subject", "(no subject)"),
            "from": header_map.get("From", ""),
            "date": header_map.get("Date", ""),
            "snippet": snippet,
        })

    return results
