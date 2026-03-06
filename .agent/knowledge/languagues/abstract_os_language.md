# The Abstract Language of mo:os

When moving from Python to a strict Go backend utilizing Category Theory and Functorial Semantics, `mo:os` underwent a profound philosophical shift: **it stopped being a program that _executes_ a script, and became a Virtual Machine that _evaluates_ a Graph.**

In traditional software, you write text in a programming language (like C, Python, or Go), the compiler builds an Abstract Syntax Tree (AST), and the CPU executes it.

In `mo:os`, **the Database Graph _is_ the AST.** We have created an Abstract Language.

## The Vocabulary of the OS Language

If `mo:os` is an abstract programming language, what are its components?

- **Syntax (Nouns):** The Containers (Nodes). The JSON schema of each container dictates the rigid "types" of our language.
- **Grammar (Verbs):** The Wires (Edges/Morphisms). Connecting `Container A` to `Container B` is the equivalent of writing `A | B` or `A.pipe(B)` in code.
- **The Execution Engine (VM):** The pure Go Kernel main loop. It constantly monitors the database state and executes the Wires.

## The Role of the Root Container

The User correctly identified a critical distinction: **The Root Container (`urn:container:os:kernel`) is the "main program", but it is absolutely NOT an LLM Context Window.**

If the Root Container were fed into an LLM context, it would be a catastrophic violation of sovereignty, context limits, and determinism.

Instead, the Root Container is the `init` process of our Abstract Language.

1. The Go Kernel (which contains zero LLM hallucination, only pure math and logic) boots up.
2. The Go Kernel evaluates the Root Container in the PostgreSQL database.
3. The Root Container contains the top-level User Workspaces and Access Control Lists (ACLs).

## Where do LLMs fit in this Language?

If the Go Kernel is the VM, and the Graph is the AST, the LLM is merely a **Fuzzy Processing Unit (FPU).**

It is a specialized coprocessor, much like a GPU.

When a user in a sub-workspace decides to invoke an AI (e.g., they drop a document into an AI translator template), the Go Kernel does not hand the OS over to the LLM.

1. **Sandboxing:** The Go Kernel uses the graph structure to isolate a specific _subgraph_ (only the containers that specific User has permissioned for that specific Workspace).
2. **Serialization:** The Go Kernel serializes _only_ that permitted subgraph into text (the context window).
3. **Execution:** The LLM FPU processes the text and returns a predicted Morphism (e.g., `MUTATE Translator_Output`).
4. **Validation:** The Go Kernel regains control, mathematically verifies the requested Morphism against the ACLs, and applies it to the AST.

## The Continuous Loop

This creates a flawless, continuous feedback loop.

Because the "main program" semantics are held in the strictly-typed Root Container and evaluated by the deterministic Go Kernel, the OS state never corrupts. The LLMs are forever trapped as sandboxed subroutines within our Abstract Language, safely fed only the exact data top-level containers allow them to see.

This is the ultimate realization of **Harness Agnosticism**. We are not building agentic scripts; we have built a compiler for human intent.
