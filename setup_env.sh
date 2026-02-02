#!/bin/bash
set -e

echo "🛠️  Setting up Study Pal environment..."
echo ""

# Parse arguments
CLEAN_INSTALL=false
INSTALL_DEPS=false
for arg in "$@"; do
    if [ "$arg" == "--clean" ]; then
        CLEAN_INSTALL=true
    elif [ "$arg" == "--install-deps" ]; then
        INSTALL_DEPS=true
    fi
done

if [ "$CLEAN_INSTALL" = true ]; then
    echo "🧹 Cleaning previous installations..."
    rm -rf .venv
    rm -rf frontend/node_modules
fi

# 1. Check for .env
if [ ! -f .env ]; then
    echo "⚠️  .env file not found."
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example. PLEASE UPDATE IT WITH YOUR API KEY!"
    else
        echo "❌ .env.example not found. Creating empty .env..."
        echo "OPENAI_API_KEY=" > .env
    fi
else
    echo "✅ .env file found."
fi

# 2. Setup Python Virtual Environment
VENV_JUST_CREATED=false
if [ ! -d ".venv" ]; then
    echo "🐍 Creating Python virtual environment..."
    python3 -m venv .venv
    VENV_JUST_CREATED=true
else
    echo "✅ Virtual environment exists."
fi

source .venv/bin/activate

# 3. Install Python Dependencies (only when venv is new or --install-deps)
if [ "$VENV_JUST_CREATED" = true ] || [ "$INSTALL_DEPS" = true ]; then
    echo "📦 Installing Python dependencies (this can take a few minutes)..."
    pip install -r requirements.txt
    pip install -r api/requirements.txt
else
    echo "✅ Skipping Python deps (already installed). Use ./setup_env.sh --install-deps to reinstall."
fi

# 4. Install Frontend Dependencies (only when missing or --install-deps)
if [ ! -d "frontend/node_modules" ] || [ "$INSTALL_DEPS" = true ]; then
    echo "📦 Installing Frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ Skipping Frontend deps (node_modules exists). Use ./setup_env.sh --install-deps to reinstall."
fi

echo ""
echo "🎉 Setup complete!"
echo "👉 1. Add your OPENAI_API_KEY to .env"
echo "👉 2. Run ./start_dev.sh to start the app"
