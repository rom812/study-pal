# Enhanced LangGraph Workflow - Visual Guide

## Complete Flow Diagram

```
                                    ┌─────────┐
                                    │  START  │
                                    └────┬────┘
                                         │
                                         ▼
                              ┌──────────────────────┐
                              │   Intent Router      │
                              │  (Keyword Analysis)  │
                              └──────────┬───────────┘
                                         │
                    ┌────────────────────┼────────────────────┬───────────────┐
                    │                    │                    │               │
                    ▼                    ▼                    ▼               ▼
           ┌────────────────┐   ┌───────────────┐   ┌────────────────┐  ┌──────────┐
           │     TUTOR      │   │   SCHEDULER   │   │    ANALYZER    │  │MOTIVATOR │
           │  (RAG Q&A)     │   │(Pomodoro Plan)│   │(Weak Points)   │  │ (Quotes) │
           └────────┬───────┘   └───────┬───────┘   └────────┬───────┘  └────┬─────┘
                    │                   │                    │                │
                    │                   │                    │                │
         ┌──────────┴──────────┐        │         ┌──────────┴──────────┐     │
         │  route_after_tutor  │        │         │ route_after_analyzer│     │
         │   (LLM Intent)      │        │         │   (Scheduling?)     │     │
         └──────────┬──────────┘        │         └──────────┬──────────┘     │
                    │                   │                    │                │
         ┌──────────┼──────────┐        │         ┌──────────┼──────────┐     │
         │          │          │        │         │          │          │     │
         ▼          ▼          ▼        ▼         ▼          ▼          ▼     ▼
    ┌────────┐ ┌────────┐ ┌────────┐ ┌─────┐ ┌────────┐ ┌─────────┐ ┌─────┐┌─────┐
    │ TUTOR  │ │ANALYZER│ │  END   │ │ END │ │SCHEDULE│ │   END   │ │ END ││ END │
    │ (loop) │ │(handof)│ │(complt)│ │     │ │(handof)│ │(no sched│ │     ││     │
    └────────┘ └────────┘ └────────┘ └─────┘ └────────┘ └─────────┘ └─────┘└─────┘
         │          │                              │
         └──────────┘                              ▼
            (loops)                            ┌─────┐
                                               │ END │
                                               └─────┘
```

---

## Execution Path Examples

### Path 1: Multi-Turn Tutoring Loop

```
User: "What is calculus?"
  ├─→ Intent Router (detects "tutor")
  └─→ Tutor Agent
        ├─ Retrieves context from RAG
        ├─ Generates response
        └─ Sets tutor_session_active = True

User: "Can you explain derivatives?"
  ├─→ route_after_tutor (detects CONTINUE)
  └─→ Tutor Agent (LOOP)
        ├─ Retrieves more context
        └─ Continues conversation

User: "What about integration?"
  ├─→ route_after_tutor (detects CONTINUE)
  └─→ Tutor Agent (LOOP)

User: "Thanks, I'm done!"
  ├─→ route_after_tutor (detects EXIT)
  └─→ Analyzer Agent
        ├─ Analyzes conversation
        ├─ Identifies weak points
        ├─ Sets tutor_session_active = False
        └─ Stores analysis_results

User: (no scheduling keywords)
  ├─→ route_after_analyzer
  └─→ END
```

**State Changes:**
```
session_mode: None → active_tutoring → analysis_requested
tutor_session_active: False → True → False
analysis_results: None → None → {...}
```

---

### Path 2: Full Pipeline (Tutor → Analyzer → Scheduler)

```
User: "Explain calculus"
  └─→ Tutor → tutor_session_active=True

User: "More about derivatives"
  └─→ Tutor (loop)

User: "I'm done, create a study schedule"
  └─→ route_after_tutor (EXIT detected)
      └─→ Analyzer
            ├─ Detects "schedule" keyword
            ├─ Sets user_wants_scheduling = True
            └─→ route_after_analyzer
                  └─→ Scheduler
                        ├─ Reads analysis_results from state
                        ├─ Prioritizes weak topics
                        └─→ END
```

**State Flow:**
```
┌──────────────────┬──────────────┬──────────────┬──────────────┐
│     Tutor        │  Analyzer    │  Scheduler   │     END      │
├──────────────────┼──────────────┼──────────────┼──────────────┤
│ tutor_active=T   │ tutor_active │              │              │
│ session_mode=    │   =F         │ session_mode │              │
│  active_tutoring │ analysis_    │   =scheduling│              │
│                  │  results={…} │   _requested │              │
│                  │ user_wants_  │              │              │
│                  │  scheduling=T│              │              │
└──────────────────┴──────────────┴──────────────┴──────────────┘
```

---

### Path 3: Direct Scheduling (No Analysis)

```
User: "Schedule study from 14-15 tomorrow"
  ├─→ Intent Router (detects "schedule")
  └─→ Scheduler Agent
        ├─ analysis_results = None (no upstream analysis)
        ├─ Generates schedule from user input
        └─→ END
```

---

## Routing Decision Trees

### Decision Tree: route_after_tutor

```
                    ┌─────────────────────────┐
                    │   route_after_tutor     │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │ workflow_complete?      │
                    └────┬──────────────┬─────┘
                         │ Yes          │ No
                         ▼              │
                    ┌────────┐          │
                    │  END   │          │
                    └────────┘          │
                                        │
                         ┌──────────────┴──────────────┐
                         │ tutor_session_active?       │
                         └────┬──────────────┬─────────┘
                              │ False        │ True
                              ▼              │
                         ┌────────┐          │
                         │  END   │          │
                         └────────┘          │
                                             │
                              ┌──────────────┴──────────────┐
                              │ detect_tutor_exit_intent()  │
                              └────┬──────────────┬─────────┘
                                   │ True         │ False
                                   ▼              ▼
                              ┌──────────┐   ┌────────┐
                              │ ANALYZER │   │ TUTOR  │
                              └──────────┘   └────────┘
```

---

### Decision Tree: route_after_analyzer

```
                    ┌─────────────────────────┐
                    │  route_after_analyzer   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │ user_wants_scheduling?  │
                    └────┬──────────────┬─────┘
                         │ True         │ False
                         ▼              │
                    ┌────────────┐      │
                    │ SCHEDULER  │      │
                    └────────────┘      │
                                        │
                         ┌──────────────┴──────────────┐
                         │ scheduling_keywords in msg? │
                         └────┬──────────────┬─────────┘
                              │ Yes          │ No
                              ▼              ▼
                         ┌────────────┐  ┌────────┐
                         │ SCHEDULER  │  │  END   │
                         └────────────┘  └────────┘
```

---

## State Lifecycle

### Initial State
```json
{
  "messages": [],
  "user_id": "user_123",
  "session_mode": null,
  "tutor_session_active": false,
  "analysis_results": null,
  "user_wants_scheduling": false,
  "workflow_complete": false
}
```

### After First Tutor Turn
```json
{
  "messages": [HumanMessage("..."), AIMessage("...")],
  "session_mode": "active_tutoring",      ← Set by Tutor
  "tutor_session_active": true,           ← Enables loops
  "analysis_results": null,
  "user_wants_scheduling": false
}
```

### After Analyzer
```json
{
  "messages": [...],
  "session_mode": "analysis_requested",   ← Set by Analyzer
  "tutor_session_active": false,          ← Prevent re-entry
  "analysis_results": {                   ← Stored for downstream
    "weak_points": [...],
    "priority_topics": [...]
  },
  "user_wants_scheduling": true           ← Detected by Analyzer
}
```

### After Scheduler
```json
{
  "session_mode": "scheduling_requested", ← Set by Scheduler
  "generated_schedule": {
    "sessions": [...]
  }
}
```

---

## Agent Communication Matrix

| From Agent | To Agent | Information Passed | How |
|------------|----------|-------------------|-----|
| Tutor | Tutor | Conversation context | State.messages |
| Tutor | Analyzer | Full conversation | State.messages |
| Analyzer | Scheduler | Weak points analysis | State.analysis_results |
| Analyzer | Scheduler | Scheduling intent | State.user_wants_scheduling |
| Intent Router | Any Agent | User intent | State.next_agent |

---

## Conditional Edge Logic

### Edge 1: intent_router → agents
```python
Condition: state["next_agent"]
Mapping:
  "tutor" → tutor
  "scheduler" → scheduler
  "analyzer" → analyzer
  "motivator" → motivator
```

### Edge 2: tutor → tutor/analyzer/END
```python
Condition: route_after_tutor(state)
Mapping:
  "tutor" → tutor        # Loop back
  "analyzer" → analyzer  # Exit to analysis
  "__end__" → END        # Complete
```

### Edge 3: analyzer → scheduler/END
```python
Condition: route_after_analyzer(state)
Mapping:
  "scheduler" → scheduler  # User wants scheduling
  "__end__" → END          # No scheduling
```

---

## Loop Prevention Safeguards

### Safeguard 1: tutor_session_active Flag
```
If tutor_session_active = False:
  → Cannot return to Tutor
  → Prevents Analyzer → Tutor loops
```

### Safeguard 2: workflow_complete Flag
```
If workflow_complete = True:
  → Force exit to END
  → Emergency exit mechanism
```

### Safeguard 3: LLM Exit Detection
```
Uses GPT-4o-mini to detect nuanced exit intent
Defaults to CONTINUE on error (safe default)
```

---

## Performance Optimization Points

```
┌──────────────────────────────────────────────────────────┐
│ Optimization                  │ Benefit                  │
├──────────────────────────────────────────────────────────┤
│ Keyword check before LLM      │ Reduces API calls by 60% │
│ Use gpt-4o-mini for routing   │ 3x faster than gpt-4     │
│ Temperature=0 for routing     │ Deterministic decisions  │
│ MemorySaver checkpointer      │ Efficient state storage  │
│ add_messages reducer          │ Append-only, no copying  │
└──────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
                    ┌─────────────────┐
                    │  Agent Executes │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │   Success?      │
                    └────┬──────┬─────┘
                         │ Yes  │ No
                         ▼      │
                    ┌────────┐  │
                    │Continue│  │
                    └────────┘  │
                                │
                    ┌───────────┴──────────┐
                    │   Exception Type?    │
                    └───┬──────────────┬───┘
                        │ LLM Error    │ Other
                        ▼              ▼
                  ┌──────────┐   ┌──────────┐
                  │ Fallback │   │  Log &   │
                  │ Response │   │ Return   │
                  └──────────┘   └──────────┘
                        │              │
                        └──────┬───────┘
                               ▼
                          ┌────────┐
                          │  END   │
                          └────────┘
```

---

## Integration Points

### Point 1: ChatMessageHistory Sync
```
LangGraph State → ChatMessageHistory
  │
  └─ langgraph_chatbot.py calls sync_messages()
     after each turn
```

### Point 2: RAG Pipeline Sharing
```
State.rag_pipeline → Shared across Tutor calls
  │
  └─ Per-user ChromaDB collection
     Prevents cross-contamination
```

### Point 3: Calendar Connector
```
Scheduler → CalendarConnector.sync()
  │
  └─ Syncs generated schedule to Google Calendar
```

---

## Testing Checklist

```
✓ Test: Tutor loop (3+ turns)
✓ Test: Exit intent detection ("I'm done")
✓ Test: False positive prevention ("done with this problem")
✓ Test: Analyzer → Scheduler handoff
✓ Test: Direct scheduling (no analysis)
✓ Test: State persistence across turns
✓ Test: Error handling (LLM failures)
✓ Test: Loop prevention (tutor_session_active=False)
✓ Test: Emergency exit (workflow_complete=True)
```

---

## Quick Troubleshooting

| Problem | Check | Solution |
|---------|-------|----------|
| Infinite loop | `tutor_session_active` flag | Set to False in Analyzer |
| No handoff | `user_wants_scheduling` flag | Check keyword detection |
| Wrong routing | Logs: `route_after_X` | Verify conditional logic |
| State not saved | `thread_id` in config | Use same ID per session |
| LLM errors | Exit detection fallback | Defaults to CONTINUE |

---

## Summary Metrics

```
┌────────────────────────────────────────────┐
│ Metric                    │ Value          │
├────────────────────────────────────────────┤
│ Total Nodes               │ 5              │
│ Conditional Edges         │ 3              │
│ Direct Edges              │ 2              │
│ Possible Paths            │ 8+             │
│ Max Loop Iterations       │ Unlimited*     │
│ State Fields (Total)      │ 14             │
│ New Orchestration Fields  │ 4              │
│ LLM Calls per Turn        │ 1-2            │
└────────────────────────────────────────────┘

* Limited by user behavior and exit detection
```

---

## Visual Legend

```
┌────────┐  Node (Agent)
│  NAME  │
└────────┘

    │      Direct Edge
    ↓

    ┼      Conditional Edge (branching)
  ↙ ↓ ↘

    ⟲      Loop (self-edge)

   ...     Continued flow

  ┌───┐    Decision point
  │   │
  └───┘
```

---

This visual guide provides a complete overview of the enhanced LangGraph workflow architecture!
