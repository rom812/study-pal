# AGENTS.md – Study Pal

Guidance for AI agents and humans working on this codebase. Keep this file updated when architecture or conventions change.

---

## 1. Coding Partnership

- **Architect & Senior Developer:** You design the system, set the standards, and review the work.
- **Implementation Assistant:** I translate your architecture into code, propose implementations, and surface considerations for your approval.
- **Workflow:** You define requirements and constraints; I suggest concrete changes, await your confirmation, and help execute them.
- **Checks & Balance:** You remain the final authority on design decisions; I provide detailed reasoning, alternatives when relevant, and keep the implementation aligned with your direction.

Together we keep the feedback loop tight: you guide the architecture, I implement through you.

---

## 2. Project Identity

**Study Pal** is an AI-driven multimodal study companion: LangGraph multi-agent orchestration, RAG tutoring, post-session analysis, scheduling, and motivation. See **README.md** for full overview, demo script, and roadmap.

---

## 3. Architecture (Canonical)

- **Orchestration:** LangGraph state machine in `core/workflow_graph.py`; node logic in `core/workflow_nodes.py`; shared state in `core/workflow_state.py`.
- **Agents:** Intent Router (in nodes) → Tutor / Analyzer / Scheduler / Motivator. Agent implementations live in `agents/` (e.g. `tutor_agent.py`, `scheduler_agent.py`, `motivator_agent.py`, `weakness_detector_agent.py`).
- **RAG:** `core/rag_pipeline.py` + ChromaDB; used by the Tutor agent.
- **UI:** Terminal (`terminal_app.py`) or FastAPI + Next.js (`api/main.py`, `frontend/`); chatbot wrapper in `core/langgraph_chatbot.py`.
- **External:** `core/mcp_connectors.py` for calendar and other services.

When changing behavior or adding features, respect this split: graph and state in `core/`, agent logic in `agents/`, UI and wiring in `terminal_app.py`, `api/main.py`, and `core/langgraph_chatbot.py`.

---

## 4. Tech Stack (Conventions)

| Area        | Choice              | Notes                                      |
|------------|---------------------|--------------------------------------------|
| Language   | Python 3.10+        | Type hints encouraged; avoid unnecessary deps. |
| LLM/Chain  | LangChain + OpenAI  | GPT-4o-mini as default generative core.   |
| Graph      | LangGraph           | Nodes return state updates; no side-only nodes. |
| RAG        | ChromaDB + embeddings | User materials; keep retrieval in `core/rag_pipeline.py`. |
| UI         | Terminal or FastAPI + Next.js | Entry points: `terminal_app.py`, `api/main.py`, `frontend/`. |
| Config/Env | `.env` / env vars   | No secrets in repo; document required vars in README. |

---

## 5. Repo Layout (Quick Reference)

```
study_pal/
├── agents/           # Agent logic (tutor, scheduler, motivator, weakness_detector, user_profile)
├── api/              # FastAPI backend for Next.js frontend
├── core/              # Graph, state, RAG, chatbot wrapper, MCP connectors
├── frontend/          # Next.js chat UI
├── data/profiles/     # User personas (gitignored)
├── logs/              # Runtime logs
├── main.py            # Tutor-only demo (RAG + TutorAgent)
├── terminal_app.py    # Full graph, terminal UI
├── requirements.txt
├── README.md
├── QUICK_START.md     # Frontend + API setup
└── AGENTS.md          # This file
```

When adding files, place them under `agents/` or `core/` (or a new top-level dir only if justified and documented).

---

## 6. How to Work Here

- **Flow / “who calls what”:** Prefer tracing via the graph and node names (e.g. `workflow_nodes.py` → `agents/`) over ad-hoc grep. The Intent Router in `workflow_nodes.py` is the entry; follow edges in `workflow_graph.py` for control flow.
- **State:** All shared session state is defined in `core/workflow_state.py`. New features that need cross-node data should extend this schema rather than introducing global or file-based state.
- **Agents:** Each agent in `agents/` should stay focused on one responsibility; orchestration and routing stay in `core/workflow_nodes.py` and `core/workflow_graph.py`.
- **RAG:** Changes to retrieval (chunking, embedding, collection naming) belong in `core/rag_pipeline.py`; agents only call the exposed interface.
- **Tests:** Prefer running the app and/or `pytest tests/` after changes. Add or extend tests when touching graph edges, state, or agent contracts.
- **Docs:** Update README.md for user-facing or setup changes; update this AGENTS.md when architecture or conventions change.

---

## 7. Out of Scope / Don’t Do

- Don’t commit API keys, tokens, or credentials (use `.env` and document in README).
- Don’t add heavy new dependencies without alignment with the Architect.
- Don’t bypass the LangGraph graph (e.g. direct agent-to-agent calls that skip state) unless explicitly part of an approved design.
- Don’t store user or session data outside the defined state and `data/profiles/` without explicit approval.

---

*Study Pal – agentic study companion. Keep this file in sync with the architecture.*
