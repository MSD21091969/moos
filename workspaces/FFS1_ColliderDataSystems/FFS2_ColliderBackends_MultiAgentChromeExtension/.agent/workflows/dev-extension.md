---
description: Chrome Extension development workflow
---

# Chrome Extension Development

## Prerequisites

- Node.js 18+
- pnpm or npm
- Chrome browser

## Setup

1. Install dependencies

```bash
cd ../FFS2_ColliderBackends_MultiAgentChromeExtension/ColliderMultiAgentsChromeExtension
npm install
```

2. Start development server

```bash
npm run dev
```

3. Load in Chrome

- Navigate to `chrome://extensions`
- Enable Developer mode
- Click "Load unpacked"
- Select `build/chrome-mv3-dev`

## Development

- Changes hot-reload automatically
- Check console for errors
- Use Chrome DevTools for debugging

## Build

```bash
npm run build
```
