#!/bin/bash
# Auto-deploy: pulls latest code and restarts the app
# Set this up as a cron job or run once to deploy updates
set -e

cd /root/Marketing-/lead_engine

echo "[deploy] Pulling latest code..."
git pull origin claude/marketing-agency-website-2ORbA

echo "[deploy] Rebuilding and restarting..."
docker compose up -d --build

echo "[deploy] Done. App running at http://$(curl -s ifconfig.me):8000"
