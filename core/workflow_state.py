"""
Workflow State for LangGraph Multi-Agent System.

This module defines the shared state that all agents use to communicate.
Think of it as a shared notebook where agents write their results and read what others wrote.
"""

from typing import Annotated, Optional, Any, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class StudyPalState(TypedDict):
    """
    Shared state for the Study Pal workflow.

    This is like a shared notebook that all agents can read and write to.
    Each field represents a piece of information that agents might need.

    Key Concepts:
    - TypedDict: A dictionary with specific fields (like a form with labeled boxes)
    - Annotated: Special instructions for how to handle updates
    - add_messages: Automatically adds new messages to the list (doesn't replace them)

    Example:
        # Starting state
        state = {
            "messages": [],
            "user_id": "alice",
            "current_topic": None
        }

        # After tutor agent runs
        state = {
            "messages": [HumanMessage("What is calculus?"), AIMessage("Calculus is...")],
            "user_id": "alice",
            "current_topic": "calculus"
        }
    """

    # Conversation history - special handling to ADD messages, not replace them
    # The 'add_messages' reducer means: "when updating, add to the list, don't replace it"
    messages: Annotated[list[BaseMessage], add_messages]

    # User information
    user_id: str

    # Current conversation context
    current_topic: Optional[str]
    current_intent: Optional[str]  # "tutor", "schedule", "analyze", "motivate"

    # Analysis results from tutor sessions
    weak_points: Optional[Any]  # Results from weakness analysis

    # Schedule information
    generated_schedule: Optional[dict]  # Generated study schedule
    schedule_plan: Optional[dict]  # Detailed plan for current/next session

    # Control flow - tells the graph where to go next
    next_agent: Optional[str]  # Which agent should run next
    workflow_complete: bool  # Should we stop the workflow?

    # === NEW: Multi-agent orchestration fields ===
    # Tracks the current mode of the workflow for sophisticated routing
    session_mode: Optional[
        Literal[
            "scheduling_requested",
            "scheduled",
            "active_tutoring",
            "analysis_requested",
            "analysis_completed",
            "motivation_requested",
            "complete",
        ]
    ]

    # Indicates if the user is actively in a tutoring loop (enables Tutor → Tutor loops)
    tutor_session_active: bool

    # Stores analyzer output so the scheduler can reference it (enables Analyzer → Scheduler handoff)
    analysis_results: Optional[Any]
    session_analysis: Optional[Any]

    # Flag indicating user wants scheduling after analysis (enables conditional Analyzer → Scheduler)
    user_wants_scheduling: bool

    # Flag indicating the user (or system) wants a motivational message
    needs_motivation: bool

    # Indicates if scheduler should hand off immediately into tutoring
    start_tutor_after_schedule: bool
    ready_for_tutoring: bool

    # Tracks whether the user signaled an exit from tutoring during the current turn
    tutor_exit_requested: bool

    # Scheduling follow-up flags
    awaiting_schedule_confirmation: bool  # Analyzer asked if user wants another session
    awaiting_schedule_details: bool  # Scheduler requested specific availability
    pending_schedule_request: Optional[str]  # Raw user text describing desired timing

    # Shared resources - persist across agents
    rag_pipeline: Optional[Any]  # Shared RAG pipeline instance

    # Optional profile/context info used by motivator
    user_profile: Optional[dict]
