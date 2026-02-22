# FILESYST Domain Instructions

> Instructions for IDE code assist in FILESYST domain (this workspace).

## This Workspace

FFS1_ColliderDataSystems is an IDE workspace containing:

- Code for Chrome Extension
- Code for Backend Servers (DataServer, GraphToolServer, VectorDbServer, AgentRunner)
- NanoClawBridge (replaces legacy skill package)
- Shared libraries

## Child Workspaces

- FFS2, FFS3... = child code projects within this workspace
- Each inherits from this manifest

## Agent Role

When assisting in this workspace:

1. Understand the codebase structure
2. Follow established patterns (see rules/)
3. Reference architecture docs (see knowledge/architecture/)
4. Use filesystem tools for file operations
