#!/bin/bash
set -e

echo "=== AI Lead Engine Server Setup ==="

# Make sure we're in the right directory
cd ~/Marketing-/lead_engine 2>/dev/null || { cd ~/Marketing- && git pull && cd lead_engine; }

# Pull latest code
git -C ~/Marketing- pull origin main 2>/dev/null || true

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo ">>> .env file created. Please fill in your API keys:"
  echo "    nano ~/Marketing-/lead_engine/.env"
  echo ""
  echo "Then run:  docker compose up -d"
else
  echo ">>> .env already exists, skipping..."
  echo ">>> Launching with Docker..."
  docker compose up -d --build
  echo ""
  echo "=== DONE! Dashboard is live at: http://$(curl -s ifconfig.me):8000 ==="
fi
