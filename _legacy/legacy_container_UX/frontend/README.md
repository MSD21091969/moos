# My Tiny Data Collider - Frontend

![React](https://img.shields.io/badge/react-18.3-blue)
![Vite](https://img.shields.io/badge/vite-5.0-purple)
![License](https://img.shields.io/badge/license-MIT-green)

The interactive frontend for My Tiny Data Collider, built with React, Vite, and ReactFlow. It provides a visual interface for organizing AI agents and tools into nested contexts.

## Features
- **Visual Workspace:** Infinite canvas for organizing AI resources.
- **Universal Object Model:** Consistent UI for all entity types.
- **Real-time Updates:** Live synchronization with the backend.
- **Interactive Agents:** Chat and tool execution interface.

## Installation

```bash
npm install
```

## Usage

```bash
# Standard dev server (default Vite port 5173)
npm run dev

# Phase 1 demo mode (no backend) on port 5174
npm run dev:demo
```

### UX recording (recommended for Phase 1)

The repo includes a single long-running recorder that captures browser console events, navigation, and periodic Zustand snapshots to disk:

- Script: `scripts/mcp/record-ux.ts`
- Output folder: `test-results/mcp/`
- Files: `ux-<timestamp>.jsonl` and `ux-<timestamp>.summary.md`

Run it from the `frontend/` folder:

```bash
npx tsx scripts/mcp/record-ux.ts
```

## Configuration
Configuration is handled via `.env` files (e.g., `.env.development`).

## Contributing
See project guidelines.

## License
MIT License
