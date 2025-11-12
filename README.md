# Study Pal – Intelligent Multi-Agent Study Assistant

Study Pal is a modular, multi-agent system that combines smart scheduling, adaptive tutoring, and persona-driven motivation to elevate the studying experience. You define the architecture; Codex assists with implementation details and automation while keeping everything aligned with your vision.

## High-Level Goals
- Coordinate independent agents through LangGraph (or Airflow) to deliver a cohesive study companion.
- Integrate with real-world services via Model Context Protocol (MCP) connectors such as Google Calendar and Gmail.
- Guarantee reliable outputs using Pydantic validation and comprehensive automated tests.
- Deliver a RAG-powered tutor that adapts to learner performance over time.

## Core Agents
### Scheduler Agent – Smart Time Manager
- Builds and updates study schedules based on productivity signals.
- Uses MCP integrations (Google Calendar, Gmail) to manage events and reminders.
- Collaborates with the Tutor Agent to allocate sessions and rebalance workloads.
- **QA:** pytest coverage for time conflicts, date parsing, and edge-case handling.

### Motivator Agent – Personalized Inspiration
- Generates motivational messages in the persona selected by the user.
- Pulls real quotes, clips, or stories from external APIs (e.g., YouTube, Wikipedia, quote databases).
- Syncs with the Scheduler to time motivational nudges.
- **QA:** Pydantic schema enforcing `text`, `source`, and `persona_style` fields for every output.

### Tutor Agent – Adaptive Study Companion
- Ingests PDFs, DOCX, or raw text and populates a vector store (ChromaDB or Pinecone).
- Uses LangChain RAG to deliver quizzes, walkthroughs, and feedback loops.
- Reports progress stats back to the Scheduler for dynamic adjustments.
- **QA:** pytest for parsing, retrieval, question generation, and Pydantic models for structured responses.

## System Architecture
```
User ➜ Scheduler Agent ➜ User
   └➜ Motivator Agent ➜ User
   └➜ Tutor Agent ➜ Scheduler Agent ➜ User
```
- **Graph Manager:** Orchestrates agent conversations using LangGraph (primary) with an option to port to Airflow if needed.
- **RAG Pipeline:** Handles text preprocessing, embedding, storage, and retrieval for study materials.
- **MCP Connectors:** Wrap external services (Calendar, Gmail, future APIs) behind a clean interface.

## Suggested Project Structure
```
multi_agent_study_assistant/
├── agents/
│   ├── scheduler_agent.py
│   ├── motivator_agent.py
│   ├── tutor_agent.py
│   └── __init__.py
├── core/
│   ├── rag_pipeline.py
│   ├── mcp_connectors.py
│   ├── graph_manager.py
│   ├── utils.py
│   └── __init__.py
├── tests/
│   ├── test_scheduler.py
│   ├── test_motivator.py
│   ├── test_tutor.py
│   ├── test_rag_pipeline.py
│   └── conftest.py
├── data/
│   ├── embeddings/
│   ├── study_materials/
│   └── logs/
├── configs/
│   ├── settings.yaml
│   └── credentials.json  # excluded from git
├── main.py
├── requirements.txt
└── README.md
```

## Development Pipeline
1. **Bootstrap Environment**
   - Define `requirements.txt` with LangChain, LangGraph, Pydantic, pytest, ChromaDB, OAuth libraries, etc.
   - Create Dockerfile and devcontainer for reproducible environments.

2. **Core Infrastructure**
   - Implement `settings.yaml` and Pydantic config models for runtime configuration.
   - Stand up `graph_manager.py` with a stubbed LangGraph workflow connecting the three agents.
   - Build MCP connector abstractions with mocked Google services to enable early testing.

3. **Agent Implementations**
   - Start with `scheduler_agent.py`: define interfaces, scheduling heuristics, and calendar sync logic.
   - Add `motivator_agent.py`: persona prompt templates, API fetchers, and message formatting.
   - Implement `tutor_agent.py`: document ingestion, embedding pipeline, and quiz generators.

4. **RAG Pipeline & Data Layer**
   - Implement `rag_pipeline.py` with document loaders, chunking strategy, embedding, and retrieval functions.
   - Wire Tutor Agent to the RAG pipeline and vector store.

5. **Validation & QA**
   - Create Pydantic models for each agent’s outputs.
   - Flesh out pytest suites for unit and integration tests, including LangGraph workflow tests.
   - Configure GitHub Actions CI for linting, tests, and type checks (mypy/ruff optional).

6. **Integrations & Observability**
   - Finalize MCP connectors with real Google Calendar/Gmail integrations.
   - Add logging, telemetry, and performance tracking under `data/logs/`.
   - Prepare analytics hooks for future dashboards.

## Future Enhancements
- Daily Summary Agent for end-of-day recaps.
- Analytics dashboard exposing productivity trends.
- Voice mode and persona-based TTS.
- Gamification mechanics (XP, achievements, streaks).

## Working Agreement
Codex acts as your implementation assistant: you provide architecture and review; Codex crafts the code, tests, and automation under your guidance. See `agents.md` for the partnership agreement.

## Getting Started (Upcoming)
- [ ] Populate `requirements.txt` and `Dockerfile`.
- [ ] Scaffold the module layout under `agents/` and `core/`.
- [ ] Add CI configuration and baseline tests.
- [ ] Implement Scheduler Agent MVP.

Check items off as we progress. Let’s build Study Pal iteratively, validating each component through tests and Pydantic models.
