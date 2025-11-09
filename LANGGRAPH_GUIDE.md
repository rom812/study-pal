# LangGraph Multi-Agent System - Phase 4

## 🎉 What We Built

We've successfully implemented **Phase 4** - a complete LangGraph-powered multi-agent system! The system now automatically routes user messages to the appropriate agent without needing manual commands.

## 🏗️ Architecture Overview

### Before (Phase 3): Manual Routing
```
User types: /finish → Manually calls Analyzer
User types: /schedule → Manually calls Scheduler
User asks question → Goes to Tutor only
```

### After (Phase 4): Automatic Multi-Agent Routing
```
User: "What is calculus?"
  → LangGraph detects TUTOR intent → Tutor Agent answers

User: "Schedule study time 2-5pm"
  → LangGraph detects SCHEDULE intent → Scheduler Agent creates plan

User: "Analyze my weak points"
  → LangGraph detects ANALYZE intent → Analyzer Agent reviews session

User: "I need motivation"
  → LangGraph detects MOTIVATE intent → Motivator Agent encourages
```

## 📁 New Files Created

### 1. `core/workflow_state.py`
**Purpose**: Defines the shared state (memory) that all agents use.

**Key Concept**: Think of this as a shared notebook where agents write their results and read what others wrote.

```python
class StudyPalState(TypedDict):
    messages: list[BaseMessage]      # Conversation history
    user_id: str                     # Who is chatting
    current_intent: str              # What user wants (tutor/schedule/analyze)
    weak_points: dict                # Analysis results
    generated_schedule: dict         # Created schedules
    next_agent: str                  # Where to route next
```

### 2. `core/workflow_nodes.py`
**Purpose**: Contains all the agent nodes (workers) that do the actual work.

**Nodes Created**:
- `intent_router_node`: Figures out what the user wants
- `tutor_agent_node`: Answers questions using RAG
- `scheduler_agent_node`: Creates Pomodoro study schedules
- `analyzer_agent_node`: Finds weak points in conversation
- `motivator_agent_node`: Provides encouragement

**Key Concept**: Each node is a Python function that:
1. Receives the current state
2. Does its work (answer question, create schedule, etc.)
3. Returns updates to the state

### 3. `core/workflow_graph.py`
**Purpose**: Connects all nodes together into a workflow graph.

**The Flow**:
```
START
  ↓
[Intent Router] ← Analyzes user message
  ↓
  ├→ [Tutor] → END
  ├→ [Scheduler] → END
  ├→ [Analyzer] → END
  └→ [Motivator] → END
```

**Key Functions**:
- `create_study_pal_graph()`: Builds the complete workflow
- `run_workflow()`: Helper to run a single message
- `stream_workflow()`: Stream updates in real-time

### 4. `core/langgraph_chatbot.py`
**Purpose**: User-friendly chatbot interface for the LangGraph system.

**What It Does**:
- Wraps the complex graph in a simple `chat()` method
- Maintains conversation history automatically
- Provides material management (ingest, clear, etc.)
- Handles errors gracefully

### 5. `test_langgraph.py`
**Purpose**: Test script to verify all agents work correctly.

**Tests**:
1. Tutor intent detection
2. Scheduler intent detection
3. Analyzer intent detection
4. Motivator intent detection

## 🔑 Key LangGraph Concepts You Learned

### 1. **State**
The shared memory all agents access. Uses `TypedDict` for type safety.

```python
# State is like a dictionary with predefined fields
state = {
    "messages": [...],
    "user_id": "alice",
    "current_intent": "tutor"
}
```

### 2. **Nodes**
Functions that do work. Receive state, return updates.

```python
def my_node(state: StudyPalState) -> dict:
    # Read from state
    user_message = state["messages"][-1]

    # Do work
    response = do_something(user_message)

    # Return updates
    return {"messages": [AIMessage(content=response)]}
```

### 3. **Edges**
Connections between nodes. Two types:

**Direct Edge**: Always go from A to B
```python
graph.add_edge("tutor", END)  # After tutor, always end
```

**Conditional Edge**: Decide where to go based on state
```python
def router(state):
    if state["intent"] == "tutor":
        return "tutor"
    else:
        return "scheduler"

graph.add_conditional_edges("router", router, {
    "tutor": "tutor",
    "scheduler": "scheduler"
})
```

### 4. **Memory (Checkpointer)**
Remembers conversations across multiple turns.

```python
memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)

# Each session gets its own memory
config = {"configurable": {"thread_id": "user_123"}}
```

## 🚀 How to Use

### Option 1: Run the Test
```bash
python test_langgraph.py
```

This runs 4 tests showing all intents working.

### Option 2: Use the Interactive Chatbot
```bash
python main.py --chat
```

Now just chat naturally!

**Examples**:
```
You: What is a derivative?
→ Automatically routes to Tutor Agent

You: I'm free 2-5pm tomorrow, schedule my study time
→ Automatically routes to Scheduler Agent

You: Can you analyze my weak points?
→ Automatically routes to Analyzer Agent

You: I need some motivation!
→ Automatically routes to Motivator Agent
```

### Option 3: Use Legacy Mode (Phase 3)
```python
# In main.py
start_chatbot(user_id="alice", use_langgraph=False)
```

## 📊 Workflow Visualization

```
┌─────────────────────────────────────────────────────────┐
│                     User Input                          │
│            "What is calculus?"                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────────────────────┐
│              Intent Router Node                        │
│  Analyzes message, detects "tutor" intent             │
│  Sets: next_agent = "tutor"                           │
└────────────────┬───────────────────────────────────────┘
                 │
                 ▼
        ┌────────┴────────┐
        │ Routing Decision │
        └────────┬─────────┘
                 │
    ┌────────────┼────────────┬─────────────┐
    │            │            │             │
    ▼            ▼            ▼             ▼
┌───────┐   ┌──────────┐  ┌─────────┐  ┌──────────┐
│ Tutor │   │Scheduler │  │Analyzer │  │Motivator │
│       │   │          │  │         │  │          │
└───┬───┘   └────┬─────┘  └────┬────┘  └────┬─────┘
    │            │             │            │
    └────────────┼─────────────┼────────────┘
                 │
                 ▼
         ┌───────────────┐
         │      END      │
         │  Return Result │
         └───────────────┘
```

## 🎓 Learning Outcomes

After this implementation, you now understand:

1. **LangGraph Basics**
   - State management with TypedDict
   - Node creation (simple functions)
   - Edge routing (direct and conditional)
   - Memory/checkpointing for conversations

2. **Multi-Agent Orchestration**
   - How to coordinate multiple AI agents
   - Intent detection and routing
   - Shared state between agents
   - Error handling in workflows

3. **Production Patterns**
   - Separating concerns (state/nodes/graph)
   - Testing multi-agent systems
   - Graceful error handling
   - User-friendly interfaces

## 🔧 Customization Ideas

### Add a New Agent
1. Create node function in `workflow_nodes.py`
2. Add to graph in `workflow_graph.py`
3. Update intent router to detect new intent
4. Test it!

### Improve Intent Detection
Replace keyword matching in `intent_router_node` with:
- LLM-based classification (more accurate)
- Few-shot examples
- Hybrid approach

### Add More Intelligence
- Make analyzer more sophisticated
- Add multi-turn scheduling conversations
- Create persona-based tutoring styles
- Add progress tracking

## 📝 Next Steps (Future Enhancements)

1. **Better Intent Classification**: Use LLM instead of keywords
2. **Streaming Responses**: Show responses as they're generated
3. **Agent Collaboration**: Let agents call each other (e.g., Tutor → Analyzer)
4. **Persistence**: Save conversation state to database
5. **Analytics**: Track which agents are used most
6. **LangSmith Integration**: Monitor and debug workflows visually

## 🐛 Troubleshooting

### "Collection expecting embedding with dimension..."
**Solution**: Clear old ChromaDB: `rm -rf data/chroma_db`

### No study materials loaded
**Solution**: Ingest a PDF first: `/ingest tests/fixtures/calculus_sample.pdf`

### Agent not routing correctly
**Solution**: Check intent keywords in `intent_router_node()` or add logging

## 📚 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [Multi-Agent Systems Guide](https://python.langchain.com/docs/use_cases/agent_workflows)

---

## ✅ Phase 4 Complete!

You now have a fully functional multi-agent system that:
- ✅ Automatically routes to correct agents
- ✅ Maintains conversation history
- ✅ Handles all 4 agent types (Tutor, Scheduler, Analyzer, Motivator)
- ✅ Has graceful error handling
- ✅ Is production-ready

**Well done! You've built a sophisticated AI system! 🎉**
