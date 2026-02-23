---
description: Build and load the ColliderMultiAgentsChromeExtension in Chrome for
development
---

# Dev: Chrome Extension

Build the Plasmo extension and load it into Chrome for development.

## Steps

1. Install dependencies (first time only):

   ```powershell
   cd D:\FFS0_Factory\workspaces\FFS1_ColliderDataSystems\FFS2_ColliderBackends_MultiAgentChromeExtension\ColliderMultiAgentsChromeExtension
   pnpm install
   ```

2. Start the Plasmo dev server (auto-rebuilds on save):

   ```powershell
   pnpm dev
   ```

   This outputs the extension to `build/chrome-mv3-dev/`.

3. Load in Chrome:
   - Open `chrome://extensions`
   - Enable **Developer mode** (top right toggle)
   - Click **Load unpacked**
   - Select: `ColliderMultiAgentsChromeExtension/build/chrome-mv3-dev/`

4. After loading, pin the extension and open the sidepanel.

## Notes

- The extension connects to ColliderDataServer on `:8000` — make sure it's running.
- Changes to source files trigger automatic rebuild; reload the extension in `chrome://extensions` to pick them up.
- Check `chrome://extensions` → Details → Errors for runtime errors.
