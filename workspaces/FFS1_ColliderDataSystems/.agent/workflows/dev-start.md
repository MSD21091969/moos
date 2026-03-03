# Dev Start

Use the unified launcher from FFS1 root for stable one-go startup.

## Windows (recommended)

- Full stack (MOOS + ffs6 + ffs4 + ffs5):
   - `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-moos-stack.ps1`
- Sidepanel-only frontend profile (MOOS + ffs4):
   - `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-moos-stack.ps1 -SidepanelOnly`
- Backend-only profile:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File .\start-moos-stack.ps1 -NoFrontends`

`start-dev.bat` now delegates to `start-moos-stack.ps1`.

## Readiness checks performed by launcher

- `http://127.0.0.1:8000/health` (Data Compatibility)
- `http://127.0.0.1:8001/health` (Tool Server)
- `http://127.0.0.1:8004/health` (Agent Compatibility)
- `ws://127.0.0.1:18789` (NanoClaw bridge TCP readiness)
- Frontends (when enabled): `4200`, `4201`, `4202`

## Stop services

Each service runs in its own PowerShell window; close those windows to stop.

## Chrome extension (FFS2 MVP wrapper)

- Extension root:
   - `FFS2_ColliderBackends_MultiAgentChromeExtension/moos/apps/chrome-extension`
- Build unpacked artifact:
   - `pnpm -C .\FFS2_ColliderBackends_MultiAgentChromeExtension\moos nx run @moos/chrome-extension:build`
- Load in Chrome:
   - Open `chrome://extensions`
   - Enable **Developer mode**
   - Click **Load unpacked** and select:
         - `FFS2_ColliderBackends_MultiAgentChromeExtension/moos/apps/chrome-extension/dist`
- Open sidepanel via extension action (pins to `http://localhost:4201` through `sidepanel.html`).
