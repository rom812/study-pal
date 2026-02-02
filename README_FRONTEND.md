# Study Pal Frontend

Modern Next.js frontend for Study Pal AI Study Assistant.

## Setup

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Install Backend API Dependencies

```bash
cd api
pip install -r requirements.txt
```

### 3. Run the Backend API

```bash
# From project root
./api/run.sh

# Or manually:
cd api
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 4. Run the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Features

- **Registration Flow**: Multi-step form to create user profile
- **Login**: Simple user ID-based authentication
- **Chat Interface**: Modern chat UI with dynamic agent emoji switching
  - 📚 Tutor Agent
  - 📅 Scheduler Agent
  - 🔍 Analyzer Agent
  - 💪 Motivator Agent
- **File Upload**: Upload PDF files for study materials
- **Dark Theme**: Minimalistic dark design

## Environment Variables

Make sure you have a `.env` file in the project root with:
```
OPENAI_API_KEY=your_key_here
```

## Usage

1. Start the backend API (port 8000)
2. Start the frontend (port 3000)
3. Open `http://localhost:3000`
4. Register a new account or login with existing user ID
5. Start chatting with the AI agents!



