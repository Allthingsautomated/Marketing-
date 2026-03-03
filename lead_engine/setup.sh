#!/bin/bash
# =============================================
# AI Lead Engine — One-Time Setup Script
# Run this once after cloning the repo
# =============================================

echo ""
echo "⚡ Setting up AI Lead Engine..."
echo ""

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "❌ Python 3 not found. Install from https://python.org"
  exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f .env ]; then
  cp .env.example .env
  echo "📝 Created .env file — open it and add your API keys"
else
  echo "✅ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Open .env and add your API keys"
echo "  2. Run: ./start.sh"
echo "  3. Open: http://localhost:8000"
echo ""
