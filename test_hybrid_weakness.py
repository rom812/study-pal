"""Test LLM-based weakness detection with the 'rom' conversation example."""

from langchain_core.messages import AIMessage, HumanMessage

from agents.weakness_detector_agent import WeaknessDetectorAgent


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
    print("Testing LLM-Based Weakness Detection Agent")
    print("=" * 70)
    print("\nConversation:")
    for msg in messages:
        role = "Student" if isinstance(msg, HumanMessage) else "Tutor"
        print(f"{role}: {msg.content}")

    print("\n" + "-" * 70)
    print("Analysis with WeaknessDetectorAgent:")
    print("-" * 70)

    # Test with the agent
    detector = WeaknessDetectorAgent(model="gpt-4o-mini")

    try:
        result = detector.analyze_conversation(
            messages,
            session_topic="Computer Memory Concepts"
        )

        weak_points = result.get("weak_points", [])
        session_summary = result.get("session_summary", "No summary")

        print("\n✅ LLM Analysis Results:")
        print(f"Weak points identified: {len(weak_points)}")

        for idx, wp in enumerate(weak_points, 1):
            print(f"\n  {idx}. Topic: {wp.get('topic')}")
            print(f"     Difficulty: {wp.get('difficulty_level')}")
            print(f"     Evidence: {wp.get('evidence', [])[:1]}")  # Show first evidence
            print(f"     Reasoning: {wp.get('reasoning', 'N/A')}")

        print(f"\n  Session Summary: {session_summary}")

    except Exception as e:
        print(f"❌ LLM Analysis failed: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 70)
    print("Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_rom_conversation()
