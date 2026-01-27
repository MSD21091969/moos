# Factory Development Environment

## Quick Start

```powershell
# From d:\factory
.\dev.ps1 collider      # Start Collider app
.\dev.ps1 studio        # Start Agent Studio
.\dev.ps1 -Stop         # Stop all services
.\dev.ps1 -Status       # Check what's running
```

## Projects

| Project      | Command              | Frontend              | Backend               |
| ------------ | -------------------- | --------------------- | --------------------- |
| Collider     | `.\dev.ps1 collider` | http://localhost:5173 | http://localhost:8000 |
| Agent Studio | `.\dev.ps1 studio`   | http://localhost:3000 | http://localhost:8000 |

## Service Control

```powershell
.\dev.ps1 collider -Service backend   # Backend only
.\dev.ps1 collider -Service frontend  # Frontend only
.\dev.ps1 collider -Service runtime   # Runtime only
```

## Environment Configuration

Edit `.env.development` in factory root - it syncs to projects on startup:

```powershell
code d:\factory\.env.development
```

### Auth Settings

```env
# Skip login (auto-authenticate)
VITE_DEV_SKIP_AUTH=true

# Require login form
VITE_DEV_SKIP_AUTH=false
```

### Test Users

| Email              | Password | Role       |
| ------------------ | -------- | ---------- |
| superuser@test.com | test123  | superadmin |
| lola@test.com      | test123  | user       |
| menno@test.com     | test123  | user       |

## Port Allocation

| Port | Service               |
| ---- | --------------------- |
| 3000 | Agent Studio Frontend |
| 5173 | Collider Frontend     |
| 8000 | Backend API           |
| 8001 | Collider Runtime      |

## Chrome Extension (Collider Pilot)

```powershell
cd workspaces\collider_apps\applications\my-tiny-data-collider\frontend
npm run build:extension
```

Load in Chrome: `chrome://extensions` → Load unpacked → `dist-extension`
