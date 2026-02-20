# StudyPal Project Restructure — Professional Polish

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the StudyPal repository so it looks clean, professional, and recruiter-ready — no functional changes, only organizational and tooling improvements.

**Architecture:** Keep the existing `agents/`, `core/`, `api/`, `frontend/` layout (it works fine). Focus on: removing clutter from root, adding modern Python tooling (`pyproject.toml`, ruff), fixing the broken CI badge, splitting the monolithic API file, extracting frontend components, and consolidating scattered docs.

**Tech Stack:** Python (ruff, pytest, pyproject.toml), GitHub Actions CI, Next.js/TypeScript (eslint), Makefile, Docker

---

## Target Structure (After All Tasks)

```
study_pal/
├── .github/
│   └── workflows/
│       └── ci.yml                # Lint + test on push/PR
├── agents/                       # Agent implementations (unchanged)
├── api/
│   ├── __init__.py
│   ├── main.py                   # Slim app factory + CORS
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py               # /api/chat, /api/warmup
│   │   ├── documents.py          # /api/upload
│   │   └── users.py              # /api/auth/register, /api/profile/{id}
│   ├── models.py                 # All Pydantic request/response schemas
│   └── dependencies.py           # Shared deps (profile_store, get_chatbot)
├── configs/
│   └── settings.yaml
├── core/                         # Graph, state, RAG (unchanged)
├── data/                         # Runtime only (fully gitignored)
├── docs/
│   ├── architecture.md           # Was ARCHITECTURE_DIAGRAMS.md
│   ├── demo.md                   # Was DEMO.md
│   ├── deployment.md             # Was DEPLOY.md
│   ├── quick-start.md            # Was QUICK_START.md
│   └── plans/                    # Implementation plans
├── frontend/
│   ├── app/
│   │   ├── chat/page.tsx         # Slim — uses components
│   │   ├── register/page.tsx     # Slim — uses components
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatHeader.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── ChatInput.tsx
│   │   └── register/
│   │       ├── StepBasicInfo.tsx
│   │       ├── StepPersona.tsx
│   │       ├── StepAcademic.tsx
│   │       └── StepGoals.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   └── utils.ts
│   ├── types/
│   │   └── index.ts              # Shared TS interfaces
│   └── ...configs
├── scripts/
│   ├── start_dev.sh              # Was root start_dev.sh
│   ├── setup_env.sh              # Was root setup_env.sh
│   ├── diagnose.sh
│   ├── fix_jsonschema.py
│   └── load_quotes.py
├── tests/                        # Unchanged
├── .env.example
├── .gitignore                    # Updated
├── docker-compose.yml
├── Dockerfile
├── LICENSE
├── Makefile                      # New: common dev commands
├── pyproject.toml                # New: modern Python config
├── README.md                     # Updated links
└── terminal_app.py               # CLI entry (stays at root — it's an entry point)
```

**Files removed from root:** `main.py` (moved to `scripts/demo_tutor.py`), `setup_env.sh`, `start_dev.sh`, `frontend_error.log`, `AGENTS.md`, `ARCHITECTURE_DIAGRAMS.md`, `DEMO.md`, `DEPLOY.md`, `QUICK_START.md`, `README_FRONTEND.md`, `api/requirements.txt`, `api/run.sh`.

---

## Phase 1: Cleanup & Git Hygiene

### Task 1: Remove committed artifacts from git history

Removes `__pycache__/`, log files, and other artifacts that were committed before `.gitignore` caught them. This is the single biggest "red flag" fix.

**Files:**
- Modify: `.gitignore`

**Step 1: Check what's tracked that shouldn't be**

Run:
```bash
git ls-files --cached | grep -E '__pycache__|\.pyc|\.log|frontend_error'
```

Expected: A list of cached `__pycache__` files, `.pyc` files, `frontend_error.log`, etc.

**Step 2: Remove cached artifacts from git index**

```bash
git rm -r --cached __pycache__/ agents/__pycache__/ api/__pycache__/ core/__pycache__/ tests/__pycache__/ 2>/dev/null || true
git rm --cached frontend_error.log 2>/dev/null || true
git rm -r --cached logs/ 2>/dev/null || true
git rm -r --cached data/quotes_store.json data/quotes_seed.json 2>/dev/null || true
```

**Step 3: Update `.gitignore` to also cover edge cases**

Add to `.gitignore` (if not already present):
```
# Artifacts
__pycache__/
*.pyc
frontend_error.log

# Data (all runtime)
/data/

# Node duplicates (npm artifact)
*\ 2/
*\ 2.*
```

**Step 4: Verify nothing unwanted is tracked**

Run:
```bash
git ls-files --cached | grep -E '__pycache__|\.pyc|\.log$'
```

Expected: Empty output.

**Step 5: Commit**

```bash
git add -A
git commit -m "chore: remove committed artifacts (__pycache__, logs, data)"
```

---

### Task 2: Fix broken npm duplicates in frontend

The `node_modules` has many `<package> 2/` duplicate directories (artifact of a broken npm install). This won't be in git (node_modules is gitignored) but it affects local dev.

**Step 1: Clean and reinstall frontend deps**

```bash
rm -rf frontend/node_modules frontend/package-lock.json
cd frontend && npm install && cd ..
```

**Step 2: Verify no "2" directories**

```bash
ls frontend/node_modules/ | grep ' 2' | head -5
```

Expected: Empty output.

**Step 3: Commit the clean lockfile**

```bash
git add frontend/package-lock.json
git commit -m "chore: regenerate clean package-lock.json"
```

---

## Phase 2: Modern Python Tooling

### Task 3: Add `pyproject.toml`

Replaces `requirements.txt` as the single source of truth for Python config. Adds ruff (linting/formatting) and pytest config. This is the #1 signal of a modern Python project.

**Files:**
- Create: `pyproject.toml`
- Delete: `api/requirements.txt` (merge into root)
- Modify: `requirements.txt` (add api deps if missing)

**Step 1: Create `pyproject.toml`**

Create `pyproject.toml` at project root:

```toml
[project]
name = "study-pal"
version = "0.1.0"
description = "AI-driven multimodal study companion with LangGraph multi-agent orchestration"
readme = "README.md"
license = { text = "MIT" }
requires-python = ">=3.10"
dependencies = [
    "langchain>=0.3.0",
    "langchain-core>=0.3.0",
    "langchain-openai>=0.2.0",
    "langchain-community>=0.3.0",
    "langchain-text-splitters>=0.3.0",
    "langgraph>=0.2.0",
    "pydantic>=2.5.0",
    "chromadb>=0.4.0",
    "python-dotenv>=1.0.0",
    "httpx>=0.25.0",
    "openai>=1.30.0",
    "pypdf>=3.17.0",
    "tiktoken>=0.5.0",
    "fastapi>=0.100.0",
    "uvicorn[standard]>=0.20.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "ruff>=0.4.0",
]

[tool.ruff]
target-version = "py310"
line-length = 120

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
ignore = ["E501"]

[tool.ruff.lint.isort]
known-first-party = ["agents", "core", "api"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"
addopts = "-v --tb=short"
```

**Step 2: Merge `api/requirements.txt` into root `requirements.txt`**

Check what `api/requirements.txt` has that root doesn't:

```bash
cat api/requirements.txt
```

Add any missing deps (`fastapi`, `uvicorn`, `python-multipart`) to root `requirements.txt`. Then:

```bash
git rm api/requirements.txt
git rm api/run.sh
```

**Step 3: Update root `requirements.txt` to include API deps**

Ensure `requirements.txt` contains (add if missing):
```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
python-multipart>=0.0.6
```

Also remove `pinecone-client` if it's not actually used (check with `grep -r "pinecone" --include="*.py"`).

**Step 4: Verify ruff works**

```bash
pip install ruff
ruff check . --select E,F,I,W
```

Expected: Some warnings (we'll fix later). No crash.

**Step 5: Commit**

```bash
git add pyproject.toml requirements.txt
git commit -m "build: add pyproject.toml with ruff and pytest config, consolidate deps"
```

---

## Phase 3: Consolidate Documentation

### Task 4: Move markdown files into `docs/`

Root has 7 markdown files besides README. Move them to `docs/` with cleaner names. This immediately makes the root look professional — just README, LICENSE, and configs visible.

**Files:**
- Move: `ARCHITECTURE_DIAGRAMS.md` → `docs/architecture.md`
- Move: `DEMO.md` → `docs/demo.md`
- Move: `DEPLOY.md` → `docs/deployment.md`
- Move: `QUICK_START.md` → `docs/quick-start.md`
- Delete: `AGENTS.md` (merge relevant content into README or `docs/contributing.md`)
- Delete: `README_FRONTEND.md` (merge into `docs/quick-start.md`)
- Keep: `CLAUDE.md` stays at root (it's a tool config file, like `.editorconfig`)

**Step 1: Move the files**

```bash
mv ARCHITECTURE_DIAGRAMS.md docs/architecture.md
mv DEMO.md docs/demo.md
mv DEPLOY.md docs/deployment.md
mv QUICK_START.md docs/quick-start.md
rm README_FRONTEND.md
rm AGENTS.md
```

**Step 2: Update docs/README.md as an index**

Overwrite `docs/README.md`:

```markdown
# Documentation

| Document | Description |
|----------|-------------|
| [Quick Start](quick-start.md) | Setup and run the app locally |
| [Architecture](architecture.md) | System diagrams and agent flow |
| [Deployment](deployment.md) | Docker, AWS, and production deployment |
| [Demo Script](demo.md) | Step-by-step recruiter demo walkthrough |
```

**Step 3: Update README.md links**

In `README.md`, find and replace all old links:
- `[QUICK_START.md](QUICK_START.md)` → `[Quick Start](docs/quick-start.md)`
- `[DEPLOY.md](DEPLOY.md)` → `[Deployment](docs/deployment.md)`
- `[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)` → `[Architecture](docs/architecture.md)`
- `[DEMO.md](DEMO.md)` → `[Demo](docs/demo.md)`
- `[AGENTS.md](AGENTS.md)` → remove or redirect
- `[README_FRONTEND.md](README_FRONTEND.md)` → remove

Also update the Documentation table in README.md to match the new locations.

**Step 4: Verify no broken links**

```bash
grep -n 'QUICK_START\|DEPLOY\.md\|ARCHITECTURE_DIAGRAMS\|DEMO\.md\|AGENTS\.md\|README_FRONTEND' README.md
```

Expected: Empty — all links updated.

**Step 5: Commit**

```bash
git add -A
git commit -m "docs: consolidate markdown files into docs/ directory"
```

---

## Phase 4: Move Loose Root Files

### Task 5: Move shell scripts and demo entry point

Moves `start_dev.sh`, `setup_env.sh`, and `main.py` (tutor demo) out of root into `scripts/`.

**Files:**
- Move: `start_dev.sh` → `scripts/start_dev.sh`
- Move: `setup_env.sh` → `scripts/setup_env.sh`
- Move: `main.py` → `scripts/demo_tutor.py`

**Step 1: Move the files**

```bash
mv start_dev.sh scripts/start_dev.sh
mv setup_env.sh scripts/setup_env.sh
mv main.py scripts/demo_tutor.py
```

**Step 2: Fix internal references in `scripts/start_dev.sh`**

In `scripts/start_dev.sh`, the `SCRIPT_DIR` logic already resolves to the script's directory. It uses `cd "$SCRIPT_DIR"` which will now be `scripts/`. We need it to operate from project root.

Change line 9 from:
```bash
cd "$SCRIPT_DIR"
```
to:
```bash
cd "$SCRIPT_DIR/.."
```

Also update the reference to `setup_env.sh` (line ~24):
```bash
./scripts/setup_env.sh
```

And the jsonschema fix (line ~42):
```bash
python "$SCRIPT_DIR/fix_jsonschema.py" 2>/dev/null || true
```

**Step 3: Update README.md references**

In README.md, update:
- `./start_dev.sh` → `./scripts/start_dev.sh`
- `./setup_env.sh` → `./scripts/setup_env.sh`
- `python main.py` → `python scripts/demo_tutor.py`

Also update `docs/quick-start.md` and `docs/deployment.md` if they reference these scripts.

**Step 4: Update the Repository Structure in README.md**

Replace the old tree in README with the new target structure shown at the top of this plan.

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: move loose scripts and demo entry into scripts/"
```

---

## Phase 5: Add GitHub Actions CI

### Task 6: Create `.github/workflows/ci.yml`

The README already has a CI badge pointing to a workflow that doesn't exist. This is a major credibility issue. Fix it by creating the actual workflow.

**Files:**
- Create: `.github/workflows/ci.yml`

**Step 1: Create the workflow directory**

```bash
mkdir -p .github/workflows
```

**Step 2: Create `ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install ruff
      - run: ruff check .
      - run: ruff format --check .

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r requirements.txt
      - run: pip install pytest
      - run: pytest tests/ -v --tb=short
    env:
      OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

  frontend-lint:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - run: npm ci
      - run: npm run lint
      - run: npm run build
```

**Step 3: Update the CI badge URL in README.md**

The current badge points to `rom812/study-pal`. Verify this matches your actual GitHub username/repo. If your repo is actually `romsheynis/study_pal`, update the badge:

```markdown
[![CI](https://github.com/<your-username>/study_pal/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/study_pal/actions)
```

**Step 4: Commit**

```bash
git add .github/workflows/ci.yml README.md
git commit -m "ci: add GitHub Actions workflow for lint, test, and frontend build"
```

---

## Phase 6: Add Makefile

### Task 7: Create `Makefile` for common dev commands

A Makefile is a universal developer signal — it says "I thought about DX." Recruiters can run `make help` and immediately understand how to use the project.

**Files:**
- Create: `Makefile`

**Step 1: Create the Makefile**

```makefile
.PHONY: help install dev test lint format clean

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (Python + Node)
	python -m venv .venv
	. .venv/bin/activate && pip install -r requirements.txt && pip install -e ".[dev]"
	cd frontend && npm install

dev: ## Start backend + frontend for development
	./scripts/start_dev.sh

test: ## Run Python tests
	pytest tests/ -v --tb=short

lint: ## Run linters (ruff + eslint)
	ruff check .
	cd frontend && npm run lint

format: ## Auto-format code
	ruff format .
	ruff check --fix .

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .ruff_cache htmlcov .coverage
```

**Step 2: Test it**

```bash
make help
```

Expected: Formatted list of available commands.

**Step 3: Commit**

```bash
git add Makefile
git commit -m "build: add Makefile with dev, test, lint, and format commands"
```

---

## Phase 7: Split API into Routers

### Task 8: Extract Pydantic models from `api/main.py`

Split the monolithic `api/main.py` into proper FastAPI structure with routers and models.

**Files:**
- Create: `api/__init__.py`
- Create: `api/models.py`
- Create: `api/dependencies.py`
- Modify: `api/main.py`

**Step 1: Create `api/__init__.py`**

```python
"""FastAPI backend for Study Pal."""
```

**Step 2: Create `api/models.py`**

Extract all Pydantic models from `api/main.py`:

```python
"""Pydantic request/response models for the Study Pal API."""

from typing import Optional
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    user_id: str
    name: str
    primary_persona: str
    preferred_personas: list[str]
    academic_field: Optional[str] = None
    study_topics: list[str] = []
    goals: list[str] = []
    traits: list[str] = []


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    agent_avatar: str
    agent_name: str


class ProfileResponse(BaseModel):
    user_id: str
    name: str
    primary_persona: str
    preferred_personas: list[str]
    academic_field: Optional[str] = None
    study_topics: list[str] = []
    goals: list[str] = []
    traits: list[str] = []
```

**Step 3: Create `api/dependencies.py`**

Extract shared state (profile store, chatbot instances):

```python
"""Shared dependencies for API routes."""

import logging
import threading
from pathlib import Path

import importlib.util
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Import user_profile directly to avoid agents/__init__.py pulling in chromadb/jsonschema
_user_profile_path = PROJECT_ROOT / "agents" / "user_profile.py"
_spec = importlib.util.spec_from_file_location("user_profile", _user_profile_path)
_user_profile = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_user_profile)
UserProfile = _user_profile.UserProfile
UserProfileStore = _user_profile.UserProfileStore
UserProgressEvent = _user_profile.UserProgressEvent

UserProfile.model_rebuild(_types_namespace={
    'datetime': datetime,
    'Literal': Literal,
    'UserProgressEvent': UserProgressEvent,
})

# Profile store
PROFILES_DIR = PROJECT_ROOT / "data" / "profiles"
PROFILES_DIR.mkdir(parents=True, exist_ok=True)
profile_store = UserProfileStore(PROFILES_DIR)

# Chatbot instances (lazy-loaded)
LangGraphChatbot = None
chatbot_instances: dict = {}
_chatbot_lock = threading.Lock()


def get_or_create_chatbot(user_id: str):
    """Get or create a chatbot instance for a user."""
    global LangGraphChatbot
    with _chatbot_lock:
        if LangGraphChatbot is None:
            logger.info("Lazy loading LangGraphChatbot...")
            from core.langgraph_chatbot import LangGraphChatbot as _LangGraphChatbot
            LangGraphChatbot = _LangGraphChatbot

        if user_id not in chatbot_instances:
            logger.info(f"Creating chatbot instance for user: {user_id}")
            chatbot_instances[user_id] = LangGraphChatbot(user_id=user_id, session_id=user_id)
        return chatbot_instances[user_id]
```

**Step 4: Verify existing tests still pass**

```bash
pytest tests/test_imports.py -v
```

Expected: PASS (imports should still work since we haven't changed module paths yet).

**Step 5: Commit**

```bash
git add api/__init__.py api/models.py api/dependencies.py
git commit -m "refactor(api): extract models and dependencies from main.py"
```

---

### Task 9: Create API routers

Split endpoints from `api/main.py` into separate router files.

**Files:**
- Create: `api/routers/__init__.py`
- Create: `api/routers/users.py`
- Create: `api/routers/chat.py`
- Create: `api/routers/documents.py`
- Modify: `api/main.py`

**Step 1: Create router directory**

```bash
mkdir -p api/routers
```

**Step 2: Create `api/routers/__init__.py`**

```python
"""API route modules."""
```

**Step 3: Create `api/routers/users.py`**

```python
"""User registration and profile routes."""

import logging
from fastapi import APIRouter, HTTPException

from api.models import RegisterRequest, ProfileResponse
from api.dependencies import profile_store, UserProfile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["users"])


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Get user profile by user_id."""
    try:
        profile = profile_store.load(user_id)
        return ProfileResponse(
            user_id=profile.user_id,
            name=profile.name,
            primary_persona=profile.primary_persona,
            preferred_personas=profile.preferred_personas,
            academic_field=profile.academic_field,
            study_topics=profile.study_topics,
            goals=profile.goals,
            traits=profile.traits,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="User profile not found")
    except Exception as e:
        logger.error(f"Error loading profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auth/register", response_model=ProfileResponse)
async def register(request: RegisterRequest):
    """Create a new user profile."""
    try:
        try:
            profile_store.load(request.user_id)
            raise HTTPException(status_code=400, detail="User ID already exists")
        except FileNotFoundError:
            pass

        profile = UserProfile(
            user_id=request.user_id,
            name=request.name,
            primary_persona=request.primary_persona,
            preferred_personas=request.preferred_personas,
            academic_field=request.academic_field,
            study_topics=request.study_topics,
            goals=request.goals,
            traits=request.traits,
            current_focus=request.study_topics[0] if request.study_topics else None,
        )

        profile_store.save(profile)
        logger.info(f"Created profile for user: {request.user_id}")

        return ProfileResponse(
            user_id=profile.user_id,
            name=profile.name,
            primary_persona=profile.primary_persona,
            preferred_personas=profile.preferred_personas,
            academic_field=profile.academic_field,
            study_topics=profile.study_topics,
            goals=profile.goals,
            traits=profile.traits,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 4: Create `api/routers/chat.py`**

```python
"""Chat and chatbot warmup routes."""

import asyncio
import logging
from fastapi import APIRouter, HTTPException

from api.models import ChatRequest, ChatResponse
from api.dependencies import get_or_create_chatbot

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.get("/warmup")
async def warmup(user_id: str):
    """Start loading the chatbot in the background."""
    def _load():
        try:
            get_or_create_chatbot(user_id)
        except Exception as e:
            logger.warning(f"Warmup failed for {user_id}: {e}")

    asyncio.create_task(asyncio.to_thread(_load))
    return {"status": "warming"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a chat message and get response."""
    try:
        chatbot = await asyncio.to_thread(get_or_create_chatbot, request.user_id)
        response_text = await asyncio.to_thread(chatbot.chat, request.message)

        agent_avatar = chatbot.get_current_avatar()
        current_intent = chatbot.get_last_intent()

        agent_name_map = {
            "tutor": "Tutor",
            "scheduler": "Scheduler",
            "analyzer": "Analyzer",
            "motivator": "Motivator",
            "unknown": "System",
        }
        agent_name = agent_name_map.get(current_intent, "System")

        return ChatResponse(
            response=response_text,
            agent_avatar=agent_avatar,
            agent_name=agent_name,
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 5: Create `api/routers/documents.py`**

```python
"""Document upload routes."""

import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from api.dependencies import get_or_create_chatbot, PROJECT_ROOT

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["documents"])


@router.post("/upload")
async def upload_file(
    user_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a PDF file for ingestion."""
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        chatbot = get_or_create_chatbot(user_id)

        upload_dir = PROJECT_ROOT / "data" / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)
        temp_path = upload_dir / file.filename

        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        try:
            import asyncio
            result = await asyncio.to_thread(chatbot.ingest_material, temp_path)
            chunks = await asyncio.to_thread(chatbot.get_materials_count)

            return {"message": result, "chunks": chunks}
        finally:
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

**Step 6: Slim down `api/main.py`**

Replace `api/main.py` with a clean app factory:

```python
"""FastAPI application for Study Pal."""

import os
import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.routers import chat, documents, users

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not os.getenv("OPENAI_API_KEY"):
    logger.warning("OPENAI_API_KEY is not set. Chat and RAG features will fail.")

app = FastAPI(title="Study Pal API", version="1.0.0")

# CORS
_cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if os.environ.get("ALLOWED_ORIGINS"):
    _cors_origins.extend(o.strip() for o in os.environ["ALLOWED_ORIGINS"].split(",") if o.strip())
if os.environ.get("FRONTEND_URL"):
    _cors_origins.append(os.environ["FRONTEND_URL"].rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(dict.fromkeys(_cors_origins)),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router)
app.include_router(chat.router)
app.include_router(documents.router)


@app.get("/")
async def root():
    return {"message": "Study Pal API", "status": "running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Step 7: Verify the API starts**

```bash
PYTHONPATH=. python -c "from api.main import app; print('OK:', app.title)"
```

Expected: `OK: Study Pal API`

**Step 8: Commit**

```bash
git add api/
git commit -m "refactor(api): split monolithic main.py into routers, models, and dependencies"
```

---

## Phase 8: Frontend Component Extraction

### Task 10: Create shared types and extract chat components

The 277-line `chat/page.tsx` and 417-line `register/page.tsx` should use shared components and types.

**Files:**
- Create: `frontend/types/index.ts`
- Create: `frontend/components/chat/MessageBubble.tsx`
- Create: `frontend/components/chat/MessageList.tsx`
- Create: `frontend/components/chat/ChatInput.tsx`
- Create: `frontend/components/chat/ChatHeader.tsx`
- Modify: `frontend/app/chat/page.tsx`

**Step 1: Create types directory and shared types**

```bash
mkdir -p frontend/types frontend/components/chat frontend/components/register
```

Create `frontend/types/index.ts`:

```typescript
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agentAvatar?: string;
  agentName?: string;
}

export const AGENT_NAMES: Record<string, string> = {
  '\uD83D\uDCDA': 'Tutor',
  '\uD83D\uDCC5': 'Scheduler',
  '\uD83D\uDD0D': 'Analyzer',
  '\uD83D\uDCAA': 'Motivator',
  '\uD83E\uDDED': 'Router',
  '\uD83E\uDD16': 'System',
};
```

**Step 2: Create `frontend/components/chat/MessageBubble.tsx`**

```tsx
import { Message } from '@/types';

interface Props {
  message: Message;
}

export function MessageBubble({ message }: Props) {
  return (
    <div className={`flex gap-4 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      {message.role === 'assistant' && (
        <div className="flex-shrink-0">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-2xl">
            {message.agentAvatar || '\uD83E\uDD16'}
          </div>
        </div>
      )}
      <div
        className={`max-w-[80%] rounded-2xl px-6 py-4 ${
          message.role === 'user'
            ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
            : 'bg-[#1a1a1a] border border-gray-800 text-gray-100'
        }`}
      >
        <div className="whitespace-pre-wrap break-words">{message.content}</div>
        {message.role === 'assistant' && message.agentName && (
          <div className="mt-2 text-xs text-gray-500">{message.agentName}</div>
        )}
      </div>
      {message.role === 'user' && (
        <div className="flex-shrink-0">
          <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-2xl">
            \uD83D\uDC64
          </div>
        </div>
      )}
    </div>
  );
}
```

**Step 3: Create `frontend/components/chat/ChatInput.tsx`**

```tsx
interface Props {
  input: string;
  loading: boolean;
  onInputChange: (value: string) => void;
  onSubmit: (e: React.FormEvent) => void;
}

export function ChatInput({ input, loading, onInputChange, onSubmit }: Props) {
  return (
    <footer className="border-t border-gray-800 bg-[#1a1a1a]/50 backdrop-blur-sm">
      <div className="max-w-6xl mx-auto px-4 py-4">
        <form onSubmit={onSubmit} className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => onInputChange(e.target.value)}
            placeholder="Ask a question or request help..."
            disabled={loading}
            className="flex-1 px-6 py-4 bg-[#0a0a0a] border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-8 py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 rounded-xl font-medium text-white transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
          >
            Send
          </button>
        </form>
      </div>
    </footer>
  );
}
```

**Step 4: Update `frontend/app/chat/page.tsx` to use components**

Replace the inline JSX in the page with imports:

```tsx
'use client';

import { useState, useEffect, useRef } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { apiClient, ChatResponse } from '@/lib/api';
import { Message, AGENT_NAMES } from '@/types';
import { MessageBubble } from '@/components/chat/MessageBubble';
import { ChatInput } from '@/components/chat/ChatInput';

export default function ChatPage() {
  // ... keep all existing state and handlers ...
  // Replace inline message rendering with <MessageBubble message={message} />
  // Replace inline form with <ChatInput ... />
}
```

> **Note to implementer:** The exact refactoring of `page.tsx` requires replacing the JSX blocks with component references while keeping all `useState`, `useEffect`, and handler logic in the page. The components are pure presentational — they receive props and render. The page keeps all state and logic.

**Step 5: Verify frontend builds**

```bash
cd frontend && npm run build && cd ..
```

Expected: Build succeeds with no errors.

**Step 6: Commit**

```bash
git add frontend/types/ frontend/components/ frontend/app/chat/page.tsx
git commit -m "refactor(frontend): extract chat components and shared types"
```

---

### Task 11: Extract register page components

Similar to Task 10 but for the 417-line register page.

**Files:**
- Create: `frontend/components/register/StepBasicInfo.tsx`
- Create: `frontend/components/register/StepPersona.tsx`
- Create: `frontend/components/register/StepAcademic.tsx`
- Create: `frontend/components/register/StepGoals.tsx`
- Modify: `frontend/app/register/page.tsx`

**Step 1: Extract each step section into its own component**

Each step (1-4) in the register page becomes a component. The components receive form state as props and call callbacks on change. Example for `StepBasicInfo.tsx`:

```tsx
interface Props {
  userId: string;
  name: string;
  onUserIdChange: (value: string) => void;
  onNameChange: (value: string) => void;
}

export function StepBasicInfo({ userId, name, onUserIdChange, onNameChange }: Props) {
  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold mb-6">Basic Information</h2>
      {/* ... existing step 1 JSX with props instead of direct state ... */}
    </div>
  );
}
```

Follow the same pattern for `StepPersona`, `StepAcademic`, `StepGoals`.

**Step 2: Slim down `register/page.tsx`**

The page keeps state and handlers, renders the step components:

```tsx
{step === 1 && <StepBasicInfo ... />}
{step === 2 && <StepPersona ... />}
{step === 3 && <StepAcademic ... />}
{step === 4 && <StepGoals ... />}
```

**Step 3: Verify frontend builds**

```bash
cd frontend && npm run build && cd ..
```

**Step 4: Commit**

```bash
git add frontend/components/register/ frontend/app/register/page.tsx
git commit -m "refactor(frontend): extract register step components"
```

---

## Phase 9: Final Polish

### Task 12: Update `.env.example` and ensure it's committed

**Files:**
- Modify: `.env.example`

**Step 1: Ensure `.env.example` is comprehensive**

```bash
# Required
OPENAI_API_KEY=sk-your-key-here

# Optional: CORS (comma-separated origins)
# ALLOWED_ORIGINS=https://your-frontend.vercel.app
# FRONTEND_URL=https://your-frontend.vercel.app
```

**Step 2: Make sure `.env.example` is tracked (not gitignored)**

Check `.gitignore` — the `*.env` pattern might be catching it. If so, add an exception:

```
!.env.example
```

**Step 3: Commit**

```bash
git add .env.example .gitignore
git commit -m "chore: update .env.example with all config options"
```

---

### Task 13: Run ruff format on the entire codebase

Now that ruff is configured, format everything for consistency.

**Step 1: Auto-format**

```bash
ruff format .
ruff check --fix .
```

**Step 2: Review changes**

```bash
git diff --stat
```

Make sure only whitespace/import-order changes happened — no logic changes.

**Step 3: Commit**

```bash
git add -A
git commit -m "style: apply ruff formatting across codebase"
```

---

### Task 14: Final README structure update

Update the README's repository structure section and documentation table to reflect all changes.

**Step 1: Update the Repository Structure block in README.md**

Replace with the target structure from the top of this plan.

**Step 2: Update the Documentation table**

```markdown
## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Overview, entry points, architecture |
| [Quick Start](docs/quick-start.md) | Web UI setup and first run |
| [Deployment](docs/deployment.md) | Docker and AWS deployment |
| [Architecture](docs/architecture.md) | Mermaid diagrams: workflow, RAG, state |
| [Demo Script](docs/demo.md) | Step-by-step recruiter demo |
```

**Step 3: Verify all internal links work**

```bash
grep -oP '\[.*?\]\(.*?\)' README.md | grep -v http | while read link; do
  file=$(echo "$link" | grep -oP '\(.*?\)' | tr -d '()')
  [ ! -f "$file" ] && echo "BROKEN: $link -> $file"
done
```

Expected: No broken links.

**Step 4: Commit**

```bash
git add README.md
git commit -m "docs: update README with new project structure and links"
```

---

## Summary: What Changes (and What Doesn't)

### Changed
- Root is clean: just README, LICENSE, pyproject.toml, Makefile, Dockerfile, docker-compose, terminal_app.py
- `api/main.py` split into routers/models/dependencies (same endpoints, same behavior)
- Frontend has `components/` and `types/` directories
- All docs consolidated under `docs/`
- Scripts moved to `scripts/`
- CI actually exists (matching the badge!)
- Modern Python tooling (`pyproject.toml`, ruff)

### NOT Changed
- `agents/` — same files, same structure
- `core/` — same files, same structure (workflow_nodes.py is big but functional; splitting it is a separate task)
- `tests/` — same files, same structure
- `terminal_app.py` — stays at root (it's a user entry point)
- All API behavior — same endpoints, same responses
- All frontend behavior — same pages, same UX
