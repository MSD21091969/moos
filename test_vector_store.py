"""Test GPU vector store."""
import time
from runtimes import VectorStore


def test_vector_store():
    print("🚀 Testing VectorStore on RTX 3060...")
    
    # Create store
    store = VectorStore(use_gpu=True)
    print(f"Store: {store}")
    print(f"GPU enabled: {store.gpu_enabled}")
    
    # Add some documents
    docs = [
        "A Container is a fundamental unit in the Collider ecosystem.",
        "LinkedContainer combines a Link, EastContainer, and Definition.",
        "The Fat Runtime compiles and executes user definitions.",
        "Pydantic v2 is used for all data models in the Collider.",
        "The Graph Safety system prevents cycles and deadlocks.",
    ]
    
    print(f"\n📝 Adding {len(docs)} documents...")
    start = time.time()
    store.add_batch(docs)
    add_time = time.time() - start
    print(f"⏱️  Add time: {add_time:.2f}s")
    
    # Search
    query = "What is a LinkedContainer?"
    print(f"\n🔍 Searching: '{query}'")
    start = time.time()
    results = store.search(query, k=3)
    search_time = time.time() - start
    print(f"⏱️  Search time: {search_time:.4f}s")
    
    print("\n📊 Results:")
    for doc, dist, meta in results:
        print(f"  [{dist:.3f}] {doc[:60]}...")
    
    print(f"\n✅ VectorStore test complete!")
    print(f"   GPU: {store.gpu_enabled}")
    print(f"   Docs: {store.count}")


if __name__ == "__main__":
    test_vector_store()
