# Enhanced LangGraph Workflow Architecture

## Overview

The Study Pal system has been upgraded from a simple **hub-and-spoke** architecture to a sophisticated **multi-agent orchestration system** that supports:

- **Multi-turn conversations** (Tutor → Tutor loops)
- **Automatic agent handoffs** (Tutor → Analyzer → Scheduler)
- **Conditional branching** based on user intent and session state
- **State-driven collaboration** between agents

---

## Architecture Diagram

```
                           START
                             ↓
                     [Intent Router]
                   (Keyword-based routing)
                             ↓
        ┌────────────────────┼────────────────────┬─────────────┐
        ↓                    ↓                    ↓             ↓
    [Tutor] ⟲          [Scheduler]          [Analyzer]    [Motivator]
        ↓                    ↓                    ↓             ↓
        ↓ (exit intent)     END              [Scheduler]      END
        ↓                                         ↓
    [Analyzer]                                   END
        ↓
        ↓ (scheduling intent)
        ↓
    [Scheduler]
        ↓
       END
```

---

## State Schema

The enhanced state includes new orchestration fields:

```python
class StudyPalState(TypedDict):
    # Core fields (existing)
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    current_topic: Optional[str]
    current_intent: Optional[str]
    weak_points: Optional[dict]
    generated_schedule: Optional[dict]
    next_agent: Optional[str]
    workflow_complete: bool
    rag_pipeline: Optional[Any]

    # NEW: Multi-agent orchestration fields
    session_mode: Optional[Literal["active_tutoring", "analysis_requested",
                                    "scheduling_requested", "complete"]]
    tutor_session_active: bool
    analysis_results: Optional[dict]
    user_wants_scheduling: bool
```

### Field Descriptions

| Field | Purpose | Set By |
|-------|---------|--------|
| `session_mode` | Tracks workflow state for routing | Tutor, Analyzer, Scheduler |
| `tutor_session_active` | Enables Tutor → Tutor loops | Tutor, Analyzer |
| `analysis_results` | Stores analyzer output for downstream use | Analyzer |
| `user_wants_scheduling` | Triggers Analyzer → Scheduler handoff | Analyzer |

---

## Agent Enhancements

### 1. Tutor Agent

**What Changed:**
- Now returns `tutor_session_active: True` to enable multi-turn loops
- Sets `session_mode: "active_tutoring"`
- Returns `next_agent: "tutor"` (overridden by `route_after_tutor`)

**Exit Detection:**
The `route_after_tutor` function uses LLM-based intent detection to determine if the user wants to:
- **Continue tutoring** → Loop back to Tutor
- **End session** → Forward to Analyzer
- **Exit completely** → Go to END

**Exit Signals:**
- "I'm done", "finish", "that's all"
- "Thanks for your help"
- "Can you analyze my session?"
- "Let's schedule a study plan"

---

### 2. Analyzer Agent

**What Changed:**
- Detects scheduling intent by scanning last 5 user messages for keywords
- Sets `analysis_results` in state for downstream agents
- Sets `user_wants_scheduling` flag for conditional routing
- Updates `tutor_session_active: False` to prevent re-entry to tutoring

**Scheduling Detection:**
Keywords: `["schedule", "plan", "calendar", "study plan", "when should i", "help me plan"]`

**Response Format:**
```
📊 Session Analysis:

I identified 3 areas to focus on:

1. 🔴 CALCULUS DERIVATIVES - severe difficulty
2. 🟡 INTEGRATION - moderate difficulty
3. 🟢 LIMITS - mild difficulty

Would you like me to create a study schedule focusing on these topics?
```

---

### 3. Scheduler Agent

**What Changed:**
- Now checks for `analysis_results` in state
- If analysis exists, displays prioritized topics in response
- Uses weak points from analysis for Pomodoro prioritization

**Enhanced Response:**
```
📚 I've created your study schedule!

📊 Based on your session analysis, I've prioritized: Calculus Derivatives, Integration, Limits

Found 5 study sessions:

1. 📖 14:00 - 15:00: Calculus Derivatives (severe)
2. 📖 15:30 - 16:30: Integration (moderate)
...
```

---

## Conditional Routing Functions

### 1. `route_after_tutor(state) -> str`

**Decision Logic:**
```python
if workflow_complete:
    return "__end__"
elif not tutor_session_active:
    return "__end__"
elif detect_tutor_exit_intent(messages):
    return "analyzer"
else:
    return "tutor"  # Continue tutoring loop
```

**Possible Outputs:**
- `"tutor"` - Loop back for more questions
- `"analyzer"` - User wants to end session
- `"__end__"` - Workflow is complete

---

### 2. `route_after_analyzer(state) -> str`

**Decision Logic:**
```python
if user_wants_scheduling:
    return "scheduler"
elif scheduling_keywords_in_last_message():
    return "scheduler"
else:
    return "__end__"
```

**Possible Outputs:**
- `"scheduler"` - User wants scheduling
- `"__end__"` - No scheduling needed

---

### 3. `detect_tutor_exit_intent(messages) -> bool`

**How It Works:**
1. **Quick keyword check** - Scans for exit keywords to avoid unnecessary LLM calls
2. **LLM-based detection** - If keywords found, uses GPT-4o-mini to detect nuanced intent
3. **Defaults to CONTINUE** - On error, keeps user in tutoring (safer)

**LLM Prompt:**
```
Does the user want to:
A) END the tutoring session and move on
B) CONTINUE with more questions

Reply with ONLY: "END" or "CONTINUE"
```

**Examples:**
- ✅ END: "I'm done for today, can you analyze my weak points?"
- ✅ END: "Thanks, that's all I needed"
- ❌ CONTINUE: "I'm done with this problem, can you give me another?"
- ❌ CONTINUE: "That's all for calculus, can you help me with physics?"

---

## Workflow Execution Paths

### Path 1: Multi-Turn Tutoring → Analysis → Scheduling

```
User: "What is calculus?"
  → Intent Router → Tutor

User: "Can you explain derivatives?"
  → Tutor (loop) ← route_after_tutor detects CONTINUE

User: "Thanks, I'm done. Can you analyze my session?"
  → route_after_tutor detects END intent
  → Analyzer
  → (Analyzer detects "analyze" keyword, sets user_wants_scheduling=False)
  → route_after_analyzer → END

  [User sees analysis with weak points]

User: "Yes, create a schedule for me"
  → Intent Router (detects "schedule")
  → Scheduler
  → (Scheduler references analysis_results from state)
  → Displays prioritized schedule
  → END
```

---

### Path 2: Direct Scheduling (No Analysis)

```
User: "Schedule study from 14-15 tomorrow for Math"
  → Intent Router → Scheduler
  → (No analysis_results in state)
  → Generates schedule without prioritization
  → END
```

---

### Path 3: Tutoring → Auto-Analysis → Auto-Scheduling

```
User: "What is calculus?"
  → Intent Router → Tutor

User: "Can you explain more?"
  → Tutor (loop)

User: "Got it! Can you analyze my session and create a study plan?"
  → route_after_tutor detects END intent
  → Analyzer
  → (Analyzer detects "study plan" → sets user_wants_scheduling=True)
  → route_after_analyzer → Scheduler
  → (Scheduler uses analysis_results for prioritization)
  → END
```

---

### Path 4: Direct Analysis (No Scheduling)

```
User: "Analyze my weak points from our last session"
  → Intent Router → Analyzer
  → (No scheduling keywords detected)
  → route_after_analyzer → END
```

---

## Graph Configuration

### Nodes
- `intent_router` - Entry point, keyword-based routing
- `tutor` - RAG-powered Q&A with multi-turn support
- `scheduler` - Pomodoro study plan generation
- `analyzer` - Weak point detection
- `motivator` - Persona-based encouragement

### Edges

| From | To | Type | Condition |
|------|-----|------|-----------|
| START | intent_router | Direct | Always |
| intent_router | tutor/scheduler/analyzer/motivator | Conditional | Based on `next_agent` |
| tutor | tutor | Conditional | User wants to continue |
| tutor | analyzer | Conditional | User wants to end session |
| tutor | END | Conditional | Workflow complete |
| analyzer | scheduler | Conditional | `user_wants_scheduling=True` |
| analyzer | END | Conditional | No scheduling requested |
| scheduler | END | Direct | Always |
| motivator | END | Direct | Always |

---

## Key Design Decisions

### 1. Why LLM-based exit detection?

**Problem:** Keyword matching fails for nuanced expressions
- ❌ "I'm done with this problem" (wants to continue)
- ✅ "I'm done for today" (wants to exit)

**Solution:** Use GPT-4o-mini for nuanced intent classification with clear examples

---

### 2. Why store `analysis_results` separately from `weak_points`?

**Reason:** Backward compatibility
- Old code checks `weak_points` for scheduler prioritization
- New orchestration uses `analysis_results` for state propagation
- Scheduler checks both: `weak_points or analysis_results`

---

### 3. Why default to "CONTINUE" on error?

**Safety:** If exit detection fails, it's better to keep the user in tutoring than to prematurely exit and lose context.

---

### 4. Why check `tutor_session_active` in routing?

**Prevents loops:** Ensures that once tutoring ends (via Analyzer), the system doesn't accidentally route back to Tutor.

---

## Testing the Workflow

### Test Case 1: Multi-Turn Tutoring
```python
from core.workflow_graph import create_study_pal_graph
from langchain_core.messages import HumanMessage

app = create_study_pal_graph()
config = {"configurable": {"thread_id": "test_session_1"}}

# Turn 1: Start tutoring
state = app.invoke({
    "messages": [HumanMessage(content="What is calculus?")],
    "user_id": "test_user",
    # ... (other required fields)
}, config)

# Turn 2: Continue tutoring (loop)
state = app.invoke({
    "messages": [HumanMessage(content="Can you explain derivatives?")],
}, config)

# Turn 3: Exit to analyzer
state = app.invoke({
    "messages": [HumanMessage(content="Thanks, I'm done!")],
}, config)

# Verify: Last agent should be analyzer
assert state.get("session_mode") == "analysis_requested"
```

---

### Test Case 2: Analyzer → Scheduler Handoff
```python
# After tutoring session with weak points detected...
state = app.invoke({
    "messages": [HumanMessage(content="Can you create a study schedule?")],
}, config)

# Verify: Scheduler received analysis results
assert state.get("session_mode") == "scheduling_requested"
assert state.get("analysis_results") is not None
```

---

## Error Handling

### Loop Prevention
- `tutor_session_active` flag prevents infinite loops
- `workflow_complete` provides explicit exit mechanism
- `route_after_tutor` checks both flags before routing

### LLM Failures
- Exit detection defaults to CONTINUE on error
- Analyzer continues without scheduling detection on error
- All agents have try-except blocks with fallback responses

---

## Performance Considerations

### LLM Call Optimization
1. **Quick keyword check first** - Avoids LLM call if no exit keywords present
2. **Use gpt-4o-mini** - Fast and cheap for routing decisions
3. **Temperature=0** - Deterministic routing decisions

### State Size
- `analysis_results` stores only summary (not full conversation)
- `messages` uses `add_messages` reducer (append-only, efficient)
- Memory checkpointer handles state persistence

---

## Future Enhancements

### Potential Additions
1. **Semantic intent classification** - Replace keyword matching with embedding-based similarity
2. **Sub-workflows** - Quiz generation with grading loops
3. **Validation nodes** - Quality checks before handoffs
4. **Retry mechanisms** - Exponential backoff for failed agents
5. **Dynamic routing** - LLM-based routing instead of conditional functions
6. **Parallel agent execution** - Run Analyzer + Motivator simultaneously

---

## Migration Guide

### For Existing Code

**Before:**
```python
# Old: Single-turn execution
state = app.invoke({"messages": [msg], "user_id": "user123"}, config)
# Workflow always ended after one agent
```

**After:**
```python
# New: Multi-turn support
state = app.invoke({"messages": [msg], "user_id": "user123"}, config)
# Workflow may continue through multiple agents
# Check state["session_mode"] to determine workflow status
```

### Required State Initialization

Add these fields to your initial state:
```python
initial_state = {
    # ... existing fields ...
    "session_mode": None,
    "tutor_session_active": False,
    "analysis_results": None,
    "user_wants_scheduling": False,
}
```

---

## Summary

The enhanced LangGraph workflow transforms Study Pal from a simple routing system into a sophisticated orchestration platform that:

✅ Supports multi-turn conversations with loop detection
✅ Enables automatic agent collaboration (Tutor → Analyzer → Scheduler)
✅ Uses LLM-based intent detection for nuanced routing
✅ Maintains backward compatibility with existing code
✅ Provides explicit state tracking for debugging
✅ Handles errors gracefully with safe defaults

This architecture is **production-ready**, **modular**, and **extensible** for future enhancements.
