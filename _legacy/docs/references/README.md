# Factory References - README

## Purpose

This directory stores original research materials (PDFs, papers, etc.) for **human reference**.

For **AI agent consumption**, these should be:

1. Read/analyzed by you (human or Gemini)
2. Key findings extracted
3. Condensed markdown summaries created in `knowledge/research/<topic>/`

---

## Current References

### Collider Research

| File                                                                                                    | Topic                      | Summary Location               |
| ------------------------------------------------------------------------------------------------------- | -------------------------- | ------------------------------ |
| [Collider_Research_Plan_v2.pdf](file:///D:/agent-factory/docs/references/Collider_Research_Plan_v2.pdf) | Collider architecture plan | `knowledge/research/collider/` |

### RAG Implementation

| File                                                                                            | Topic                   | Summary Location               |
| ----------------------------------------------------------------------------------------------- | ----------------------- | ------------------------------ |
| [Implementing_PIKE-RAG.pdf](file:///D:/agent-factory/docs/references/Implementing_PIKE-RAG.pdf) | PIKE-RAG implementation | `knowledge/research/pike_rag/` |

### System Design

| File                                                                                                | Topic                            | Summary Location                    |
| --------------------------------------------------------------------------------------------------- | -------------------------------- | ----------------------------------- |
| [Recursive_Orchestration.pdf](file:///D:/agent-factory/docs/references/Recursive_Orchestration.pdf) | Recursive orchestration patterns | `knowledge/research/orchestration/` |

---

## Workflow for New References

### 1. Add PDF Here

```powershell
Copy-Item source.pdf D:\agent-factory\docs\references\Topic_Name.pdf
```

### 2. Extract Key Findings

Read the PDF, identify:

- Core concepts
- Algorithms
- Code patterns
- Implementation strategies

### 3. Create Agent Summary

Create condensed markdown in `knowledge/research/<topic>/`:

````markdown
# Topic Summary (from PDF)

## Key Concepts

- Concept 1
- Concept 2

## Implementation Pattern

```python
# Code example
```
````

## References

- Full PDF: docs/references/Topic_Name.pdf

```

### 4. Update Factory Knowledge Index
Add entry to `docs/INDEX.md` under appropriate section.

---

## Why Keep PDFs?

**For Humans**:
- Full context and citations
- Diagrams and visuals
- Original author's voice
- Complete methodology

**Not for Agents**:
- Can't parse PDFs natively
- Need structured markdown
- Want concise summaries
- Focus on actionable patterns

---

## Next Steps for These Files

**TODO**: Create markdown summaries in:
- `knowledge/research/collider/collider_plan_summary.md`
- `knowledge/research/pike_rag/pike_rag_summary.md`
- `knowledge/research/orchestration/orchestration_summary.md`

Each summary should be:
- Concise (1-2 pages max)
- Code-focused
- Structured for LLM parsing
- Linked back to this PDF for full details
```
