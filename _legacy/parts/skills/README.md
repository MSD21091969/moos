# V-Storm Skills Store

> **Standard**: V-Storm DeepAgent Pattern
> **Content**: Markdown Files Only (`.md`)

## Purpose

This directory stores **Skills** (Job Training).
Each `.md` file represents a distinct capability set or persona that an Agent can "learn" by ingesting.

## Format

Skills should follow the `AgentSpec` knowledge format:

```markdown
# Skill Name

## Role Description

...

## Rules

- Rule 1
- Rule 2

## Knowledge

...
```

**Do NOT put Python code here.** Python tools belong in `../toolsets/`.
