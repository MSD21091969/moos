# kb-starter

Minimal knowledge-base scaffold for the **mo:os** kernel.

Copy this directory to a location **outside** the repo and boot with:

```powershell
# Windows
.\moos.exe --kb C:\path\to\your\kb --hydrate

# Linux / macOS
./moos --kb /path/to/your/kb --hydrate
```

## Structure

| Path                     | Purpose                                                       |
| ------------------------ | ------------------------------------------------------------- |
| `superset/ontology.json` | 21-kind / 16-morphism categorical ontology (source of truth)  |
| `superset/schema.json`   | JSON schema for ontology validation                           |
| `instances/`             | Your domain instance models (`.json` files, hydrated on boot) |
| `doctrine/`              | Your prose specs and policies (`.md` files, read by agents)   |

## Minimum viable KB

The kernel requires only `superset/ontology.json` to boot.  
Everything else (`instances/`, `doctrine/`) can be empty directories.

## Extending

- Add `.json` files under `instances/` to materialise domain nodes and wires on boot.
- Add `.md` files under `doctrine/` to capture design decisions and policies.
- Add further subdirectories (e.g. `design/`, `reference/`) as your KB grows — the kernel ignores unknown directories.

See the full ontology spec at `superset/ontology.json` and the schema at `superset/schema.json`.
