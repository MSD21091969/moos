# Complete Model Inventory (VERIFIED)

**Date**: 2026-01-16  
**Source**: C:\Users\hp\.ollama\models\manifests\

---

## Installed Models (9 total)

| Model                     | Full Name        | Type       | Size   | Purpose                             |
| ------------------------- | ---------------- | ---------- | ------ | ----------------------------------- |
| `agatha:latest`           | agatha           | Custom     | ~9GB   | Personal assistant (qwen3:14b base) |
| `bakllava:latest`         | bakllava         | Vision     | ~4.7GB | Multimodal (vision + text)          |
| `codellama:13b`           | codellama        | Code       | ~7.3GB | Code generation, completion         |
| `deepseek-r1:14b`         | deepseek-r1      | Reasoning  | ~9GB   | Advanced reasoning, math            |
| `gemma3:12b`              | gemma3           | Multimodal | ~7GB   | Google Gemma 3, vision + text       |
| `godel:latest`            | godel            | Custom     | ~9GB   | Meta-agent (Agent Factory)          |
| `nomic-embed-text:latest` | nomic-embed-text | Embeddings | 274MB  | Text embeddings                     |
| `phi4:14b`                | phi4             | General    | ~9GB   | Microsoft Phi-4 (efficient)         |
| `qwen3:14b`               | qwen3            | General    | ~9GB   | Alibaba Qwen3 (multilingual)        |

**Total Storage**: ~63GB

---

## Specialization Mapping

### Vision / Multimodal

- **bakllava:latest** - Vision + text (LLaVA architecture)
- **gemma3:12b** - Vision + text (Google, 128K context, 140+ languages)

### Code

- **codellama:13b** - Meta's code specialist
- **qwen3:14b** - Also good at code

### Math/Reasoning

- **deepseek-r1:14b** - Best for complex reasoning
- **phi4:14b** - Alternative reasoning model
- **gemma3:12b** - Good at math reasoning

### General

- **qwen3:14b** - Multilingual, balanced
- **gemma3:12b** - Efficient, 128K context
- **phi4:14b** - Microsoft Phi-4
- **agatha:latest** - Custom persona (from IADORE)
- **godel:latest** - Meta-agent persona

### Embeddings

- **nomic-embed-text:latest** - For RAG, semantic search

---

## Experiment Assignments

### Exp 1: Basic Toolsets

- **Model**: `ollama:codellama:13b`

### Exp 2: Skills System

- **Math skill**: `ollama:deepseek-r1:14b`
- **Code skill**: `ollama:codellama:13b`

### Exp 3: Subagent Delegation

- **Coordinator**: `ollama:qwen3:14b`
- **Specialists**:
  - Researcher: `ollama:phi4:14b`
  - Coder: `ollama:codellama:13b`
  - Analyst: `ollama:deepseek-r1:14b`

### Exp 4: File Uploads

- **Model**: `ollama:qwen3:14b`

### Exp 5: Streaming

- **Model**: `ollama:codellama:13b`

### Exp 6: Session Management

- **Model**: `ollama:qwen3:14b`

### Exp 7: Vision (TWO OPTIONS!)

- **Option A**: `ollama:bakllava:latest` (LLaVA-based)
- **Option B**: `ollama:gemma3:12b` (Google, more languages)

---

## Key Insights

### Gemma 3 (12B)

- **Multimodal**: Handles text AND images
- **128K context**: Huge context window
- **140+ languages**: Best multilingual support
- **Efficient**: Good performance/size ratio

### Custom Models

**agatha** - Personal file manager
**godel** - Meta-agent for Collider analysis

Could be useful for Phase 5!

---

## Status

✅ All models confirmed  
✅ Experiments updated  
✅ Ready to run!
