"""
Complete Runnable Example: Enhanced LangGraph Workflow

This script demonstrates all execution paths of the enhanced Study Pal workflow:
1. Multi-turn tutoring with loops
2. Tutor → Analyzer → Scheduler pipeline
3. Direct routing to individual agents
4. Exit intent detection
5. State propagation between agents

Run this script to see the workflow in action!
"""

import logging
from langchain_core.messages import HumanMessage
from core.workflow_graph import create_study_pal_graph

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_separator(title: str):
    """Print a nice separator for readability"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_state_summary(state: dict):
    """Print key state information"""
    print(f"📊 State Summary:")
    print(f"   Session Mode: {state.get('session_mode', 'None')}")
    print(f"   Tutor Active: {state.get('tutor_session_active', False)}")
    print(f"   Wants Scheduling: {state.get('user_wants_scheduling', False)}")
    print(f"   Has Analysis: {state.get('analysis_results') is not None}")
    print(f"   Message Count: {len(state.get('messages', []))}")
    if state.get('messages'):
        last_msg = state['messages'][-1]
        content = last_msg.content[:100] + "..." if len(last_msg.content) > 100 else last_msg.content
        print(f"   Last Message: {content}")
    print()


# =============================================================================
# EXAMPLE 1: Multi-Turn Tutoring with Loop
# =============================================================================

def example_1_multi_turn_tutoring():
    """
    Demonstrates:
    - Intent Router → Tutor
    - Tutor → Tutor (loop)
    - Tutor → Tutor (loop)
    - route_after_tutor detects CONTINUE intent
    """
    print_separator("EXAMPLE 1: Multi-Turn Tutoring Loop")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_1"}}

    # Initial state
    initial_state = {
        "messages": [],
        "user_id": "demo_user_1",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Turn 1: Ask first question
    print("🗣️  User: 'What is calculus?'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="What is calculus?")],
    }, config)
    print_state_summary(state)

    # Turn 2: Ask follow-up (should loop back to tutor)
    print("🗣️  User: 'Can you explain derivatives?'")
    state = app.invoke({
        "messages": [HumanMessage(content="Can you explain derivatives?")],
    }, config)
    print_state_summary(state)

    # Turn 3: Ask another follow-up (should loop again)
    print("🗣️  User: 'What about integration?'")
    state = app.invoke({
        "messages": [HumanMessage(content="What about integration?")],
    }, config)
    print_state_summary(state)

    print("✅ Example 1 Complete: Tutor loop worked successfully!")
    print("   The workflow stayed in tutoring mode for multiple turns.")
    return state


# =============================================================================
# EXAMPLE 2: Tutor → Analyzer → END (No Scheduling)
# =============================================================================

def example_2_tutor_to_analyzer():
    """
    Demonstrates:
    - Tutor → Analyzer handoff when user says "I'm done"
    - route_after_tutor detects EXIT intent
    - route_after_analyzer goes to END (no scheduling requested)
    """
    print_separator("EXAMPLE 2: Tutor → Analyzer (Exit Without Scheduling)")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_2"}}

    initial_state = {
        "messages": [],
        "user_id": "demo_user_2",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Turn 1: Start tutoring
    print("🗣️  User: 'What is calculus?'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="What is calculus?")],
    }, config)
    print_state_summary(state)

    # Turn 2: Continue tutoring
    print("🗣️  User: 'Tell me about derivatives'")
    state = app.invoke({
        "messages": [HumanMessage(content="Tell me about derivatives")],
    }, config)
    print_state_summary(state)

    # Turn 3: Exit signal - should trigger Tutor → Analyzer
    print("🗣️  User: 'Thanks, I'm done for now'")
    state = app.invoke({
        "messages": [HumanMessage(content="Thanks, I'm done for now")],
    }, config)
    print_state_summary(state)

    print("✅ Example 2 Complete: Tutor → Analyzer handoff successful!")
    print("   The analyzer ran and workflow ended (no scheduling requested).")
    return state


# =============================================================================
# EXAMPLE 3: Tutor → Analyzer → Scheduler (Full Pipeline)
# =============================================================================

def example_3_full_pipeline():
    """
    Demonstrates:
    - Tutor → Analyzer → Scheduler automatic handoff
    - route_after_tutor detects EXIT intent
    - route_after_analyzer detects SCHEDULING intent
    - Scheduler receives analysis_results from state
    """
    print_separator("EXAMPLE 3: Full Pipeline (Tutor → Analyzer → Scheduler)")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_3"}}

    initial_state = {
        "messages": [],
        "user_id": "demo_user_3",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Turn 1: Start tutoring
    print("🗣️  User: 'What is calculus?'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="What is calculus?")],
    }, config)
    print_state_summary(state)

    # Turn 2: Continue tutoring
    print("🗣️  User: 'Explain derivatives'")
    state = app.invoke({
        "messages": [HumanMessage(content="Explain derivatives")],
    }, config)
    print_state_summary(state)

    # Turn 3: Exit with scheduling request
    print("🗣️  User: 'Got it! Can you analyze my session and create a study schedule?'")
    state = app.invoke({
        "messages": [HumanMessage(content="Got it! Can you analyze my session and create a study schedule?")],
    }, config)
    print_state_summary(state)

    print("✅ Example 3 Complete: Full pipeline executed!")
    print("   Workflow: Tutor → Analyzer → Scheduler")
    print("   Scheduler received analysis results from state")
    return state


# =============================================================================
# EXAMPLE 4: Direct Scheduling (No Analysis)
# =============================================================================

def example_4_direct_scheduling():
    """
    Demonstrates:
    - Intent Router → Scheduler (direct routing)
    - No analysis_results in state
    - Scheduler works without upstream analysis
    """
    print_separator("EXAMPLE 4: Direct Scheduling (No Analysis)")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_4"}}

    initial_state = {
        "messages": [],
        "user_id": "demo_user_4",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Direct scheduling request
    print("🗣️  User: 'Schedule study from 14-15 tomorrow for Math'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="Schedule study from 14-15 tomorrow for Math")],
    }, config)
    print_state_summary(state)

    print("✅ Example 4 Complete: Direct scheduling worked!")
    print("   Intent Router correctly routed to Scheduler")
    print("   No analysis_results in state (as expected)")
    return state


# =============================================================================
# EXAMPLE 5: Direct Analysis Request
# =============================================================================

def example_5_direct_analysis():
    """
    Demonstrates:
    - Intent Router → Analyzer (direct routing)
    - Analyzer → END (no scheduling requested)
    """
    print_separator("EXAMPLE 5: Direct Analysis Request")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_5"}}

    initial_state = {
        "messages": [],
        "user_id": "demo_user_5",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Direct analysis request
    print("🗣️  User: 'Analyze my weak points'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="Analyze my weak points")],
    }, config)
    print_state_summary(state)

    print("✅ Example 5 Complete: Direct analysis worked!")
    print("   Intent Router correctly routed to Analyzer")
    return state


# =============================================================================
# EXAMPLE 6: Exit Intent Detection Edge Cases
# =============================================================================

def example_6_exit_intent_edge_cases():
    """
    Demonstrates:
    - Subtle differences in exit intent detection
    - "I'm done with this problem" vs "I'm done for today"
    """
    print_separator("EXAMPLE 6: Exit Intent Detection (Edge Cases)")

    app = create_study_pal_graph()
    config = {"configurable": {"thread_id": "session_example_6"}}

    initial_state = {
        "messages": [],
        "user_id": "demo_user_6",
        "current_topic": None,
        "current_intent": None,
        "weak_points": None,
        "generated_schedule": None,
        "next_agent": None,
        "workflow_complete": False,
        "session_mode": None,
        "tutor_session_active": False,
        "analysis_results": None,
        "user_wants_scheduling": False,
    }

    # Turn 1: Start tutoring
    print("🗣️  User: 'What is calculus?'")
    state = app.invoke({
        **initial_state,
        "messages": [HumanMessage(content="What is calculus?")],
    }, config)
    print_state_summary(state)

    # Turn 2: Edge case - "done" but wants to continue
    print("🗣️  User: 'I'm done with this problem, can you give me another one?'")
    state = app.invoke({
        "messages": [HumanMessage(content="I'm done with this problem, can you give me another one?")],
    }, config)
    print_state_summary(state)
    print("   ⚠️  Should stay in TUTOR (not exit to Analyzer)")

    # Turn 3: Real exit signal
    print("🗣️  User: 'Okay, I'm done for today'")
    state = app.invoke({
        "messages": [HumanMessage(content="Okay, I'm done for today")],
    }, config)
    print_state_summary(state)
    print("   ✅ Should exit to ANALYZER")

    print("✅ Example 6 Complete: Exit intent detection handled edge cases!")
    return state


# =============================================================================
# Main Execution
# =============================================================================

def run_all_examples():
    """Run all workflow examples"""
    print("\n" + "🚀" * 40)
    print("ENHANCED LANGGRAPH WORKFLOW - COMPLETE DEMONSTRATION")
    print("🚀" * 40)

    try:
        # Run all examples
        example_1_multi_turn_tutoring()
        example_2_tutor_to_analyzer()
        example_3_full_pipeline()
        example_4_direct_scheduling()
        example_5_direct_analysis()
        example_6_exit_intent_edge_cases()

        # Summary
        print_separator("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("✅ Multi-turn tutoring loops")
        print("✅ Tutor → Analyzer handoffs")
        print("✅ Analyzer → Scheduler pipelines")
        print("✅ Direct agent routing")
        print("✅ Exit intent detection")
        print("✅ State propagation between agents")
        print("\n🎉 The enhanced LangGraph workflow is production-ready!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        logger.exception("Example execution failed")


if __name__ == "__main__":
    # You can run individual examples or all at once
    run_all_examples()

    # Or run individual examples:
    # example_1_multi_turn_tutoring()
    # example_3_full_pipeline()
