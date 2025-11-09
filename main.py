"""Entry point for the Study Pal system."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from agents import MotivatorAgent, OpenAIMotivationModel, QuoteStore, SchedulerAgent, TutorAgent
from agents.onboarding import create_onboarding_agent
from agents.tutor_chatbot import ChatInterface, TutorChatbot
from agents.user_profile import UserProfileStore
from core.graph_manager import GraphManager
from core.mcp_connectors import CalendarConnector
from core.rag_pipeline import RAGPipeline


load_dotenv(override=True)


class DummyFetcher:
    def fetch(self, persona: str) -> dict:
        return {"text": f"Keep climbing, {persona}!", "source": "dummy"}


def load_quote_store(path: Path) -> QuoteStore:
    store = QuoteStore(path)
    if not path.exists():
        print(f"[quotes] No quote store found at {path}. Run `python -m scripts.load_quotes` to seed data.")
    else:
        print(f"[quotes] Loaded quote store from {path}.")
    return store


def demo_tutor_agent():
    """Demonstrate TutorAgent capabilities with RAG pipeline."""
    print("\n" + "=" * 60)
    print("🎓 TUTOR AGENT DEMO - RAG-Powered Study Assistant")
    print("=" * 60 + "\n")

    # Initialize RAG pipeline for tutor
    rag_pipeline = RAGPipeline()
    tutor = TutorAgent(rag_pipeline=rag_pipeline)

    # Check if we have the test PDF
    test_pdf = Path("tests/fixtures/calculus_sample.pdf")
    if not test_pdf.exists():
        print("❌ Test PDF not found. Please ensure tests/fixtures/calculus_sample.pdf exists.")
        return

    # 1. Ingest study material
    print("📚 Step 1: Ingesting study material...")
    print(f"   Loading: {test_pdf.name}")
    num_chunks = tutor.ingest_material(test_pdf)
    print(f"   ✓ Successfully ingested {num_chunks} chunks\n")

    # 2. Check materials count
    print(f"📊 Step 2: Knowledge base status")
    total_chunks = tutor.count_materials()
    print(f"   Total chunks in knowledge base: {total_chunks}\n")

    # 3. Retrieve context for a question
    print("🔍 Step 3: Retrieving context for a question...")
    question = "What is a derivative?"
    print(f"   Question: '{question}'")
    context = tutor.get_context(question, k=2)
    print(f"   Retrieved {len(context)} relevant snippets:")
    for i, snippet in enumerate(context, 1):
        print(f"   [{i}] {snippet[:100]}..." if len(snippet) > 100 else f"   [{i}] {snippet}")
    print()

    # 4. Generate a quiz
    print("📝 Step 4: Generating quiz on derivatives...")
    quiz = tutor.generate_quiz("derivatives", num_questions=3)
    print(f"   Generated {len(quiz)} quiz item(s):")
    for i, item in enumerate(quiz, 1):
        print(f"\n   Question {i}:")
        print(f"   Q: {item.question}")
        print(f"   A: {item.answer}")
        print(f"   Difficulty: {item.difficulty}")
    print()

    # 5. Try different topics
    print("🔍 Step 5: Testing context retrieval for different topics...")
    topics = [
        ("integrals", "Tell me about integrals"),
        ("limits", "What are limits in calculus?"),
    ]

    for topic, query in topics:
        print(f"\n   Topic: {topic}")
        print(f"   Query: '{query}'")
        context = tutor.get_context(query, k=1)
        if context:
            preview = context[0][:80] + "..." if len(context[0]) > 80 else context[0]
            print(f"   → {preview}")
        else:
            print(f"   → No context found")

    print("\n" + "=" * 60)
    print("✅ DEMO COMPLETE - TutorAgent successfully demonstrated!")
    print("=" * 60 + "\n")


def demo_full_system():
    """Demonstrate the full Study Pal system with all agents."""
    print("\n" + "=" * 60)
    print("🚀 FULL SYSTEM DEMO - Study Pal Daily Cycle")
    print("=" * 60 + "\n")

    calendar_connector = CalendarConnector()
    quote_store = load_quote_store(Path("data/quotes_store.json"))

    # Initialize all agents
    rag_pipeline = RAGPipeline()
    scheduler = SchedulerAgent(calendar_connector=calendar_connector)
    motivator = MotivatorAgent(
        fetcher=DummyFetcher(),
        quote_store=quote_store,
        llm=OpenAIMotivationModel(),
    )
    tutor = TutorAgent(rag_pipeline=rag_pipeline)

    manager = GraphManager(
        scheduler=scheduler,
        motivator=motivator,
        tutor=tutor,
    )

    result = manager.run_daily_cycle(
        {
            "persona": "Steve Jobs",
            "topic": "neural networks",
            "user_input": "I am free 10-11pm tonight and want to focus on neural networks then review notes.",
        }
    )
    print(result)


def run_onboarding(user_id: str = "default_user"):
    """Run the onboarding flow for a new user."""
    print(f"\n🎯 Starting onboarding for user: {user_id}")

    # Check if profile already exists
    profile_store = UserProfileStore(Path("data/profiles"))
    try:
        existing_profile = profile_store.load(user_id)
        print(f"\n⚠️  Profile already exists for '{user_id}'")
        print(f"   Name: {existing_profile.name}")
        print(f"   Persona: {existing_profile.primary_persona}")

        overwrite = input("\nDo you want to create a new profile? This will overwrite the existing one. (yes/no): ").strip().lower()
        if overwrite not in ["yes", "y"]:
            print("Onboarding cancelled.\n")
            return
    except FileNotFoundError:
        pass  # No existing profile, proceed with onboarding

    # Create and run onboarding agent
    onboarding_agent = create_onboarding_agent()
    try:
        profile = onboarding_agent.run_onboarding(user_id)
        print(f"✅ Profile saved to: data/profiles/{user_id}.json\n")
        return profile
    except KeyboardInterrupt:
        print("\n\n👋 Onboarding interrupted. You can try again anytime.\n")
        return None


def check_and_load_profile(user_id: str = "default_user") -> bool:
    """
    Check if a user profile exists and load it.

    Args:
        user_id: User identifier

    Returns:
        True if profile exists, False otherwise
    """
    profile_store = UserProfileStore(Path("data/profiles"))
    try:
        profile = profile_store.load(user_id)
        print(f"✅ Loaded profile for {profile.name}")
        print(f"   Motivational guide: {profile.primary_persona}")
        if profile.current_focus:
            print(f"   Current focus: {profile.current_focus}")
        return True
    except FileNotFoundError:
        return False


def start_chatbot(user_id: str = "default_user", use_langgraph: bool = True):
    """Start the interactive chatbot."""
    # Check for user profile
    if not check_and_load_profile(user_id):
        print(f"\n⚠️  No profile found for user '{user_id}'")
        print("Let's create one first!\n")
        run_onboarding(user_id)
        print()

    if use_langgraph:
        print("🚀 Starting Study Pal LangGraph Multi-Agent System...")
        print("   All agents (Tutor, Scheduler, Analyzer, Motivator) are ready!\n")

        # Use the new LangGraph chatbot
        from core.langgraph_chatbot import LangGraphChatbot

        chatbot = LangGraphChatbot(user_id=user_id, session_id=user_id)

        # Start chat interface with LangGraph bot
        chat_interface = ChatInterface(chatbot=chatbot)
        chat_interface.run()
    else:
        print("🚀 Starting Study Pal Chatbot (Legacy Mode)...")
        print("   Initializing RAG pipeline and AI tutor...\n")

        # Initialize RAG pipeline and tutor agent
        rag_pipeline = RAGPipeline()
        tutor_agent = TutorAgent(rag_pipeline=rag_pipeline)

        # Create chatbot
        chatbot = TutorChatbot(tutor_agent=tutor_agent)

        # Start chat interface
        chat_interface = ChatInterface(chatbot=chatbot)
        chat_interface.run()


if __name__ == "__main__":
    import sys

    # Get user_id if provided
    user_id = "default_user"
    if len(sys.argv) > 2:
        user_id = sys.argv[2]

    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "--onboard":
            run_onboarding(user_id)
        elif command == "--chat":
            start_chatbot(user_id)
        elif command == "--tutor-demo":
            demo_tutor_agent()
        elif command == "--full":
            demo_full_system()
        else:
            print(f"❌ Unknown command: {command}")
            print("\n📖 Study Pal - Available commands:")
            print("   python main.py --onboard [user_id]   # Create/update user profile")
            print("   python main.py --chat [user_id]      # Start interactive chatbot")
            print("   python main.py --tutor-demo          # Demo TutorAgent with RAG")
            print("   python main.py --full                # Demo full system with all agents")
            print("\n   [user_id] is optional and defaults to 'default_user'")
    else:
        print("\n📖 Study Pal - Available commands:")
        print("   python main.py --onboard [user_id]   # Create/update user profile")
        print("   python main.py --chat [user_id]      # Start interactive chatbot")
        print("   python main.py --tutor-demo          # Demo TutorAgent with RAG")
        print("   python main.py --full                # Demo full system with all agents")
        print("\n   [user_id] is optional and defaults to 'default_user'")
        print("\nDefaulting to chatbot...\n")
        start_chatbot(user_id)
