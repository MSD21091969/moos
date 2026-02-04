---
description: FILESYST sync workflow between local folders and Data Server
---

# FILESYST Sync Workflow

## Overview

Sync `.agent/` folders between local filesystem and Collider Data Server.

## Directions

| Direction     | Trigger          | Frequency    |
| ------------- | ---------------- | ------------ |
| File → Server | Chrome Extension | Daily/manual |
| Server → File | Manual/API       | On-demand    |

## File → Server

1. Extension reads `.agent/` via Native Messaging
2. Extension sends to Data Server via REST
3. Server stores in nodecontainer

## Server → File

1. Request sync from Extension or API
2. Data Server sends container content
3. Native Host writes to `.agent/`

## Conflict Resolution

- Last-write-wins (with timestamp)
- Future: 3-way merge
