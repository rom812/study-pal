"""Entry point for the Study Pal system."""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from agents import MotivatorAgent, OpenAIMotivationModel, QuoteStore, SchedulerAgent, TutorAgent
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


if __name__ == "__main__":
    import sys

    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--tutor-demo":
        demo_tutor_agent()
    elif len(sys.argv) > 1 and sys.argv[1] == "--full":
        demo_full_system()
    else:
        print("\n📖 Study Pal - Available demos:")
        print("   python main.py --tutor-demo   # Demo TutorAgent with RAG")
        print("   python main.py --full         # Demo full system with all agents")
        print("\nDefaulting to TutorAgent demo...\n")
        demo_tutor_agent()
