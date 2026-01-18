# Experiment 1 Results

**Date**: 2026-01-16  
**Model**: qwen3:14b  
**Status**: ✅ **SUCCESS**

---

## Test Results

### Test 1: Simple Addition ✅

- **Prompt**: "What is 15 + 7?"
- **Result**: Correctly called `add(15, 7)` and returned 22
- **Tool used**: `add` from `math_tools` toolset

### Test 2: Chained Operations ✅

- **Prompt**: "Calculate (5 + 3) multiplied by 2, then raise to the power of 2"
- **Result**: Correctly chained `add(5, 3)` → `multiply(8, 2)` → `power(16, 2)` = 256
- **Tools used**: Multiple tools from toolset

### Test 3: Context-Aware Tool ✅

- **Prompt**: "What's the user's name?"
- **Result**: Called `get_user_name()` and returned "Test User"
- **Tool used**: Standalone tool (not in toolset)

---

## Key Learnings

### ✅ What Worked

1. **Environment Variables**: Setting `OPENAI_BASE_URL` + `OPENAI_API_KEY` works perfectly
2. **Tool Registration**: `@toolset.tool` decorator registers tools correctly
3. **Tool Execution**: Local Ollama model can call Python functions
4. **Multiple Tools**: Can chain multiple tool calls in single request
5. **Mixed Tools**: Can combine toolsets AND standalone tools

### ❌ Critical Finding: Model Compatibility

**CodeLlama:13b does NOT support tool calling**

Error:

```
ModelHTTPError: status_code: 400,
body: 'registry.ollama.ai/library/codellama:13b does not support tools'
```

**Implication**: Need to check which models support tools before assigning to experiments.

---

## Model Recommendations Update

### Tool-Calling Capable (Verified)

- ✅ `qwen3:14b` - Full tool support
- ✅ `gemma3:12b` - Likely supports (Gemini-based)
- ✅ `phi4:14b` - Likely supports (Microsoft)
- ❓ `deepseek-r1:14b` - Need to test

### No Tool Support

- ❌ `codellama:13b` - Confirmed NO tool support
- ❓ `bakllava` - Vision model, uncertain

---

## Next Steps

1. Test other models for tool support
2. Update experiments to use tool-capable models only
3. Reserve codellama for non-tool experiments (Exp 5: Streaming?)
4. Test deepseek-r1 and phi4 tool capabilities
