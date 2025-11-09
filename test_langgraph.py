"""
Simple test script to see LangGraph workflow in action.

Run this to test that our multi-agent system works!

Usage:
    python test_langgraph.py
"""

import logging
from dotenv import load_dotenv

# Set up logging so we can see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

# Load environment variables (for OpenAI API key)
load_dotenv()

from core.workflow_graph import run_workflow


def test_tutor_intent():
    """Test that tutoring questions work."""
    print("\n" + "="*70)
    print("TEST 1: Tutoring Question")
    print("="*70)

    print("\n📝 NOTE: This test will show a message about no study materials")
    print("   In a real scenario, you'd ingest PDFs first using /ingest command")

    result = run_workflow(
        user_message="What is a derivative in calculus?",
        user_id="test_user",
        session_id="test_1"
    )

    print("\n📥 USER: What is a derivative in calculus?")
    print(f"🤖 INTENT DETECTED: {result['current_intent']}")
    print(f"📤 ASSISTANT: {result['messages'][-1].content}\n")


def test_scheduler_intent():
    """Test that scheduling requests work."""
    print("\n" + "="*70)
    print("TEST 2: Schedule Creation")
    print("="*70)

    result = run_workflow(
        user_message="I'm free from 2pm to 5pm tomorrow. Can you schedule study time?",
        user_id="test_user",
        session_id="test_2"
    )

    print("\n📥 USER: I'm free from 2pm to 5pm tomorrow. Can you schedule study time?")
    print(f"🤖 INTENT DETECTED: {result['current_intent']}")
    print(f"📤 ASSISTANT: {result['messages'][-1].content}\n")


def test_analyzer_intent():
    """Test that analysis requests work."""
    print("\n" + "="*70)
    print("TEST 3: Session Analysis")
    print("="*70)

    # First, have a short conversation
    session_id = "test_3"

    result1 = run_workflow(
        user_message="What is integration?",
        user_id="test_user",
        session_id=session_id
    )

    result2 = run_workflow(
        user_message="I don't understand limits at all",
        user_id="test_user",
        session_id=session_id
    )

    # Now analyze
    result3 = run_workflow(
        user_message="Can you analyze my weak points?",
        user_id="test_user",
        session_id=session_id
    )

    print("\n📥 USER: Can you analyze my weak points?")
    print(f"🤖 INTENT DETECTED: {result3['current_intent']}")
    print(f"📤 ASSISTANT: {result3['messages'][-1].content}\n")


def test_motivator_intent():
    """Test that motivation requests work."""
    print("\n" + "="*70)
    print("TEST 4: Motivation")
    print("="*70)

    result = run_workflow(
        user_message="I need some motivation to study!",
        user_id="test_user",
        session_id="test_4"
    )

    print("\n📥 USER: I need some motivation to study!")
    print(f"🤖 INTENT DETECTED: {result['current_intent']}")
    print(f"📤 ASSISTANT: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    print("\n" + "🚀 " + "="*66)
    print("  LANGGRAPH MULTI-AGENT WORKFLOW TEST")
    print("="*68 + " 🚀\n")

    print("This will test all 4 agent types:")
    print("  1. Tutor Agent (answers questions)")
    print("  2. Scheduler Agent (creates study plans)")
    print("  3. Analyzer Agent (finds weak points)")
    print("  4. Motivator Agent (provides encouragement)")

    try:
        test_tutor_intent()
        test_scheduler_intent()
        test_analyzer_intent()
        test_motivator_intent()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED!")
        print("="*70 + "\n")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
