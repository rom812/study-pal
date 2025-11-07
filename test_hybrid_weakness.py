"""Test hybrid weakness detection with the 'rom' conversation example."""

from langchain_core.messages import AIMessage, HumanMessage

from core.weakness_analyzer import WeaknessAnalyzer


def test_rom_conversation():
    """Test the conversation that previously failed (identified 'again' and 'simpler' instead of 'rom')."""

    # Simulate the conversation from the user's test
    messages = [
        HumanMessage(content="tell me about rom"),
        AIMessage(content="ROM stands for Read-Only Memory. It's a type of computer memory that permanently stores data and cannot be easily modified..."),
        HumanMessage(content="tell me again about rom but simpler"),
        AIMessage(content="ROM is like a book that can only be read, not written in. The computer can look at what's in it, but can't change it..."),
        HumanMessage(content="simpler"),
        AIMessage(content="ROM = permanent storage that computer reads but cannot change."),
    ]

    print("=" * 70)
    print("Testing Hybrid Weakness Detection")
    print("=" * 70)
    print("\nConversation:")
    for msg in messages:
        role = "Student" if isinstance(msg, HumanMessage) else "Tutor"
        print(f"{role}: {msg.content}")

    print("\n" + "-" * 70)
    print("Analysis with LLM enabled (hybrid approach):")
    print("-" * 70)

    # Test with LLM enabled (hybrid)
    analyzer_llm = WeaknessAnalyzer(
        min_frequency=2,
        min_confusion_signals=1,
        use_llm=True,
        llm_model="gpt-4o-mini"
    )

    try:
        recommendations_llm = analyzer_llm.analyze_conversation(
            messages,
            session_topic="Computer Memory Concepts"
        )

        print("\n✅ LLM Analysis Results:")
        print(f"Weak points identified: {len(recommendations_llm.weak_points)}")
        for wp in recommendations_llm.weak_points:
            print(f"\n  Topic: {wp.topic}")
            print(f"  Difficulty: {wp.difficulty_level}")
            print(f"  Evidence: {wp.evidence[:1]}")  # Show first evidence
            print(f"  Confusion indicators: {wp.confusion_indicators}")

        print(f"\n  Session Summary: {recommendations_llm.session_summary}")
        print(f"\n  Priority topics: {recommendations_llm.priority_topics}")

    except Exception as e:
        print(f"❌ LLM Analysis failed: {e}")

    print("\n" + "-" * 70)
    print("Analysis with LLM disabled (rule-based only):")
    print("-" * 70)

    # Test with LLM disabled (rule-based fallback)
    analyzer_rules = WeaknessAnalyzer(
        min_frequency=2,
        min_confusion_signals=1,
        use_llm=False
    )

    recommendations_rules = analyzer_rules.analyze_conversation(
        messages,
        session_topic="Computer Memory Concepts"
    )

    print("\n✅ Rule-based Analysis Results:")
    print(f"Weak points identified: {len(recommendations_rules.weak_points)}")
    for wp in recommendations_rules.weak_points:
        print(f"\n  Topic: {wp.topic}")
        print(f"  Difficulty: {wp.difficulty_level}")
        print(f"  Evidence: {wp.evidence[:1]}")
        print(f"  Confusion indicators: {wp.confusion_indicators}")

    print(f"\n  Session Summary: {recommendations_rules.session_summary}")
    print(f"\n  Priority topics: {recommendations_rules.priority_topics}")

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_rom_conversation()
