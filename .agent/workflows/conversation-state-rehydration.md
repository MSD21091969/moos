---
description: mo:os Context Rehydration & Knowledge Synchronization
---

# mo:os Context Rehydration & Knowledge Synchronization

Use this workflow at the start of every session (or when context is lost) to rehydrate the agent with the core theoretical framework and current execution state of the mo:os project.

## 1. Establish Foundational Awareness

Before executing any technical tasks, the agent MUST understand the categorical underpinnings of mo:os.

- Read `D:\FFS0_Factory\.agent\knowledge\MANIFESTO.md` for the core philosophy (Category Theory, Data Sovereignty, Harness Agnosticism).
- Read `D:\FFS0_Factory\.agent\knowledge\languagues\abstract_os_language.md` to map the architecture (Kernel = VM, Graph = AST, LLM = Fuzzy FPU).

## 2. Locate the Execution State (The Living Roadmap)

The project is divided into 5 parallel branches.

- Read `D:\FFS0_Factory\.agent\knowledge\living_roadmap_moos.md` to identify which branch is currently active (marked with `[ ]` or `[/]`).
- Check `task.md` in the current conversation workspace for the granular step-by-step checklist.

## 3. Branch-Specific Hydration

### If Branch 1 (ACT 2026 Paper) is active:

- Read the current draft: `D:\FFS0_Factory\.papers\act2026\main.tex`.
- Review the bibliography: `D:\FFS0_Factory\.papers\act2026\references.bib`.
- **Academic Research Tools:**
  - To parse dense PDFs with math symbols, run: `python D:\FFS0_Factory\.papers\act2026\read_pdf_fitz.py <pdf_path> <out_path>`
  - To query the arXiv network for related papers, run: `python D:\FFS0_Factory\.papers\act2026\arxiv_search.py "<query>"`

### If Branch 2 (Open Source Extraction) is active:

- Sync to the isolated module workspace: `my-tiny-data-collider`.
- Review the `package.json` and architectural boundaries to ensure no proprietary FFS0 data leaks.

### If Branch 3 (Superset Runtime) or Branch 4 (System 3) is active:

- Read `D:\FFS0_Factory\CLAUDE.md`.
- Read the active workspace `.agent/index.md` and load `.agent/manifest.yaml` (resolving `includes` and `exports`).
- Verify backend compatibility runtimes at `:8000`, `:8004`, `:18789`.

## 4. DB Array & Graph Synchronization (Admin)

- _Note for IDE/Runtime:_ The `.agent` configurations and workflow files in `FFS0_Factory` are designed to be ingested by the Root Container graph. When the application runs, these workspaces are synced to the DB array, becoming formal structured nodes within the mo:os graph topology subject to RBAC.
