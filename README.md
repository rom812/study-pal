# Study Pal – LangGraph-Powered Multi-Agent Study Assistant

Study Pal is a production-grade multi-agent system that orchestrates four specialized AI agents through LangGraph to deliver an intelligent, personalized studying experience. Built with LangChain, ChromaDB, and Gradio, it demonstrates modern AI architecture patterns including RAG, multi-agent workflows, and external service integration via Model Context Protocol (MCP).

## Key Features

- **LangGraph-Orchestrated Multi-Agent System**: Conditional routing between 4 specialized agents based on intent detection
- **RAG-Powered Tutoring**: Per-user vector stores ensure answers come strictly from uploaded study materials
- **Smart Scheduling**: Pomodoro-based study plans with optional Google Calendar integration (MCP)
- **Adaptive Analysis**: Session-by-session weakness detection using LLM-based analysis
- **Personalized Motivation**: Context-aware motivational messages with web-scraped quotes
- **User Authentication**: Google OAuth-based login with per-user data isolation
- **Comprehensive Testing**: 73+ test cases covering core components and agent logic

## Architecture

### LangGraph Workflow

```
User Input → LangGraphChatbot → Intent Router Node
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
              ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐     ┌──────────┐
              │   Tutor   │     │ Scheduler │     │ Analyzer  │     │Motivator │
              │   Agent   │     │   Agent   │     │   Agent   │     │  Agent   │
              │  (RAG)    │     │(Pomodoro) │     │(Weakness) │     │ (Quotes) │
              └───────────┘     └───────────┘     └───────────┘     └──────────┘
                    │                  │                  │                │
                    └──────────────────┴──────────────────┴────────────────┘
                                       │
                                 Response to User
```

**Implementation Files**:
- `core/langgraph_chatbot.py` - Main chatbot orchestrator with LangGraph workflow
- `core/workflow_graph.py` - LangGraph graph definition and node connections
- `core/workflow_nodes.py` - Intent router and 4 agent node implementations
- `core/workflow_state.py` - Shared state schema for inter-agent communication

### Agent Implementations

**1. Tutor Agent** ([agents/tutor_agent.py](agents/tutor_agent.py))
- Ingests PDFs and creates per-user ChromaDB collections
- Uses RAG (Retrieval-Augmented Generation) to answer questions strictly from uploaded materials
- Conversation history management for contextual responses
- Prevents hallucination through context-only system prompts

**2. Scheduler Agent** ([agents/scheduler_agent.py](agents/scheduler_agent.py))
- Generates Pomodoro-based study schedules with work/break intervals
- Optional Google Calendar integration via MCP connectors
- Structured output using Pydantic models for reliability

**3. Analyzer Agent** ([agents/weakness_detector_agent.py](agents/weakness_detector_agent.py))
- Detects learning weaknesses from study session interactions
- Provides actionable recommendations for improvement
- LLM-powered analysis with structured output

**4. Motivator Agent** ([agents/motivator_agent.py](agents/motivator_agent.py))
- Persona-based motivational messages (Socrates, Feynman, Yoda, etc.)
- Web scraping integration for authentic quotes
- Context-aware encouragement based on user progress

### External Integrations

**Model Context Protocol (MCP)** ([core/mcp_connectors.py](core/mcp_connectors.py)):
- Google Calendar sync for study schedule management
- Graceful degradation when services are unavailable
- Extensible architecture for future integrations (Gmail, Notion, etc.)

**RAG Pipeline** ([core/rag_pipeline.py](core/rag_pipeline.py)):
- Document processing with sentence-transformers embeddings
- Per-user ChromaDB collections for data isolation
- Efficient retrieval with configurable chunk sizes

### User Interface

**Gradio Web App** ([gradio_app.py](gradio_app.py)):
- Google OAuth authentication with secure session management
- Interactive onboarding flow
- Multi-tab interface: Chat, Upload, Analysis, Scheduling
- Real-time material count and session tracking

## Project Structure

```
study_pal/
├── agents/                      # Agent implementations
│   ├── motivator_agent.py       # Motivational message generation
│   ├── scheduler_agent.py       # Study schedule creation
│   ├── tutor_agent.py          # RAG-powered tutoring
│   ├── weakness_detector_agent.py # Session analysis
│   └── quote_store.py          # Quote web scraping
├── core/                        # Core infrastructure
│   ├── langgraph_chatbot.py    # Main chatbot with LangGraph
│   ├── workflow_graph.py        # LangGraph workflow definition
│   ├── workflow_nodes.py        # Agent nodes and intent router
│   ├── workflow_state.py        # Shared state schema
│   ├── rag_pipeline.py         # RAG pipeline implementation
│   ├── mcp_connectors.py       # MCP service connectors
│   └── document_processor.py   # Document ingestion
├── tests/                       # Comprehensive test suite
│   ├── test_tutor.py           # 12 tutor tests
│   ├── test_rag_pipeline.py    # 13 RAG tests
│   ├── test_scheduler_agent.py # 7 scheduler tests
│   ├── test_motivator_agent.py # 4 motivator tests
│   ├── test_document_processor.py # 10 document tests
│   ├── test_onboarding.py      # 20 onboarding tests
│   └── conftest.py             # Shared fixtures
├── data/                        # Data storage (gitignored)
│   ├── chroma_db/              # Per-user vector stores
│   ├── profiles/               # User profiles
│   └── study_materials/        # Uploaded documents
├── configs/
│   └── settings.yaml           # Configuration management
├── gradio_app.py               # Web UI entry point
├── main.py                     # CLI entry point
└── requirements.txt            # Python dependencies
```

## Technical Stack

- **LangChain**: Agent framework and LLM abstractions
- **LangGraph**: Multi-agent workflow orchestration with conditional routing
- **OpenAI GPT-4o-mini**: Primary LLM for all agents
- **ChromaDB**: Vector database for RAG pipeline
- **Gradio**: Web UI framework with OAuth support
- **Pydantic**: Data validation and structured outputs
- **pytest**: Test framework (73+ tests)
- **sentence-transformers**: Document embeddings

## Getting Started

### Prerequisites

```bash
Python 3.10+
OpenAI API key
Google OAuth credentials (for login and calendar sync)
```

### Installation

```bash
# Clone repository
git clone <repo-url>
cd study_pal

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and credentials
```

### Configuration

Required environment variables:
- `OPENAI_API_KEY` - OpenAI API access
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth secret
- `GOOGLE_CALENDAR_MCP_ENDPOINT` (optional) - MCP server for calendar sync

### Running

```bash
# Launch web interface
python gradio_app.py

# CLI interface
python main.py
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_rag_pipeline.py -v
```

## Development Status

### Completed Features
- ✅ Full LangGraph multi-agent orchestration
- ✅ Intent-based routing between 4 agents
- ✅ Per-user RAG pipeline with ChromaDB
- ✅ Google OAuth authentication
- ✅ Gradio web interface with 4 tabs
- ✅ MCP connector framework
- ✅ 73+ test cases covering core functionality
- ✅ Pydantic validation for structured outputs

### Known Limitations
- LangGraph workflow tests not yet implemented (planned)
- Intent routing is keyword-based (LLM-based routing planned)
- Global state in Gradio app (refactoring for scalability planned)
- Calendar sync requires MCP server setup (optional feature)

## Demo Video Preparation

This project is designed to showcase in technical interviews:

**Key Talking Points**:
1. **Modern Stack**: Demonstrates proficiency with cutting-edge LangChain/LangGraph ecosystem
2. **Clean Architecture**: Clear separation of concerns (state, nodes, graph, agents)
3. **Production Patterns**: Per-user isolation, graceful degradation, structured outputs
4. **Testing Discipline**: Comprehensive test suite showing quality focus
5. **External Integrations**: MCP connectors demonstrate API integration skills

**Code Walkthrough Sequence**:
1. [core/workflow_state.py](core/workflow_state.py) - Shared state definition
2. [core/workflow_graph.py](core/workflow_graph.py) - LangGraph workflow
3. [core/workflow_nodes.py](core/workflow_nodes.py) - Intent router logic
4. [agents/tutor_agent.py](agents/tutor_agent.py) - RAG implementation
5. [gradio_app.py](gradio_app.py) - UI and session management

## Future Enhancements

- [ ] Add LangGraph workflow integration tests
- [ ] Migrate to LLM-based intent routing for better accuracy
- [ ] Implement Redis-backed session management for horizontal scaling
- [ ] Add daily summary agent for end-of-day recaps
- [ ] Build analytics dashboard for productivity trends
- [ ] Add voice mode with persona-based TTS
- [ ] Implement gamification (XP, achievements, streaks)

## Contributing

This is a portfolio project demonstrating AI engineering capabilities. Feedback and suggestions welcome via issues.

## License

MIT License - See LICENSE file for details

---

**Built with**: LangGraph for orchestration, LangChain for agents, ChromaDB for RAG, and Gradio for UI.
