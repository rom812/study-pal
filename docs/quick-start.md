# 🚀 Quick Start Guide

## Prerequisites

- Node.js 18+ installed
- Python 3.10+ installed
- OpenAI API key in `.env` file

## Setup Steps

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Install Backend API Dependencies

```bash
pip install -r api/requirements.txt
```

### 3. Environment Setup

Make sure you have a `.env` file in the project root:

```bash
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Start Development Servers

**Option A: Use the start script (recommended)**

```bash
./start_dev.sh
```

**Option B: Start manually**

Terminal 1 - Backend:
```bash
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Terminal 2 - Frontend:
```bash
cd frontend
npm run dev
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

To deploy the UI for a remote demo (e.g. Vercel + Railway), see **[DEPLOY.md](DEPLOY.md)**.

## First Time Usage

1. Open http://localhost:3000
2. Click "Create Account"
3. Fill out the registration form:
   - Step 1: Enter User ID and Name
   - Step 2: Select motivational persona(s)
   - Step 3: Add academic field and study topics (optional)
   - Step 4: Add goals and select challenges (optional)
4. Start chatting with the AI agents!

## Features

- ✅ **Registration Flow**: Beautiful multi-step form
- ✅ **Login**: Simple user ID authentication
- ✅ **Chat Interface**: Modern UI with dynamic agent emojis
  - 📚 Tutor Agent - Answers study questions
  - 📅 Scheduler Agent - Creates study schedules
  - 🔍 Analyzer Agent - Analyzes study sessions
  - 💪 Motivator Agent - Provides motivation
- ✅ **File Upload**: Upload PDFs for study materials
- ✅ **Dark Theme**: Minimalistic dark design

## Troubleshooting

### Backend won't start
- Check that Python dependencies are installed
- Verify `.env` file exists with `OPENAI_API_KEY`
- Make sure port 8000 is not in use

### Frontend won't start / Connection Refused on localhost:3000
- Run `npm install` in the `frontend` directory
- Check that Node.js 18+ is installed
- Make sure port 3000 is not in use
- **If `./start_dev.sh` says "Both servers running" but browser shows Connection Refused:**
  1. Run the frontend manually in a separate terminal: `cd frontend && npm run dev`
  2. Wait 30–60 seconds for the first compile (Next.js can be slow on first run)
  3. Clear the build cache: `rm -rf frontend/.next` then retry
  4. Try `npm cache clean --force` if installs seem corrupted

### API connection errors
- Verify backend is running on port 8000
- Check `frontend/.env.local` has `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Check browser console for CORS errors

## Project Structure

```
study_pal/
├── frontend/          # Next.js frontend
│   ├── app/          # Pages and routes
│   ├── lib/           # Utilities and API client
│   └── package.json
├── api/               # FastAPI backend
│   ├── main.py        # API endpoints
│   └── requirements.txt
└── ...                # Existing Python code (agents, core, etc.)
```

Enjoy your Study Pal! 🎓



