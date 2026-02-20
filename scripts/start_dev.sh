#!/bin/bash
# Start both backend and frontend for development.
# Run from project root: ./start_dev.sh

set -e

# Always run from project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "🚀 Starting Study Pal Development Environment..."
echo "   Project root: $(pwd)"
echo ""

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  .env not found. Create it (e.g. copy .env.example) and set OPENAI_API_KEY."
    echo "   Continuing anyway; backend may fail without the key."
else
    # Export variables from .env so they're available to this script
    set -a
    source .env
    set +a
fi

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  No .venv found. Running setup first..."
    ./scripts/setup_env.sh
fi

# Activate venv (same shell)
# shellcheck source=/dev/null
source .venv/bin/activate

# Ensure uvicorn is available (from requirements.txt)
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn not found. Install deps: pip install -r requirements.txt"
    exit 1
fi

# Log dir for backend
mkdir -p logs
BACKEND_LOG="$(pwd)/logs/backend.log"

# Fix jsonschema_specifications JSONDecodeError (chromadb dep) - skip corrupt/empty files
python "$SCRIPT_DIR/fix_jsonschema.py" 2>/dev/null || true

# Remove .DS_Store from schemas dir (macOS)
# Remove .DS_Store from schemas dir (macOS)
for dir in ".venv/lib/python"*/site-packages/jsonschema_specifications/schemas; do
    [ -d "$dir" ] && rm -f "$dir/.DS_Store" 2>/dev/null
done

# Kill any existing Study Pal backend (uvicorn with --reload spawns parent+child)
pkill -9 -f "uvicorn api.main:app" 2>/dev/null || true
sleep 2

# Pick port: try 8000 first, fallback to 8001 if 8000 is stuck
BACKEND_PORT=8000
if lsof -ti :8000 >/dev/null 2>&1; then
    echo "⚠️  Port 8000 in use. Using port 8001 instead..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null || true
    BACKEND_PORT=8001
    sleep 2
fi
# Clear 8001 too if we're using it
[ "$BACKEND_PORT" = 8001 ] && lsof -ti :8001 | xargs kill -9 2>/dev/null || true
[ "$BACKEND_PORT" = 8001 ] && sleep 1

# Start backend in background from project root
echo "📡 Starting FastAPI backend on http://localhost:$BACKEND_PORT ..."
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$SCRIPT_DIR"
# Disable ChromaDB telemetry to avoid import/network delays
export ANONYMIZED_TELEMETRY=False
export CHROMA_TELEMETRY=false
python -m uvicorn api.main:app --reload --reload-dir api --reload-dir core --reload-dir agents --host 0.0.0.0 --port "$BACKEND_PORT" >> "$BACKEND_LOG" 2>&1 &
BACKEND_PID=$!

# Wait for backend to bind and respond (curl with timeout so we don't hang)
echo "   Waiting for backend to be ready..."
for i in $(seq 1 30); do
    sleep 1
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo "❌ Backend exited. Last lines of $BACKEND_LOG:"
        tail -20 "$BACKEND_LOG"
        exit 1
    fi
    if curl -s --connect-timeout 2 --max-time 3 -o /dev/null -w "%{http_code}" "http://localhost:$BACKEND_PORT/" 2>/dev/null | grep -q 200; then
        echo "   Backend ready after ${i}s (PID $BACKEND_PID)"
        break
    fi
    [ $i -eq 60 ] && echo "❌ Backend did not respond after 60s. Check $BACKEND_LOG" && kill "$BACKEND_PID" 2>/dev/null && exit 1
done

# --- Google Calendar MCP sidecar (optional) ---
GCAL_MCP_PORT=3001
if command -v npx &>/dev/null && [ -n "${GOOGLE_CALENDAR_MCP_ENABLED:-}" ]; then
    echo "📅 Starting Google Calendar MCP server on http://localhost:$GCAL_MCP_PORT ..."
    npx -y @cocal/google-calendar-mcp --transport http --port "$GCAL_MCP_PORT" >> "logs/calendar-mcp.log" 2>&1 &
    GCAL_PID=$!
    # Quick readiness check
    for i in $(seq 1 15); do
        sleep 1
        if curl -s --connect-timeout 2 -o /dev/null "http://localhost:$GCAL_MCP_PORT" 2>/dev/null; then
            echo "   Calendar MCP ready after ${i}s (PID $GCAL_PID)"
            break
        fi
        [ $i -eq 15 ] && echo "⚠️  Calendar MCP did not respond after 15s. Check logs/calendar-mcp.log"
    done
    # Override the env var so CalendarConnector finds the local server
    export GOOGLE_CALENDAR_MCP_URL="http://localhost:$GCAL_MCP_PORT/mcp"
else
    echo "📅 Calendar MCP skipped (set GOOGLE_CALENDAR_MCP_ENABLED=1 to start)"
fi

# Frontend env - must match backend port
echo "NEXT_PUBLIC_API_URL=http://localhost:$BACKEND_PORT" > frontend/.env.local

# Kill any leftover frontend process on port 3000 (e.g. from a previous Ctrl+C)
if lsof -ti :3000 >/dev/null 2>&1; then
    echo "⚠️  Port 3000 in use. Killing old frontend process..."
    lsof -ti :3000 | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Truncate old frontend log so we only see current run
: > "logs/frontend.log"

# Start frontend in foreground (Next.js needs a TTY — it hangs when backgrounded)
echo "🎨 Starting Next.js frontend on http://localhost:3000 ..."
echo "   Backend running at http://localhost:$BACKEND_PORT (docs: http://localhost:$BACKEND_PORT/docs)"
echo ""
echo "Press Ctrl+C to stop everything."

trap "kill $BACKEND_PID ${GCAL_PID:-} 2>/dev/null; exit" INT TERM

cd frontend && exec npm run dev
