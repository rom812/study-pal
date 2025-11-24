"""
Test script for LLM-based intent router.

This script tests the new LLM intent classification with various user inputs
to ensure it handles synonyms, paraphrasing, and edge cases correctly.
"""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_core.messages import HumanMessage, AIMessage
from core.workflow_nodes import classify_intent_with_llm


def test_intent_classification():
    """Test the LLM intent classifier with diverse inputs."""

    test_cases = [
        # Tutor intent - various phrasings
        ("What is a derivative?", "tutor"),
        ("Can you explain photosynthesis to me?", "tutor"),
        ("Help me understand recursion", "tutor"),
        ("Break down this concept for me", "tutor"),
        ("I don't get this", "tutor"),
        ("Quiz me on calculus", "tutor"),
        ("Can you walk me through this problem?", "tutor"),
        ("Teach me about quantum mechanics", "tutor"),
        ("I need help with math", "tutor"),

        # Scheduler intent - various phrasings
        ("Schedule a study session for tomorrow", "scheduler"),
        ("I'm free from 2-4pm today", "scheduler"),
        ("Create a Pomodoro plan for me", "scheduler"),
        ("When should I study next?", "scheduler"),
        ("Help me plan my study time", "scheduler"),
        ("Block out time for studying", "scheduler"),
        ("I want to schedule sessions", "scheduler"),

        # Analyzer intent - various phrasings
        ("Analyze my session", "analyzer"),
        ("What are my weak points?", "analyzer"),
        ("Give me a summary of what we covered", "analyzer"),
        ("How am I doing?", "analyzer"),
        ("What should I focus on?", "analyzer"),
        ("Recap my progress", "analyzer"),
        ("Show me my trouble areas", "analyzer"),
        ("I want to see a review of my session", "analyzer"),

        # Motivator intent - various phrasings
        ("I need motivation", "motivator"),
        ("Give me a pep talk", "motivator"),
        ("Encourage me to study", "motivator"),
        ("Hype me up!", "motivator"),
        ("I'm feeling discouraged", "motivator"),
        ("Inspire me", "motivator"),
        ("I need some encouragement", "motivator"),

        # Edge cases
        ("hello", "tutor"),  # Greeting - should default to tutor
        ("thanks", "tutor"),  # Gratitude - should default to tutor
    ]

    print("🧪 Testing LLM Intent Router\n")
    print("=" * 80)

    passed = 0
    failed = 0
    errors = 0

    for user_input, expected_intent in test_cases:
        try:
            # Test with empty conversation history for simplicity
            detected_intent = classify_intent_with_llm(user_input, [])

            # Check if the detected intent matches expected
            if detected_intent == expected_intent:
                status = "✅ PASS"
                passed += 1
            else:
                status = f"❌ FAIL (expected: {expected_intent}, got: {detected_intent})"
                failed += 1

            print(f"{status:20} | {user_input[:50]:50} → {detected_intent}")

        except Exception as e:
            status = f"⚠️  ERROR: {str(e)[:30]}"
            errors += 1
            print(f"{status:20} | {user_input[:50]:50}")

    print("=" * 80)
    print(f"\n📊 Results: {passed} passed, {failed} failed, {errors} errors")
    print(f"   Success rate: {passed / len(test_cases) * 100:.1f}%")

    if failed > 0:
        print("\n⚠️  Some tests failed. This may be due to LLM interpretation differences.")
        print("   Review the results to ensure the classifications are semantically reasonable.")

    return passed, failed, errors


def test_with_conversation_context():
    """Test intent classification with conversation history."""

    print("\n\n🧪 Testing with Conversation Context\n")
    print("=" * 80)

    # Simulate a tutoring conversation
    conversation = [
        HumanMessage(content="What is a derivative?"),
        AIMessage(content="A derivative measures the rate of change..."),
        HumanMessage(content="Can you give me another example?"),
        AIMessage(content="Sure! Let's look at velocity..."),
    ]

    test_cases_with_context = [
        ("I'm done for today", "analyzer", "User wants to finish tutoring"),
        ("That's all I needed", "analyzer", "User is satisfied and wants to end"),
        ("What about integrals?", "tutor", "User wants to continue learning"),
    ]

    for user_input, expected_intent, description in test_cases_with_context:
        try:
            detected_intent = classify_intent_with_llm(user_input, conversation)

            if detected_intent == expected_intent:
                status = "✅ PASS"
            else:
                status = f"❌ FAIL (expected: {expected_intent}, got: {detected_intent})"

            print(f"{status:20} | {user_input:30} → {detected_intent:10} | {description}")

        except Exception as e:
            print(f"⚠️  ERROR: {str(e):30} | {user_input:30}")

    print("=" * 80)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("LLM-Based Intent Router Test Suite")
    print("=" * 80 + "\n")

    # Run basic tests
    passed, failed, errors = test_intent_classification()

    # Run context-aware tests
    test_with_conversation_context()

    print("\n✅ Testing complete!\n")

    # Exit with appropriate code
    if errors > 0:
        sys.exit(2)  # Errors occurred
    elif failed > 0:
        sys.exit(1)  # Tests failed
    else:
        sys.exit(0)  # All tests passed
