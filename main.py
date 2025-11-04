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


class DummyStore:
    def add_documents(self, docs):
        print(f"[store] ingesting {len(list(docs))} docs")

    def similarity_search(self, query: str, k: int = 5):
        return [{"content": f"Stub context for {query}"} for _ in range(k)]


def load_quote_store(path: Path) -> QuoteStore:
    store = QuoteStore(path)
    if not path.exists():
        print(f"[quotes] No quote store found at {path}. Run `python -m scripts.load_quotes` to seed data.")
    else:
        print(f"[quotes] Loaded quote store from {path}.")
    return store


if __name__ == "__main__":
    calendar_connector = CalendarConnector()

    quote_store = load_quote_store(Path("data/quotes_store.json"))
    print(quote_store.all)
    
    scheduler = SchedulerAgent(calendar_connector=calendar_connector)
    motivator = MotivatorAgent(
        fetcher=DummyFetcher(),
        quote_store=quote_store,
        llm=OpenAIMotivationModel(),
    )
    tutor = TutorAgent(store=DummyStore())

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
