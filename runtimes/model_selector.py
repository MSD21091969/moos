"""Model selector for per-task model switching.

Automatically selects the best model based on task type.
"""
from enum import Enum
from typing import Optional


class TaskType(Enum):
    """Types of tasks for model selection."""
    GENERAL = "general"
    CODE = "code"
    MATH = "math"
    REASONING = "reasoning"
    VISION = "vision"


# Model capabilities mapping
MODEL_CAPABILITIES = {
    "qwen3:14b": {
        "strengths": [TaskType.GENERAL, TaskType.REASONING],
        "context": 41000,
        "description": "Best general reasoning, MMLU 80%",
    },
    "deepseek-r1:14b": {
        "strengths": [TaskType.REASONING, TaskType.MATH],
        "context": 64000,
        "description": "Chain-of-thought, AIME 80%",
    },
    "phi4:14b": {
        "strengths": [TaskType.MATH],
        "context": 16000,
        "description": "Best math, MATH 80%, GPQA 56%",
    },
    "gemma3:12b": {
        "strengths": [TaskType.GENERAL, TaskType.VISION],
        "context": 128000,
        "description": "Vision + long context (128K)",
    },
    "codellama:13b": {
        "strengths": [TaskType.CODE],
        "context": 16000,
        "description": "Pure code specialist",
    },
}

# Default model for each task type
TASK_MODEL_DEFAULTS = {
    TaskType.GENERAL: "qwen3:14b",
    TaskType.CODE: "codellama:13b",
    TaskType.MATH: "phi4:14b",
    TaskType.REASONING: "deepseek-r1:14b",
    TaskType.VISION: "gemma3:12b",
}


def detect_task_type(query: str) -> TaskType:
    """
    Detect task type from query content.
    
    Uses simple keyword matching; could be enhanced with ML.
    """
    query_lower = query.lower()
    
    # Code detection
    code_keywords = [
        "code", "python", "function", "class", "implement",
        "debug", "fix", "refactor", "script", "program",
        "def ", "import ", "async", "await", "compile"
    ]
    if any(kw in query_lower for kw in code_keywords):
        return TaskType.CODE
    
    # Math detection
    math_keywords = [
        "calculate", "math", "equation", "solve", "proof",
        "theorem", "integral", "derivative", "algebra",
        "number", "formula", "compute", "arithmetic"
    ]
    if any(kw in query_lower for kw in math_keywords):
        return TaskType.MATH
    
    # Reasoning detection
    reasoning_keywords = [
        "analyze", "reason", "think", "explain why",
        "step by step", "deduce", "infer", "prove",
        "evaluate", "assess", "compare", "logic"
    ]
    if any(kw in query_lower for kw in reasoning_keywords):
        return TaskType.REASONING
    
    # Vision detection
    vision_keywords = [
        "image", "picture", "photo", "screenshot",
        "visual", "see", "look at", "diagram"
    ]
    if any(kw in query_lower for kw in vision_keywords):
        return TaskType.VISION
    
    return TaskType.GENERAL


def select_model(
    query: str,
    task_type: Optional[TaskType] = None,
    force_model: Optional[str] = None,
) -> str:
    """
    Select the best model for a given query.
    
    Args:
        query: The user's query
        task_type: Override task type (auto-detect if None)
        force_model: Force a specific model
        
    Returns:
        Model name to use
    """
    if force_model:
        return force_model
    
    detected_type = task_type or detect_task_type(query)
    return TASK_MODEL_DEFAULTS.get(detected_type, "qwen3:14b")


def get_model_context(model_name: str) -> int:
    """Get the context window size for a model."""
    if model_name in MODEL_CAPABILITIES:
        return MODEL_CAPABILITIES[model_name]["context"]
    return 8192  # Default


def get_model_info(model_name: str) -> dict:
    """Get full info about a model."""
    return MODEL_CAPABILITIES.get(model_name, {
        "strengths": [TaskType.GENERAL],
        "context": 8192,
        "description": "Unknown model",
    })


def list_available_models() -> list[str]:
    """List all available models."""
    return list(MODEL_CAPABILITIES.keys())
