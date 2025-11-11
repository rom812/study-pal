#!/bin/bash
# Quick start script for Study Pal Gradio UI

echo "========================================================================"
echo "  🎓 STUDY PAL - GRADIO UI LAUNCHER"
echo "========================================================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  WARNING: .env file not found!"
    echo "   Please create a .env file with your OPENAI_API_KEY"
    echo ""
    echo "   Example:"
    echo "   OPENAI_API_KEY=your_api_key_here"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if gradio is installed
if ! python -c "import gradio" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo ""
fi

echo "🚀 Starting Gradio UI..."
echo "   The app will open in your browser at http://localhost:7860"
echo ""
echo "   Press Ctrl+C to stop the server"
echo ""
echo "========================================================================"
echo ""

python gradio_app.py
