#!/bin/bash
# Lumi setup script — run once to install everything

set -e  # stop on any error

echo ""
echo "Setting up Lumi..."
echo ""

# Step 1: Create virtual environment
echo "→ Creating virtual environment..."
python3 -m venv venv
echo "  ✓ Done"

# Step 2: Activate it
echo "→ Activating virtual environment..."
source venv/bin/activate
echo "  ✓ Done"

# Step 3: Upgrade pip quietly
echo "→ Upgrading pip..."
pip install --upgrade pip --quiet
echo "  ✓ Done"

# Step 4: Install dependencies
echo "→ Installing dependencies (this takes ~30 seconds)..."
pip install -r requirements.txt
echo "  ✓ Done"

# Step 5: Create .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "  ✓ Created .env from .env.example"
    echo "  ⚠  Open .env and fill in your API keys before running the bot."
else
    echo "  ✓ .env already exists"
fi

echo ""
echo "Setup complete! Next steps:"
echo ""
echo "  1. Fill in your .env file with your API keys"
echo "  2. Run: docker-compose up -d          (starts Redis)"
echo "  3. Run: source venv/bin/activate && uvicorn main:app --reload --port 8000"
echo "  4. In another terminal: source venv/bin/activate && celery -A worker worker --loglevel=info"
echo "  5. In another terminal: ngrok http 8000"
echo "  6. Run: python set_telegram_webhook.py https://YOUR-NGROK-URL.ngrok-free.app"
echo ""
