"""Test script for agent-factory with new 8b model."""
import time
from definitions import ColliderAgentDefinition, ModelConfig, ReasoningConfig
from runtimes import AgentRuntime


# Define a test pilot with 8b model
TEST_PILOT = ColliderAgentDefinition(
    name="test-pilot",
    version=1,
    description="Test pilot for benchmarking llama3.1:8b",
    system_prompt="""You are a Collider Pilot - a local AI assistant.
Be concise. Answer in 1-2 sentences when possible.
You have knowledge of the Collider ecosystem.""",
    model=ModelConfig(model_name="llama3.1:8b"),
    reasoning=ReasoningConfig(chain_of_thought=True, max_history=10),
)


def benchmark():
    """Run benchmark test."""
    print("🚀 Testing llama3.1:8b on RTX 3060...")
    print(f"Model: {TEST_PILOT.model.model_name}")
    print("-" * 40)
    
    runtime = AgentRuntime(TEST_PILOT)
    
    prompts = [
        "What is a Container in the Collider?",
        "Explain a LinkedContainer in one sentence.",
        "What does the Fat Runtime do?",
    ]
    
    total_time = 0
    for prompt in prompts:
        print(f"\n📝 {prompt}")
        start = time.time()
        response = runtime.chat(prompt)
        elapsed = time.time() - start
        total_time += elapsed
        print(f"⏱️  {elapsed:.2f}s")
        print(f"💬 {response[:200]}...")
    
    avg = total_time / len(prompts)
    print("\n" + "=" * 40)
    print(f"✅ Average response time: {avg:.2f}s")
    print(f"🎯 Expected: ~2-3s with RTX 3060")


if __name__ == "__main__":
    benchmark()
