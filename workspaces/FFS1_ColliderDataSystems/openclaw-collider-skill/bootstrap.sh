#!/usr/bin/env bash
# bootstrap.sh — Hydrate an OpenClaw workspace from a Collider NodeContainer.
#
# Reads the bootstrap endpoint and writes:
#   AGENTS.md   → agent identity / instructions
#   SOUL.md     → guardrails / rules
#   TOOLS.md    → knowledge / reference docs
#   skills/collider-tools/<name>.SKILL.md  → one file per SkillDefinition
#
# Required env vars:
#   COLLIDER_URL      e.g. http://localhost:8000
#   COLLIDER_NODE_ID  UUID of the root NodeContainer
#   COLLIDER_TOKEN    JWT from POST /api/v1/auth/login
#
# Optional:
#   OPENCLAW_WORKSPACE_DIR  (defaults to ~/.openclaw/workspace)

set -euo pipefail

: "${COLLIDER_URL:?ERROR: Set COLLIDER_URL (e.g. http://localhost:8000)}"
: "${COLLIDER_NODE_ID:?ERROR: Set COLLIDER_NODE_ID (UUID of your root node)}"
: "${COLLIDER_TOKEN:?ERROR: Set COLLIDER_TOKEN (JWT from Collider login)}"

WORKSPACE="${OPENCLAW_WORKSPACE_DIR:-$HOME/.openclaw/workspace}"

echo "🕸️  Collider bootstrap: node ${COLLIDER_NODE_ID}"
echo "   Target workspace: ${WORKSPACE}"

# Fetch bootstrap payload
BOOTSTRAP=$(curl -sf \
  -H "Authorization: Bearer ${COLLIDER_TOKEN}" \
  "${COLLIDER_URL}/api/v1/openclaw/bootstrap/${COLLIDER_NODE_ID}") || {
  echo "ERROR: Failed to fetch bootstrap from ${COLLIDER_URL}" >&2
  exit 1
}

# Write workspace files via inline Python (no extra deps)
python3 - <<PYEOF
import json, pathlib, os, sys

raw = '''${BOOTSTRAP}'''
try:
    b = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"ERROR: Invalid JSON from bootstrap endpoint: {e}", file=sys.stderr)
    sys.exit(1)

ws = pathlib.Path("${WORKSPACE}")
ws.mkdir(parents=True, exist_ok=True)

# Core bootstrap files
(ws / "AGENTS.md").write_text(b.get("agents_md", ""))
(ws / "SOUL.md").write_text(b.get("soul_md", ""))
(ws / "TOOLS.md").write_text(b.get("tools_md", ""))

# Per-skill SKILL.md files
skills = b.get("skills", [])
if skills:
    sk_dir = ws / "skills" / "collider-tools"
    sk_dir.mkdir(parents=True, exist_ok=True)
    for s in skills:
        requires_env = json.dumps(s.get("requires_env", []))
        requires_bins = json.dumps(s.get("requires_bins", []))
        emoji = s.get("emoji", "")
        body = s.get("markdown_body", "")
        skill_md = f'''---
name: {s["name"]}
description: "{s.get("description", "")}"
metadata:
  {{
    "openclaw":
      {{
        "emoji": "{emoji}",
        "requires": {{ "env": {requires_env}, "bins": {requires_bins} }},
      }},
  }}
---

{body}
'''
        filename = s["name"].replace("/", "-") + ".SKILL.md"
        (sk_dir / filename).write_text(skill_md)

print(f"✅  Wrote AGENTS.md, SOUL.md, TOOLS.md + {len(skills)} skill file(s) to {ws}")
print(f"   Node: {b.get('node_path', '?')} ({b.get('kind', '?')})")
PYEOF
