"""
LangGraph Workflow - The Complete Multi-Agent System.

This is where we build the graph (flowchart) that connects all our agents.

Think of it like designing a flowchart:
1. Add boxes (nodes) for each agent
2. Draw arrows (edges) showing how to go from one box to another
3. Define rules for which arrow to follow (conditional edges)

Visual representation:
                    START
                      ↓
              [Intent Router] ← Figures out what user wants
                      ↓
        ┌─────────────┼─────────────┐
        ↓             ↓             ↓
    [Tutor]     [Scheduler]   [Analyzer]
        ↓             ↓             ↓
                    END
"""

import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from core.workflow_state import StudyPalState
from core.workflow_nodes import (
    intent_router_node,
    tutor_agent_node,
    scheduler_agent_node,
    analyzer_agent_node,
    motivator_agent_node,
    route_after_scheduler,
    route_after_tutor,
    route_after_analyzer,
)

logger = logging.getLogger(__name__)


def create_study_pal_graph():
    """
    Build the LangGraph workflow connecting all agents.

    This function creates the complete flowchart for how agents work together.

    Returns:
        Compiled LangGraph application ready to run

    Graph Structure:
        1. START → Intent Router (figures out what user wants)
        2. Intent Router → Routes to correct agent (tutor/scheduler/analyzer/motivator)
        3. Agent does work → END

    Example:
        User: "What is calculus?"
        Flow: START → Intent Router (detects "tutor") → Tutor → END
    """
    logger.info("🏗️  Building LangGraph workflow...")

    # Step 1: Create the graph builder with our state type
    # StateGraph is like a flowchart template - we define the structure
    graph_builder = StateGraph(StudyPalState)

    # Step 2: Add nodes (the boxes in our flowchart)
    # Each node is a worker that does a specific job
    logger.info("   Adding nodes...")
    graph_builder.add_node("intent_router", intent_router_node)
    graph_builder.add_node("tutor", tutor_agent_node)
    graph_builder.add_node("scheduler", scheduler_agent_node)
    graph_builder.add_node("analyzer", analyzer_agent_node)
    graph_builder.add_node("motivator", motivator_agent_node)

    # Step 3: Set the entry point (where to start)
    # Every workflow starts at the intent router
    logger.info("   Setting entry point to intent_router...")
    graph_builder.set_entry_point("intent_router")

    # Step 4: Add conditional edges (smart arrows that choose where to go)
    # After intent router, go to the agent it chose
    logger.info("   Adding conditional edges...")

    def route_after_intent(state: StudyPalState) -> str:
        """
        Decide where to go after intent router.

        This function looks at what the intent router decided and
        routes to the appropriate agent.

        Returns:
            Name of the next node to visit
        """
        next_node = state.get("next_agent") or "__end__"
        valid_targets = {"tutor", "scheduler", "analyzer", "motivator"}

        if next_node not in valid_targets:
            logger.info(f"      Routing to: END (next_agent={next_node})")
            return "__end__"

        logger.info(f"      Routing to: {next_node}")
        return next_node

    # Add the conditional edge: from intent_router, decide where to go
    graph_builder.add_conditional_edges(
        "intent_router",
        route_after_intent,
        {
            "tutor": "tutor",
            "scheduler": "scheduler",
            "analyzer": "analyzer",
            "motivator": "motivator",
            "__end__": END,
        },
    )

    # Step 5: Add orchestration edges between agents
    logger.info("   Adding routing edges...")
    graph_builder.add_conditional_edges(
        "scheduler",
        route_after_scheduler,
        {
            "tutor": "tutor",
            "motivator": "motivator",
            "__end__": END,
        },
    )

    graph_builder.add_conditional_edges(
        "tutor",
        route_after_tutor,
        {
            "analyzer": "analyzer",
            "__end__": END,
        },
    )

    graph_builder.add_conditional_edges(
        "analyzer",
        route_after_analyzer,
        {
            "scheduler": "scheduler",
            "motivator": "motivator",
            "__end__": END,
        },
    )

    graph_builder.add_edge("motivator", END)

    # Step 6: Add memory so conversations are remembered
    # MemorySaver lets us have persistent conversations across multiple turns
    memory = MemorySaver()

    # Step 7: Compile the graph into a runnable application
    logger.info("   Compiling graph...")
    app = graph_builder.compile(checkpointer=memory)

    logger.info("✅ LangGraph workflow built successfully!")
    return app


# =============================================================================
# Helper function to run the graph
# =============================================================================

def run_workflow(user_message: str, user_id: str = "default_user", session_id: str = "default") -> dict:
    """
    Run a single message through the workflow.

    This is a simple helper function to make it easy to use the graph.

    Args:
        user_message: What the user said
        user_id: User identifier
        session_id: Conversation session ID (for memory)

    Returns:
        The final state after all agents have run

    Example:
        >>> result = run_workflow("What is a derivative?")
        >>> print(result["messages"][-1].content)
        "A derivative measures the rate of change..."
    """
    from langchain_core.messages import HumanMessage

    # Create the graph
    app = create_study_pal_graph()

    # Build initial state
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "schedule_plan": None,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "session_analysis": None,
        "user_wants_scheduling": False,
        "needs_motivation": False,
        "start_tutor_after_schedule": False,
        "ready_for_tutoring": False,
        "tutor_exit_requested": False,
        "rag_pipeline": None,
        "user_profile": None,
        "awaiting_schedule_confirmation": False,
        "awaiting_schedule_details": False,
        "pending_schedule_request": None,
    }

    # Configuration for memory (so it remembers this conversation)
    config = {"configurable": {"thread_id": session_id}}

    # Run the workflow!
    logger.info(f"🚀 Running workflow for message: {user_message[:50]}...")
    final_state = app.invoke(initial_state, config)

    logger.info("✅ Workflow completed!")
    return final_state


def stream_workflow(user_message: str, user_id: str = "default_user", session_id: str = "default"):
    """
    Stream the workflow execution step by step.

    This is useful if you want to see what's happening in real-time.
    Each yield gives you updates as nodes finish their work.

    Args:
        user_message: What the user said
        user_id: User identifier
        session_id: Conversation session ID

    Yields:
        Updates after each node completes

    Example:
        >>> for update in stream_workflow("Explain calculus"):
        >>>     print(f"Update: {update}")
    """
    from langchain_core.messages import HumanMessage

    app = create_study_pal_graph()

    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "user_id": user_id,
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "schedule_plan": None,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "session_analysis": None,
        "user_wants_scheduling": False,
        "needs_motivation": False,
        "start_tutor_after_schedule": False,
        "ready_for_tutoring": False,
        "tutor_exit_requested": False,
        "rag_pipeline": None,
        "user_profile": None,
        "awaiting_schedule_confirmation": False,
        "awaiting_schedule_details": False,
        "pending_schedule_request": None,
    }

    config = {"configurable": {"thread_id": session_id}}

    logger.info(f"🚀 Streaming workflow for message: {user_message[:50]}...")

    # Stream returns updates as each node completes
    for update in app.stream(initial_state, config):
        logger.info(f"   Update from: {list(update.keys())}")
        yield update

    logger.info("✅ Workflow stream completed!")
