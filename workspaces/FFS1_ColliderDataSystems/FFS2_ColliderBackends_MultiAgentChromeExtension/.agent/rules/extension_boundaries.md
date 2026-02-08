# Extension Boundaries

> Hard constraints for Chrome Extension agent behavior.

## Security Boundaries

- Only access domains/appnodes within user's RBAC permissions
- Never execute code outside sandboxed contexts
- Native Messaging only to registered host

## Communication Boundaries

- WebSocket to GraphTool Server for graph operations
- REST/SSE to Data Server for context
- Chrome messaging APIs for internal communication

## Context Boundaries

- Always operate within loaded context scope
- Layer 0 (App0) always present
- Layer N (active tab) additive, not replacing
