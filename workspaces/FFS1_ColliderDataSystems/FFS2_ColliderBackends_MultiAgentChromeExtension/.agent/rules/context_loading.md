---
description: How agent context is layered — App0 base layer, active tab appnode
additive layer, domain-specific loading (FILESYST/CLOUD/ADMIN) activation:
model_decision
---

# Context Loading Rules

> Rules for how agent context is loaded and layered.

## Layering

1. **Layer 0**: App0 default context (always present)
2. **Layer N**: Active tab's appnode context (additive)

## Inheritance

- Child workspaces inherit from parent via manifest.yaml
- `includes:` defines what to load from parent
- `exports:` defines what children can inherit

## Domain-Specific Loading

| Domain | Source | Method |
| -------- | ----------------- | ---------------- |
| FILESYST | .agent/ folders | Native Messaging |
| CLOUD | nodecontainer | Data Server API |
| ADMIN | account container | Data Server API |

## Cache Strategy

- IndexedDB for persistent cache
- chrome.storage.session for hot cache
- SSE for real-time updates
