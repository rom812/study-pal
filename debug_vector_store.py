"""Debug script to check vector store contents."""

from core.rag_pipeline import RAGPipeline

# Create pipeline
pipeline = RAGPipeline()

# Check document count
count = pipeline.count_documents()
print(f"\n📊 Documents in vector store: {count}")

# Try a test query
if count > 0:
    print("\n🔍 Testing query: 'rom'")
    results = pipeline.run_query("rom", k=3)
    print(f"   Found {len(results)} results")

    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   {result[:200]}...")

    print("\n🔍 Testing query: 'rom sheynis'")
    results = pipeline.run_query("rom sheynis", k=3)
    print(f"   Found {len(results)} results")

    for i, result in enumerate(results, 1):
        print(f"\n   Result {i}:")
        print(f"   {result[:200]}...")

    # Test with scores to see similarity
    print("\n🔍 Testing query with scores: 'information'")
    results_with_scores = pipeline.run_query_with_scores("information", k=5)
    print(f"   Found {len(results_with_scores)} results")

    for i, (result, score) in enumerate(results_with_scores, 1):
        print(f"\n   Result {i} (score: {score:.4f}):")
        print(f"   {result[:150]}...")
else:
    print("\n⚠️  No documents in vector store!")
