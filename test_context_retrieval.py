"""Test what context is being retrieved for the questions."""

from agents.tutor_agent import TutorAgent
from core.rag_pipeline import RAGPipeline

# Create RAG pipeline and tutor
rag_pipeline = RAGPipeline()
tutor = TutorAgent(rag_pipeline=rag_pipeline)

# Test the exact queries from the chat
queries = [
    "tell me about rom",
    "tell me about rom sheynis",
    "what information do u have?"
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")

    context = tutor.get_context(query, k=3)

    if context:
        print(f"✅ Found {len(context)} context chunks:")
        for i, chunk in enumerate(context, 1):
            print(f"\n--- Chunk {i} ---")
            print(chunk[:300])
    else:
        print("❌ No context found!")
