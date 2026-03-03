#!/bin/bash
# =============================================
# AI Lead Engine — Start the dashboard
# =============================================

cd "$(dirname "$0")"

# Activate venv if it exists
if [ -d "venv" ]; then
  source venv/bin/activate
fi

if [ ! -f ".env" ]; then
  echo "⚠️  No .env file found. Copy .env.example to .env and add your API keys."
  exit 1
fi

echo ""
echo "⚡ Starting AI Lead Engine..."
echo "   Dashboard: http://localhost:8000"
echo "   Press Ctrl+C to stop"
echo ""

python main.py
