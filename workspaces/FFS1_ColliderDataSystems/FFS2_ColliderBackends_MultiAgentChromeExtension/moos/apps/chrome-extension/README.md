# Collider Multi Agents Chrome Extension (MVP)

This extension is a thin MV3 wrapper for the `ffs4` sidepanel app.

## Dev flow

1. Start backend + sidepanel:
   - `powershell -NoProfile -ExecutionPolicy Bypass -File ..\..\..\..\start-moos-stack.ps1 -SidepanelOnly`
2. Build unpacked extension output:
   - `pnpm -C ..\.. nx run @moos/chrome-extension:build`
3. Open `chrome://extensions`
4. Enable **Developer mode**
5. Click **Load unpacked** and select `dist/`
6. Pin the extension and click it to open the sidepanel.

The sidepanel page embeds `http://localhost:4201`.
