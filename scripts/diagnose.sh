#!/bin/bash
# Run from project root: ./scripts/diagnose.sh
cd "$(dirname "$0")/.." || exit 1

echo "🔍 Starting Diagnosis..."
echo "--------------------------------"

# Check Node and NPM
echo "Checking Environment:"
echo "Node Path: $(which node)"
echo "Node Version: $(node -v)"
echo "NPM Version: $(npm -v)"
echo "--------------------------------"

# Check Directories
echo "Checking Project Structure:"
if [ -d "frontend/node_modules" ]; then
    echo "✅ frontend/node_modules exists"
else
    echo "❌ frontend/node_modules MISSING"
fi

if [ -f "frontend/.env.local" ]; then
    echo "✅ frontend/.env.local exists"
else
    echo "❌ frontend/.env.local MISSING"
fi
echo "--------------------------------"

# Try to run frontend
echo "🚀 Attempting to start frontend (capturing log)..."
cd frontend
npm run dev > ../frontend_error.log 2>&1 &
PID=$!

echo "Waiting 10 seconds to see if it crashes..."
sleep 10

# Check if still running
if ps -p $PID > /dev/null; then
   echo "✅ Frontend seems to be running properly (PID: $PID)"
   echo "Killing it now for safety."
   kill $PID
else
   echo "❌ Frontend crashed or stopped immediately."
fi

echo "--------------------------------"
echo "📄 Last 20 lines of log:"
tail -n 20 ../frontend_error.log
