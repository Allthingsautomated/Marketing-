#!/bin/bash
# AllThings CRM - Quick Start Script

echo "🚀 Starting AllThings CRM..."

# Install backend deps
echo "📦 Installing backend dependencies..."
cd "$(dirname "$0")/backend"
npm install

# Install frontend deps
echo "📦 Installing frontend dependencies..."
cd ../frontend
npm install

# Start both servers
echo ""
echo "✅ Starting servers..."
echo "   Backend:  http://localhost:5000"
echo "   Frontend: http://localhost:5173"
echo ""

cd ..
# Start backend in background
cd backend && node server.js &
BACKEND_PID=$!

# Start frontend
cd ../frontend && npm run dev

# Cleanup on exit
kill $BACKEND_PID 2>/dev/null
