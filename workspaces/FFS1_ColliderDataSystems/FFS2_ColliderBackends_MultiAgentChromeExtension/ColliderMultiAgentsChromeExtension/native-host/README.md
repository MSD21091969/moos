# Native Messaging Host for FILESYST Domain

This Python-based native host enables the Chrome Extension to access the local filesystem securely via Chrome's Native Messaging protocol.

## Architecture

```
┌─────────────────────┐    Native Messaging    ┌─────────────────────┐
│  Chrome Extension   │◄─────────────────────►│   Python Host       │
│  (background.js)    │    stdin/stdout        │   (host.py)         │
│                     │    JSON + 4-byte len   │                     │
└─────────────────────┘                        └─────────────────────┘
         │                                              │
         │ Uses                                         │ Accesses
         ▼                                              ▼
┌─────────────────────┐                        ┌─────────────────────┐
│  native.ts client   │                        │  Local Filesystem   │
│  (high-level API)   │                        │  (restricted paths) │
└─────────────────────┘                        └─────────────────────┘
```

## Installation

1. **Activate Python environment:**

   ```powershell
   cd D:\FFS0_Factory
   & .\.venv\Scripts\Activate.ps1
   ```

2. **Run installer:**

   ```powershell
   cd ColliderMultiAgentsChromeExtension/native-host
   python install.py [EXTENSION_ID]
   ```

   If you don't provide an extension ID, it will allow all extensions (dev mode).

3. **Verify installation:**
   - Check manifest: `%LOCALAPPDATA%\Google\Chrome\NativeMessagingHosts\com.collider.filesyst.json`
   - Check registry: `HKCU\Software\Google\Chrome\NativeMessagingHosts\com.collider.filesyst`

## Uninstallation

```powershell
python install.py --uninstall
```

## Supported Actions

| Action   | Description        | Parameters                               |
| -------- | ------------------ | ---------------------------------------- |
| `ping`   | Health check       | none                                     |
| `list`   | List directory     | `path`                                   |
| `read`   | Read file          | `path`, `options.max_size`               |
| `write`  | Write file         | `path`, `content`, `options.create_dirs` |
| `search` | Find files         | `path`, `pattern`, `options.max_results` |
| `sync`   | Get directory tree | `path`, `options.max_depth`              |

## Security

The host restricts access to:

- User's home directory (`~`)
- Development workspace (`D:/FFS0_Factory`)

Paths outside these roots are rejected.

## Logging

Logs are written to `native_host.log` in this directory.

## Testing

From the extension, use the `native.ts` client:

```typescript
import { pingNativeHost, listDirectory } from "../external/native";

// Check connection
const pong = await pingNativeHost();
console.log(pong); // { success: true, data: { message: "pong", version: "1.0.0" } }

// List files
const files = await listDirectory("D:/FFS0_Factory");
console.log(files.entries);
```
