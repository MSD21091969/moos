# LogicGraph — Paper Digest

> **Paper:** Wu et al., "LogicGraph: Benchmarking Multi-Path Logical Reasoning via Neuro-Symbolic Generation and Verification" (arXiv:2602.21044v1, Feb 2026)
>
> **Digest purpose:** Extract concepts relevant to mo:os evaluation pipeline, multi-path derivation, error taxonomy, and mock lifecycle reasoning.

---

## Core Thesis

Existing logical reasoning benchmarks evaluate only **single-path** reasoning (one correct proof). LogicGraph is the first benchmark for **multi-path** logical reasoning: given premises, find ALL minimal subsets that entail the conclusion. This tests both **convergent thinking** (finding the correct answer) and **divergent thinking** (exploring alternative valid paths).

---

## Key Formalizations

### Minimal Support Sets

$$S \subseteq \mathcal{P} \text{ is } \text{MinSup}(S, \mathcal{G}) \iff S \vdash \mathcal{G} \;\wedge\; \forall S' \subsetneq S : S' \nvdash \mathcal{G}$$

where $\mathcal{P}$ is the complete premise set and $\mathcal{G}$ is the goal. A minimal support set is the smallest subset of premises that suffices to derive the conclusion — nothing in it is redundant.

**mo:os relevance:** This formalizes a key question for the hydration pipeline: _what is the minimal set of S1 authored objects needed to fully derive a given S2 operational state?_ If an S2 workspace object can be hydrated via two different subsets of S1 declarations, those are two distinct minimal support sets. Understanding this helps with:

- **Dependency analysis**: Which S1 objects are essential vs. redundant for a given S2 output?
- **Impact analysis**: If an S1 declaration changes, which S2 objects are affected?
- **Mock lifecycle**: A mock category's promotion depends on whether it participates in ANY minimal support set for production state.

### Logic DAG (Backward Construction)

The benchmark generates Logic DAGs by backward construction from the target conclusion using **seven fundamental argument forms**:

| Form | Pattern | Example |
| --- | --- | --- |
| Modus Ponens (MP) | $P, P \to Q \vdash Q$ | If it rains, ground is wet. It rains. ∴ Ground is wet. |
| Modus Tollens (MT) | $\neg Q, P \to Q \vdash \neg P$ | |
| Hypothetical Syllogism (HS) | $P \to Q, Q \to R \vdash P \to R$ | |
| Disjunctive Syllogism (DS) | $P \lor Q, \neg P \vdash Q$ | |
| Constructive Dilemma (CD) | $(P \to Q) \land (R \to S), P \lor R \vdash Q \lor S$ | |
| Simplification (Simp) | $P \land Q \vdash P$ | |
| Conjunction (Conj) | $P, Q \vdash P \land Q$ | |

**Multi-path generation** works by introducing **shared intermediate nodes** in the DAG — a conclusion derivable via two different argument chains that share an intermediate inference step.

**mo:os relevance:** This backward construction parallels backward hydration validation. Given an S2 state:

1. The evaluator traces backward: which morphism programs (from $M$) produced this state?
2. Those programs trace backward to: which validated artifacts (from $V$) produced those programs?
3. Those artifacts trace backward to: which authored objects produced those artifacts?

If there are multiple valid backward paths, the S2 state has multiple minimal support sets — multiple valid derivation histories. The seven argument forms map loosely to mo:os morphism composition patterns: MP ≈ sequential composition, HS ≈ transitive linking, Conj ≈ parallel composition, DS ≈ conditional branching.

### Convergent vs. Divergent Thinking

From Guilford's Structure of Intellect (1967):

- **Convergent thinking**: Given premises, find THE correct conclusion. Evaluates logical soundness.
- **Divergent thinking**: Given premises, find ALL valid reasoning paths. Evaluates creative exploration of the logical space.

**Metrics:**
- $\text{path\_precision}(i)$: fraction of model-proposed paths that are actually valid
- $\text{path\_recall}(i)$: fraction of valid paths that the model discovered
- $\text{Convergent Score}$: average path precision
- $\text{Divergent Score}$: average path recall

**mo:os relevance:** This framework maps directly to mock evaluation:

- **Convergent evaluation**: "Is this mock's proposed topology valid?" — does the mock correctly derive from its stated S1 sources? Tests correctness.
- **Divergent evaluation**: "What OTHER topologies could produce equivalent operational state?" — are there alternative S1 configurations that would yield the same S2 result? Tests completeness of exploration.

The benchmark finding that **LLMs strongly favor convergent over divergent reasoning** (they fixate on one path) has important implications: LLM-proposed mock configurations will likely miss alternative valid configurations. The system should not rely on LLMs alone for exhaustive topology exploration.

---

## Neuro-Symbolic Evaluation Pipeline

### Three-Stage Pipeline

1. **Auto-formalization**: LLM converts natural language reasoning into first-order logic (FOL) formulas
2. **Symbolic verification**: Prover9 (automated theorem prover) checks each step's logical validity
3. **Error classification**: Failed steps are categorized by a hierarchical error taxonomy

**Key result:** 98.80% step-level accuracy for the verifier (near-perfect symbolic checking).

**mo:os relevance:** This maps directly to the kernel validation architecture:

1. **LLM → morphism proposal** (auto-formalization): LLM proposes morphism envelopes
2. **Kernel validation** (symbolic verification): Pure core validates each morphism against graph constraints
3. **Error classification** (hierarchical taxonomy): Failed morphisms are classified by `kernel_specification.md` §9 error types

### Hierarchical Error Taxonomy

| Category | Subcategory | Description |
| --- | --- | --- |
| **Semantic Comprehension** | Misinterpretation | Model misunderstands a premise |
| | Information Omission | Model ignores a relevant premise |
| | Fact Hallucination | Model fabricates non-existent information |
| **Logical Execution** | Invalid Deduction | Conclusion does not follow from premises |
| | Rule Misapplication | Correct rule applied incorrectly |
| | Insufficient Premise | Conclusion drawn from incomplete premise set |

**mo:os mapping:**

| LogicGraph Error | mo:os Equivalent | Kernel Sentinel |
| --- | --- | --- |
| Misinterpretation | Wrong wire port type in morphism | `ErrInvalidPort` |
| Information Omission | Missing required LINK before MUTATE | `ErrPermissionDenied` (wire not found) |
| Fact Hallucination | Referencing non-existent URN | `ErrURNNotFound` |
| Invalid Deduction | Invalid morphism type for context | `ErrInvalidMorphism` |
| Rule Misapplication | Correct morphism, wrong target | `ErrDuplicateWire` / `ErrVersionConflict` |
| Insufficient Premise | MUTATE without required wires | `ErrPermissionDenied` |

---

## Key Experimental Findings

1. **LLMs fixate on single routes** and increasingly fail to discover alternatives as reasoning depth grows — "pseudo-divergence" (appears to explore but merely rephrases the same path).
2. **Result-oriented fabrication**: When pressured for multiple paths, LLMs fabricate invalid reasoning that reaches the correct conclusion.
3. **Path recall degrades with complexity**: As the number of valid paths increases, models find proportionally fewer of them.
4. **Closed-source models (o3, Gemini 2.5 Pro) outperform open-source** on convergent but still fail on divergent.
5. **Process-verified rewards > outcome-verified**: Step-by-step verification outperforms final-answer-only checking.

**mo:os implications:**
- LLM agents in mo:os will propose SINGLE valid morphism sequences but miss alternatives → the kernel should support enumeration of valid morphism programs reaching the same state.
- Process-level verification (each morphism validated individually) is categorically superior to outcome-level verification (only checking final state) — this is functoriality applied to verification.
- The System 3 architecture (symbolic kernel + LLM coprocessor) is validated: symbolic verification catches the errors that LLMs systematically produce.

---

## Concepts Promoted to mo:os Knowledge

| Concept | Promoted To | Section |
| --- | --- | --- |
| Minimal support sets | `foundations.md` §19 | Formalizes minimal S1 dependency for S2 state |
| Convergent/divergent evaluation | `05_moos_design/hydration_lifecycle.md` | Evaluation framework for mock lifecycle |
| Backward construction ↔ backward hydration | `05_moos_design/hydration_lifecycle.md` | Validates bidirectional pipeline |
| Hierarchical error taxonomy | `05_moos_design/kernel_specification.md` §9 | Extends error classification |
| Process-verified > outcome-verified | `foundations.md` §14 | Strengthens functoriality argument |
| LLM pseudo-divergence finding | `foundations.md` §14 | Informs System 3 design constraints |
