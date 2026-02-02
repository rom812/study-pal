#!/bin/bash
# Start both backend and frontend for development.
# Run from project root: ./start_dev.sh

set -e

# Always run from project root (directory containing this script)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Study Pal Development Environment..."
echo "   Project root: $SCRIPT_DIR"
echo ""

# Check .env
if [ ! -f .env ]; then
    echo "⚠️  .env not found. Create it (e.g. copy .env.example) and set OPENAI_API_KEY."
    echo "   Continuing anyway; backend may fail without the key."
fi

# Ensure virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  No .venv found. Running setup first..."
    ./setup_env.sh
fi

# Activate venv (same shell)
# shellcheck source=/dev/null
source .venv/bin/activate

# Ensure uvicorn is available (from api/requirements.txt)
if ! python -c "import uvicorn" 2>/dev/null; then
    echo "❌ uvicorn not found. Install API deps: pip install -r api/requirements.txt"
    exit 1
fi

# Log dir for backend
mkdir -p logs
BACKEND_LOG="$SCRIPT_DIR/logs/backend.log"

# Fix macOS .DS_Store breaking jsonschema_specifications (chromadb dependency)
for dir in "$SCRIPT_DIR/.venv/lib/python"*/site-packages/jsonschema_specifications/schemas; do
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
    [ $i -eq 30 ] && echo "❌ Backend did not respond after 30s. Check $BACKEND_LOG" && kill "$BACKEND_PID" 2>/dev/null && exit 1
done

# Frontend env - must match backend port
echo "NEXT_PUBLIC_API_URL=http://localhost:$BACKEND_PORT" > frontend/.env.local

# Start frontend (must run from frontend/)
echo "🎨 Starting Next.js frontend on http://localhost:3000 ..."
(
    cd frontend
    npm run dev
) >> "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
FRONTEND_PID=$!

# Wait for port 3000 to be listening (Next.js can take 15-45s on first compile)
echo "   Waiting for frontend to bind to port 3000 (may take 30-60s on first run)..."
for i in $(seq 1 30); do
    if lsof -i :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "   Frontend ready after ${i}s"
        break
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo "❌ Frontend exited. Last lines of logs/frontend.log:"
        tail -30 "$SCRIPT_DIR/logs/frontend.log"
        kill "$BACKEND_PID" 2>/dev/null || true
        exit 1
    fi
    sleep 2
done

if ! lsof -i :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "❌ Frontend did not bind to port 3000 after 60s."
    echo "   Check logs/frontend.log. Try running manually: cd frontend && npm run dev"
    echo "   Last lines of log:"
    tail -20 "$SCRIPT_DIR/logs/frontend.log"
    kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
    exit 1
fi
echo "   Frontend PID $FRONTEND_PID (log: logs/frontend.log)"

echo ""
echo "✅ Both servers are running."
echo "   Backend:  http://localhost:$BACKEND_PORT  (docs: http://localhost:$BACKEND_PORT/docs)"
echo "   Frontend: http://localhost:3000"
echo ""
echo "   If Create Account shows 'Backend not reachable', verify: curl http://localhost:$BACKEND_PORT/"
echo ""
echo "Press Ctrl+C to stop both."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
