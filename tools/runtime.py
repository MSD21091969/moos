"""Runtime evaluation and benchmarking tools."""
import time
from typing import Optional


def benchmark_runtime(prompt: str = "Hello", iterations: int = 3, **kwargs) -> str:
    """Benchmark the current runtime performance.
    
    Args:
        prompt: Test prompt to use
        iterations: Number of iterations
        
    Returns:
        Benchmark results
    """
    from runtimes import AgentRuntime
    from definitions import ColliderAgentDefinition, ModelConfig
    
    # Minimal test definition
    test_def = ColliderAgentDefinition(
        name="benchmark-test",
        system_prompt="Reply with 'OK' only.",
        model=ModelConfig(model_name="llama3.1:8b"),
    )
    
    runtime = AgentRuntime(test_def)
    
    times = []
    for i in range(iterations):
        start = time.time()
        response = runtime.chat(prompt)
        elapsed = time.time() - start
        times.append(elapsed)
    
    avg = sum(times) / len(times)
    min_t = min(times)
    max_t = max(times)
    
    return f"""## Runtime Benchmark

**Model**: {test_def.model.model_name}
**Iterations**: {iterations}
**Prompt**: "{prompt}"

### Results:
| Metric | Value |
|--------|-------|
| Average | {avg:.2f}s |
| Min | {min_t:.2f}s |
| Max | {max_t:.2f}s |

### Performance Grade:
{_grade_performance(avg)}
"""


def _grade_performance(avg_seconds: float) -> str:
    """Grade performance based on average response time."""
    if avg_seconds < 2:
        return "🟢 **Excellent** (<2s)"
    elif avg_seconds < 5:
        return "🟡 **Good** (2-5s)"
    elif avg_seconds < 10:
        return "🟠 **Acceptable** (5-10s)"
    else:
        return "🔴 **Needs Improvement** (>10s)"


def improve_runtime(issue: Optional[str] = None, **kwargs) -> str:
    """Suggest runtime improvements.
    
    Args:
        issue: Specific issue to address
        
    Returns:
        Improvement suggestions
    """
    suggestions = [
        "**Model Optimization**:",
        "- Use smaller model for simple tasks (llama3.2:3b)",
        "- Use larger model for complex reasoning (llama3.1:13b)",
        "",
        "**GPU Utilization**:",
        "- Ensure Ollama is using GPU: `nvidia-smi`",
        "- Keep model loaded: `ollama run llama3.1:8b` in background",
        "",
        "**RAG Optimization**:",
        "- Use VectorStore with FAISS for fast retrieval",
        "- Pre-compute embeddings for knowledge base",
        "",
        "**Caching**:",
        "- Cache frequent queries",
        "- Use conversation history efficiently",
    ]
    
    return f"""## Runtime Improvement Suggestions

{chr(10).join(suggestions)}
"""
