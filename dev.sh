#!/bin/bash
# Starts everything needed for local Lumi dev.
# Usage: ./dev.sh
# Stop: Ctrl+C (kills all processes)

cd "$(dirname "$0")"

source venv/bin/activate

# 1. Docker (Redis + Postgres)
echo "[dev] Starting Docker services..."
docker-compose up -d

# 2. Start ngrok in background
echo "[dev] Starting ngrok..."
pkill -f "ngrok http" 2>/dev/null || true
ngrok http 8000 --log=stdout > /tmp/ngrok.log 2>&1 &
NGROK_PID=$!

# 3. Wait for ngrok tunnel to be ready, then grab the URL
echo "[dev] Waiting for ngrok tunnel..."
NGROK_URL=""
for i in {1..15}; do
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null \
        | python3 -c "
import sys, json
try:
    tunnels = json.load(sys.stdin).get('tunnels', [])
    https = [t['public_url'] for t in tunnels if t['proto'] == 'https']
    print(https[0] if https else '')
except:
    pass
" 2>/dev/null) || true
    if [ -n "$NGROK_URL" ]; then break; fi
    sleep 1
done

if [ -z "$NGROK_URL" ]; then
    echo "[dev] ERROR: ngrok didn't start. Is ngrok installed?"
    exit 1
fi

echo "[dev] ngrok URL: $NGROK_URL"

# 4. Register webhook with Telegram
python backend/set_telegram_webhook.py "$NGROK_URL"

# 5. Kill all child processes on Ctrl+C
cleanup() {
    echo ""
    echo "[dev] Shutting down..."
    kill $WEB_PID $WORKER_PID $NGROK_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# 6. Start FastAPI + Celery, prefix their logs so you can tell them apart
(cd backend && uvicorn main:app --reload --port 8000) 2>&1 | sed 's/^/[web]    /' &
WEB_PID=$!

(cd backend && celery -A worker worker --loglevel=info) 2>&1 | sed 's/^/[worker] /' &
WORKER_PID=$!

echo "[dev] All systems go. Ctrl+C to stop."
wait
