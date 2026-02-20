# Deploying the Study Pal UI for the Demo

Three ways to run the UI: **Docker** (one command), **locally** (fastest for dev), or **deployed** (shareable URL).

---

## Option 0: Run with Docker (API only)

One-command API for quick testing:

```bash
# Create .env with OPENAI_API_KEY first
cp .env.example .env
# Edit .env and add your key

docker-compose up --build
```

API runs at http://localhost:8000. Run the frontend separately (`cd frontend && npm run dev`) and set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local`.

---

## Option 1: Run Locally (recommended for demo)

Use this when you’re demoing on your own machine.

### One command

From the project root:

```bash
./start_dev.sh
```

This starts:

- **Backend** at http://localhost:8000 (needs `OPENAI_API_KEY` in `.env`)
- **Frontend** at http://localhost:3000

Then:

1. Open **http://localhost:3000**
2. Register (e.g. user ID `demo_user`)
3. Follow [DEMO.md](DEMO.md) Option B (upload PDF, tutor, quiz, analyze, schedule, motivator)

### Two terminals (alternative)

**Terminal 1 – API:**

```bash
cd /path/to/study_pal
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – Frontend:**

```bash
cd /path/to/study_pal/frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm install && npm run dev
```

Then open http://localhost:3000 and run the demo.

### If something fails

- **Backend:** `.env` in project root with `OPENAI_API_KEY`; port 8000 free; `pip install -r requirements.txt` (and `api/requirements.txt` if you use it).
- **Frontend:** `frontend/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`; port 3000 free; `npm install` in `frontend/`.

---

## Option 2: Deploy so the UI has a public URL

Use this when you want a link to share (e.g. for a remote demo). The frontend and API are deployed separately.

### Backend (API)

The API must run on a host that can execute Python and has access to `OPENAI_API_KEY`. Options:

| Platform   | Notes |
|-----------|--------|
| **Railway** | Add repo, set root to project, build: `pip install -r requirements.txt`, start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`. Set `OPENAI_API_KEY` and `FRONTEND_URL` (see below). |
| **Render**  | New Web Service, connect repo, build: `pip install -r requirements.txt`, start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`. Set env vars. Use a persistent disk if you want ChromaDB/data to persist. |
| **Fly.io**  | `fly launch` in project root, Dockerfile or `fly.toml` that runs uvicorn with `api.main:app`. Set secrets for `OPENAI_API_KEY` and `FRONTEND_URL`. |

After deploy you’ll have an API URL, e.g. `https://your-app.railway.app`.

### Frontend (Next.js)

1. **Vercel (simplest for Next.js)**  
   - Import the repo, set root to `frontend`.  
   - Add env var: `NEXT_PUBLIC_API_URL=https://your-api-url` (your deployed API URL).  
   - Deploy. You’ll get a URL like `https://study-pal.vercel.app`.

2. **Other hosts**  
   - Build: `cd frontend && npm ci && npm run build`.  
   - Run: `npm run start` (or serve the `.next` output as per host docs).  
   - Set `NEXT_PUBLIC_API_URL` to your API URL at build time.

### CORS (API)

The API allows `localhost:3000` by default. For a deployed frontend, either:

- Set **one** of these env vars on the API server:
  - `FRONTEND_URL=https://your-frontend.vercel.app`  
  - or `ALLOWED_ORIGINS=https://your-frontend.vercel.app,https://another-origin.com`
- Restart the API after setting the env var.

### Summary for a “deployed demo”

1. Deploy the API (Railway/Render/Fly), get `API_URL`.
2. Set on API: `OPENAI_API_KEY`, `FRONTEND_URL=<frontend URL>` (or `ALLOWED_ORIGINS`).
3. Deploy the frontend (e.g. Vercel), set `NEXT_PUBLIC_API_URL=<API_URL>`.
4. Open the frontend URL and run the demo as in [DEMO.md](DEMO.md).

---

## Quick reference

| Goal              | Command / step |
|-------------------|----------------|
| Demo on your machine | `./start_dev.sh` → open http://localhost:3000 |
| API with Docker   | `docker-compose up --build` → API at http://localhost:8000 |
| API only (e.g. for Postman) | `./api/run.sh` or `PYTHONPATH=. python -m uvicorn api.main:app --host 0.0.0.0 --port 8000` |
| Deployed UI       | Deploy API → set `FRONTEND_URL`; deploy frontend with `NEXT_PUBLIC_API_URL` → use frontend URL for demo |

For the step-by-step demo flow once the UI is running, see [DEMO.md](DEMO.md).
