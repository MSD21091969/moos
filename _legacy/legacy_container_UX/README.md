# Legacy Container UX (Factory Demo)

This is the **Legacy Container UX** component, adapted to run within the Agent Factory environment for **demonstration purposes**.

## Status

- **Mode**: Demo / Visual Only
- **Backend**: Disabled (Mocked/Disconnected)
- **Frontend**: Running on Port 5174

## Quick Start

Run the legacy demo from the factory root:

```powershell
# In d:\agent-factory
.\run_legacy.ps1
```

Access the demo at: **http://localhost:5174**

## Development Notes

This component has been cloned from `my-tiny-data-collider` (feature/rebuild-v2) and modified to run side-by-side with the main Factory Agent Studio.

- **Configuration**: `frontend/.env.demo`
- **Startup Script**: `..\run_legacy.ps1`
