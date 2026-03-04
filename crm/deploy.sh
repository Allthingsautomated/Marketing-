#!/bin/bash
# AllThings CRM — Re-deploy script
# Run this after pulling latest changes

set -e

echo "🔄 Pulling latest changes..."
git pull origin main

echo "📦 Installing backend deps..."
cd "$(dirname "$0")/backend"
npm install --production

echo "📦 Installing & building frontend..."
cd ../frontend
npm install
npm run build

echo "♻️  Restarting backend..."
pm2 restart crm-backend || pm2 start ../ecosystem.config.js

echo ""
echo "✅ CRM redeployed!"
pm2 status
