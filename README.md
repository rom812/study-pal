# Study Pal – AI-Driven Multimodal Study Companion

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-green.svg)](https://github.com/langchain-ai/langgraph)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-18-black?style=flat&logo=next.js)](https://nextjs.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector%20Store-orange.svg)](https://www.trychroma.com/)
[![Tests](https://github.com/romsheynis/study_pal/actions/workflows/test.yml/badge.svg)](https://github.com/romsheynis/study_pal/actions)

**Quick Start:** `./start_dev.sh` → open http://localhost:3000 (see [QUICK_START.md](QUICK_START.md))

<div align="center">
  <img src="docs/screenshot.png" alt="Study Pal Chat UI" width="80%" />
</div>

Study Pal is your autonomous study mentor: it plans lessons, delivers personalized tutoring, tracks comprehension, and keeps motivation high. Built on **LangGraph**, modern LLMs, and a **multi-agent architecture**, it works like a full learning team in your pocket.

---

## Table of Contents

- [Why Study Pal Stands Out](#-why-study-pal-stands-out)
- [Architecture Overview](#-architecture-overview)
- [Workflow](#-workflow)
- [Tech Stack](#-tech-stack)
- [Entry Points & How to Run](#-entry-points--how-to-run)
- [Repository Structure](#-repository-structure)
- [Environment Variables](#-environment-variables)
- [Agent Roles](#-agent-roles)
- [Demo Script](#-demo-script-recruiter-ready)
- [Development & Testing](#-development--testing)
- [Documentation](#-documentation)
- [Security & Privacy](#-security--privacy)
- [Roadmap](#-roadmap)
- [About](#-about)

---

## Why Study Pal Stands Out

- **Agentic intelligence** – LangGraph orchestrates specialized agents that collaborate to plan, teach, analyze, and motivate.
- **Adaptive RAG tutoring** – Explanations are grounded in your uploaded materials; the system minimizes hallucination and stays on-topic.
- **Post-session intelligence** – Sessions can end with AI-generated weakness analysis and prompts to schedule the next one.
- **GPT-4o-class performance** – End-to-end flows (tutoring, analysis, motivation, scheduling) run without manual switching.

---

## Architecture Overview

### Core Agents

| Agent | Role | Highlights |
|-------|------|------------|
| **Intent Router** | Entry point | LLM-based classification: tutoring, scheduling, analysis, or motivation. |
| **Tutor Agent** | Active session | RAG-powered Q&A, quizzes, explanations; adapts to user level. |
| **Analyzer Agent** | Post-session | Summaries, strengths/weaknesses, learning objectives; writes to shared state. |
| **Scheduler Agent** | Planning | Suggests sessions from weak points and availability; optional calendar sync. |
| **Motivator Agent** | Engagement | Persona-aligned motivational messages using user profile and quotes. |

Orchestration lives in **LangGraph**: one state machine, one entry (Intent Router), conditional edges to the right agent. Shared state is a `TypedDict` with message history, session flags, and analysis/schedule data. See [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) for detailed diagrams.

---

## Workflow

```mermaid
flowchart TD
    Start([User Message]) --> Router{Intent Router}
    Router -- "Motivation" --> Motivator
    Router -- "Tutoring" --> Tutor
    Router -- "Analysis" --> Analyzer
    Router -- "Scheduling" --> Scheduler
    Tutor -->|User done| Analyzer
    Analyzer -->|Yes| Scheduler
    Scheduler -->|Calendar sync?| Calendar
    Analyzer -->|Motivation?| Motivator
    Motivator --> End([✅])
    Scheduler --> End
    Analyzer --> End
    Tutor -->|More questions| Tutor
```

### Session flow (high level)

1. **Intent** – Classify the user message (tutor / scheduler / analyzer / motivator).
2. **Tutoring** – Answer questions with RAG over uploaded materials; support quizzes and follow-ups.
3. **Wrap-up** – When the user is done, run the Analyzer for summary and weak points.
4. **Scheduling** – Optionally suggest and create a study plan; optionally sync to calendar (e.g. MCP).
5. **Motivation** – Deliver a persona-aligned motivational message when requested.

---

## Tech Stack

| Layer | Technology | Role |
|-------|------------|------|
| **Orchestration** | LangGraph | State machine, nodes, conditional edges, checkpointer. |
| **LLM / chains** | LangChain + OpenAI | GPT-4o-mini for tutoring, routing, analysis, messaging. |
| **RAG** | ChromaDB + OpenAI embeddings | User materials: chunking, embedding, retrieval in `core/rag_pipeline.py`. |
| **Backend** | FastAPI | REST API for the Next.js frontend (`api/main.py`). |
| **Frontend** | Next.js | Chat UI, registration, file upload (`frontend/`). |
| **CLI** | Python | Full graph in the terminal (`terminal_app.py`). |
| **Config** | `.env` / env vars | API keys and optional MCP/calendar config. |

---

## Entry Points & How to Run

Study Pal has **three** ways to run. There is **no Gradio**; UIs are **Terminal** and **Web (FastAPI + Next.js)**.

### Prerequisites

- **Python 3.10+**
- **OpenAI API key** (required)
- **Node.js 18+** (only for Web UI)
- Optional: Calendar MCP or other external service credentials (see [Environment variables](#-environment-variables))

### Option A – Terminal UI (full graph)

Best for trying the full multi-agent flow locally.

```bash
git clone https://github.com/<your-handle>/study_pal.git
cd study_pal
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...   # or use .env
python terminal_app.py
```

Use the terminal chat; you can say `upload` and provide materials, then ask questions, request analysis, scheduling, or a pep talk.

### Option B – Web UI (API + Next.js)

Full graph behind a web chat, registration, and file upload.

1. **Backend:** `api/` (FastAPI)  
2. **Frontend:** `frontend/` (Next.js)  
3. **Quick start:** See **[QUICK_START.md](QUICK_START.md)** for step-by-step setup (e.g. `./start_dev.sh` or running API and frontend separately).

After setup:

- **Frontend:** http://localhost:3000  
- **API:** http://localhost:8000  
- **API docs:** http://localhost:8000/docs  

### Option C – Tutor-only demo

RAG + Tutor agent only; no full graph (no Analyzer/Scheduler/Motivator).

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...
python main.py
```

Useful for testing the RAG pipeline and Tutor in isolation.

### Option D – Run with Docker

One-command API (requires `OPENAI_API_KEY` in `.env` or environment):

```bash
# Build and run API only
docker-compose up --build

# API at http://localhost:8000
# Frontend: run separately with ./start_dev.sh or see DEPLOY.md
```

See [DEPLOY.md](DEPLOY.md) for full deployment options.

---

## Repository Structure

```
study_pal/
├── agents/                    # Agent implementations
│   ├── tutor_agent.py         # RAG tutoring, quizzes
│   ├── scheduler_agent.py     # Study plans, calendar
│   ├── motivator_agent.py     # Persona-based motivation
│   ├── weakness_detector_agent.py
│   ├── user_profile.py        # Profile / persona handling
│   ├── onboarding.py
│   └── ...
├── api/                       # FastAPI backend for Web UI
│   ├── main.py                # API entry, chat/upload endpoints
│   └── requirements.txt
├── core/                      # Graph, state, RAG, chatbot
│   ├── workflow_graph.py      # LangGraph graph definition
│   ├── workflow_nodes.py      # Intent router + agent node functions
│   ├── workflow_state.py      # Shared state (StudyPalState)
│   ├── langgraph_chatbot.py   # Chatbot wrapper around the graph
│   ├── rag_pipeline.py        # ChromaDB retrieval pipeline
│   ├── document_processor.py  # PDF chunking
│   ├── vector_stores.py       # ChromaDB wrapper
│   ├── mcp_connectors.py      # Calendar / external services
│   └── ...
├── frontend/                  # Next.js chat UI
│   ├── app/                   # Pages (chat, register, etc.)
│   └── lib/                   # API client, utils
├── configs/                   # YAML/config (e.g. settings.yaml)
├── data/                      # Runtime data (profiles, chroma, quotes)
├── logs/                      # Runtime logs
├── scripts/                   # Utilities (e.g. load_quotes.py)
├── tests/                     # Pytest tests
├── main.py                    # Tutor-only demo entry
├── terminal_app.py            # Full graph, terminal UI
├── start_dev.sh               # Start API + frontend for dev
├── requirements.txt           # Python deps (root)
├── QUICK_START.md             # Web UI setup
├── AGENTS.md                  # For AI agents / contributors
├── ARCHITECTURE_DIAGRAMS.md    # Mermaid diagrams
└── README.md                  # This file
```

- **Orchestration:** `core/workflow_graph.py`, `core/workflow_nodes.py`, `core/workflow_state.py`  
- **Agents:** `agents/` (Tutor, Scheduler, Motivator, etc.); nodes in `core/workflow_nodes.py` call them.  
- **RAG:** `core/rag_pipeline.py`, `core/document_processor.py`, `core/vector_stores.py`  
- **UIs:** `terminal_app.py` (CLI), `api/main.py` + `frontend/` (Web). No `gradio_app.py`.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for LLM and embeddings. |
| (Others) | No | Optional MCP/calendar or other service config; document in `.env.example` if you add them. |

Create a `.env` in the project root (see `.env.example`). For Web UI, see [QUICK_START.md](QUICK_START.md) for frontend env (e.g. `NEXT_PUBLIC_API_URL`).

---

## Agent Roles

| Agent | Stage | Inputs | Outputs | Purpose |
|-------|--------|--------|---------|--------|
| Intent Router | Every turn | Latest user message, history | `next_agent` | Route to Tutor / Scheduler / Analyzer / Motivator. |
| Tutor Agent | During study | User question, RAG context | Answers, quizzes | Learning grounded in uploaded material. |
| Analyzer Agent | After session | Transcript, state | Summary, weak points, scheduling prompt | Reflection and next-step prompts. |
| Scheduler Agent | On request | Availability, weak points | Pomodoro-style plan, optional calendar events | Turn feedback into concrete plans. |
| Motivator Agent | On request | User profile | Persona-aligned message | Keep engagement high. |

---

## Demo Script (Recruiter Ready)

For a step-by-step demo script (terminal + web), see **[DEMO.md](DEMO.md)**.

1. **Upload materials** – Terminal: type `upload` and provide a PDF path; Web: use the chat upload. Confirm chunk count or success.
2. **Tutoring** – e.g. “Walk me through support vector machines.” Get an explanation (and optionally a quiz).
3. **Quiz** – Ask for a quiz, answer, get grading/feedback.
4. **End session** – e.g. “Thanks, I’m done. Analyze my studying.” Trigger the Analyzer.
5. **Scheduling** – When asked, say “Yes” and give a window (e.g. “Wednesday 18:00–20:00”).
6. **Calendar** – If prompted, confirm “Yes” to sync (when MCP/calendar is configured).
7. **Motivation** – e.g. “Give me a pep talk.” Get a persona-aligned message.

Use **Terminal** (`python terminal_app.py`) or **Web UI** ([QUICK_START.md](QUICK_START.md)). Watch logs to see LangGraph hand-offs.

---

## Development & Testing

- **Run the full graph:** `python terminal_app.py` or run API + frontend per QUICK_START.
- **Run tutor-only:** `python main.py`.
- **Tests:** From repo root, run e.g. `pytest tests/` (see `tests/` for RAG, agents, terminal, etc.). After doc or code changes, run tests to avoid regressions.
- **Code layout:** Keep graph/state/nodes in `core/`; agent logic in `agents/`; RAG in `core/rag_pipeline.py`. See [AGENTS.md](AGENTS.md) for conventions.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | This file – overview, entry points, structure. |
| [QUICK_START.md](QUICK_START.md) | Web UI: frontend + API setup, first run, troubleshooting. |
| [DEPLOY.md](DEPLOY.md) | Run UI locally for demo; deploy frontend + API for a shareable URL. |
| [AGENTS.md](AGENTS.md) | For contributors and AI agents: architecture, repo layout, conventions. |
| [ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md) | Mermaid diagrams: workflow, RAG, state. |
| [README_FRONTEND.md](README_FRONTEND.md) | Frontend-specific notes if present. |

---

## Security & Privacy

- User/session data is scoped: per-user Chroma collections and LangGraph state where applicable.
- Materials, analyses, and schedules are not shared across users by design.
- Analyzer outputs stay in session state unless explicitly exported.
- External services (e.g. calendar, quotes) degrade gracefully if unavailable.

---

## Roadmap

- **Memory & reinforcement** – Track skill progression across sessions.
- **Voice mode** – Speech-to-text input; persona-based text-to-speech output.
- **Curriculum builder** – Multi-day study journey generation.
- **Analytics dashboard** – Study streaks, topic mastery, motivation trends.
- **LLM-routed intent** – Already in place; possible refinements (e.g. few-shot router).

---

## About

Study Pal is a modular, agentic study platform that showcases LangGraph, RAG, and multi-agent design. Built by an AI systems engineer focused on turning LLM theory into usable products—agent orchestration, retrieval, and human-in-the-loop flows. If you want to extend or ship agentic, multimodal AI experiences, this repo is a solid reference.

---

**Study Pal** – more than a chatbot: a modular, agentic coaching platform and a practical example of modern LLM engineering.
