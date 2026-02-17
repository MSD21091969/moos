# Sandbox Rules

> Access boundaries and path constraints for FFS0 Factory

---

## Allowed Paths

| Path                          | Purpose            |
| ----------------------------- | ------------------ |
| `D:\FFS0_Factory\`            | Factory root       |
| `D:\FFS0_Factory\.agent\`     | Root agent context |
| `D:\FFS0_Factory\workspaces\` | Child workspaces   |
| `D:\FFS0_Factory\models\`     | Pydantic models    |
| `D:\FFS0_Factory\sdk\`        | SDK components     |
| `D:\FFS0_Factory\secrets\`    | API keys (gitignored) |

## Denied Paths

| Path                | Reason                      |
| ------------------- | --------------------------- |
| `C:\Windows\`       | System files                |
| `C:\Program Files\` | Installed software          |
| `%USERPROFILE%\`    | User home (except explicit) |

---

## Behavioral Constraints

1. **Single source of truth** — One definition per concept
2. **Inherit don't duplicate** — Use manifest includes
3. **Stay local** — Sovereignty over convenience
