# IADORE Local Model Setup

**Investigation Date**: 2026-01-16  
**Purpose**: Document local LLM infrastructure for Phase 4.5 experiments

---

## Model Inventory

### 1. Custom Agatha Model

**Name**: `agatha:latest` (Ollama)  
**Base**: `qwen3:14b` (9.3GB)  
**Type**: Custom fine-tuned chat model

**Configuration** (`Modelfile`):

```modelfile
FROM qwen3:14b

SYSTEM """Agatha (Bartos, polish, hairy) - agentic AI detective"""

PARAMETER temperature 0.75
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.2
PARAMETER num_ctx 8192          # 2x default context
PARAMETER num_predict 384        # Max response length
PARAMETER stop "<|im_end|>"
```

**Key Features**:

- ✅ Persona baked into model (no system prompt overhead)
- ✅ 8K context window (2x default)
- ✅ Optimized parameters for conversation
- ✅ Stop sequences to prevent rambling

**Usage**:

```python
# Direct Ollama usage
response = ollama.chat(
    model='agatha',  # Persona already included
    messages=[...]
)
```

---

### 2. BakLLaVA (Vision)

**Name**: `bakllava:latest` (Ollama)  
**Size**: 4.7GB  
**Type**: Multimodal (Vision + Text)

**Local Model Files** (D:\IADORE\models\):

- `ggml-model-q4_k.gguf` (4.3GB) - BakLLaVA Q4_K quantized
- `mmproj-model-f16.gguf` (624MB) - CLIP vision encoder

**Capabilities**:

- Image analysis and description
- OCR (text extraction from images)
- Visual question answering
- Image comparison

**Usage**:

```python
import ollama

response = ollama.chat(
    model='bakllava',
    messages=[{
        'role': 'user',
        'content': 'Describe this image',
        'images': ['path/to/image.jpg']
    }]
)
```

---

### 3. Qwen3:14B (Base)

**Name**: `qwen3:14b`  
**Size**: 9.3GB  
**Type**: General-purpose chat model

Used as the base for the custom `agatha` model.

---

### 4. Gödel Model

**Name**: `godel:latest`  
**Size**: 9.3GB  
**Type**: Custom philosophical agent

(Mentioned in BAKLLAVA_GUIDE.md)

---

## Model Creation Pattern

### Custom Model via Modelfile

**Step 1**: Create `Modelfile` with persona and parameters

```modelfile
FROM base_model:tag

SYSTEM """Your custom system prompt"""

PARAMETER temperature 0.75
PARAMETER num_ctx 8192
# ... other params
```

**Step 2**: Build custom model

```powershell
ollama create agatha -f D:\IADORE\Modelfile
```

**Step 3**: Use in Python

```python
model = OllamaModel("agatha:latest")
```

---

## Integration with pydantic-deep

### Current IADORE Setup (Old)

```python
# agents/agatha.py
from pydantic_ai.models.ollama import OllamaModel

model = OllamaModel("agatha:latest")
agent = DeepAgent(
    user=user,
    model=model,
    toolsets=[...],
)
```

### Pattern for Phase 4.5 Experiments

**Experiment**: Test local models in deepagent-test

```python
# experiments/exp_local_models.py
from pydantic_ai.models.ollama import OllamaModel
from pydantic_deep import create_deep_agent, DeepAgentDeps
from pydantic_ai_backends import StateBackend

# Option 1: Use custom agatha model
agent_agatha = create_deep_agent(
    model="ollama:agatha",  # Custom model with persona
    instructions="",  # Empty - persona is baked in
)

# Option 2: Use base qwen3
agent_qwen = create_deep_agent(
    model="ollama:qwen3:14b",
    instructions="You are a helpful assistant"
)

# Option 3: Use vision model
agent_vision = create_deep_agent(
    model="ollama:bakllava",
    instructions="You are a vision assistant"
)

deps = DeepAgentDeps(backend=StateBackend())
```

---

## Key Insights for Phase 4.5

### 1. **Modelfile Pattern**

- Bake system prompts into custom models
- Optimize parameters per use-case
- Reduce overhead (no system prompt per message)

**Collider Application**: Could create specialized models for different StepNode types:

- `collider-planner:latest` - Graph planning
- `collider-executor:latest` - Code execution
- `collider-reviewer:latest` - Quality checks

### 2. **Local vs Cloud Models**

- Local: Fast, private, no API costs
- Custom models: Consistent persona, optimized parameters
- Vision models: Multimodal capabilities

**Experiment Idea**: Compare local vs cloud performance in exp7

### 3. **Vision Integration**

- BakLLaVA via Ollama API
- 4.7GB model size (acceptable for local)
- Useful for graph visualization analysis

**Collider Application**: Analyze generated graph diagrams, UI screenshots

### 4. **Model Management**

- Hard-linked models (shared across workspaces)
- 4GB+ savings by not duplicating .gguf files
- Centralized model repo pattern

---

## Recommended Experiments

### Experiment 7: Local Model Comparison

```python
# Compare local vs cloud performance
- agatha:latest (custom local)
- qwen3:14b (base local)
- gpt-4o-mini (cloud)

Metrics:
- Latency
- Quality
- Cost
- Context retention
```

### Experiment 8: Vision Toolset

```python
# Create vision toolset using BakLLaVA
@vision_toolset.tool
async def analyze_image(path: str) -> str:
    # Use bakllava via Ollama
    pass
```

---

## Files Referenced

- `D:\IADORE\Modelfile` - Custom agatha model definition
- `D:\IADORE\CUSTOM_MODEL.md` - Model creation guide
- `D:\IADORE\BAKLLAVA_GUIDE.md` - Vision model usage
- `D:\IADORE\models\*.gguf` - Local model weights
- `D:\IADORE\pyproject.toml` - Dependencies (ollama, pydantic-deep)

---

## Next Steps

1. Add local model experiments to Phase 4.5
2. Test custom model creation pattern
3. Benchmark local vs cloud for Collider use-cases
4. Explore vision toolset for graph analysis
