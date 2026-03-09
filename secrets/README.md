# Factory Secrets

This directory contains sensitive credentials. **Never commit actual secrets.**

## Canonical role

- `secrets/` is the Secret bindings surface for this workspace.
- `api_keys.env` is the canonical local secret env file.
- Root `.env` files are not authoritative here. If some downstream tool requires `.env`, generate it from `secrets/` as a compatibility projection.

## Files (create locally)

### `api_keys.env`

```env
# mo:os local development
MOOS_DB_PASSWORD=your-local-postgres-password

# Google AI Studio
GEMINI_API_KEY=your-key-here

# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...
```

### `gmail_credentials.json`

Google OAuth2 client credentials for Gmail API access.
Download from Google Cloud Console → APIs & Services → Credentials → OAuth 2.0
Client IDs.

### `gmail_token.json`

Auto-generated OAuth2 token from the Gmail authentication flow.
Refreshed automatically when expired.

### `gcp-service-account.json`

Download from Google Cloud Console → IAM → Service Accounts → Keys

Then set:

```env
GOOGLE_APPLICATION_CREDENTIALS=D:/FFS0_Factory/moos/secrets/gcp-service-account.json
```

## Usage in Code

```python
import os
from pathlib import Path

from agent_factory.parts.config.settings import load_workspace_settings

settings = load_workspace_settings()
api_key = settings.get_secret("GEMINI_API_KEY")
```

The code path should resolve shared settings from `.agent/configs/` and confidential bindings from `secrets/`. It should not treat root `.env` as the source of truth.

For the Windows local-development kernel preset, `MOOS_DB_PASSWORD` is only required if `MOOS_KERNEL_STORE=postgres` and `platform/presets/windows-local-dev.json` needs to resolve `MOOS_DATABASE_URL` without committing a literal password.

For Gmail credentials:

```python
FACTORY_ROOT = Path(os.environ.get("FACTORY_ROOT", "D:/FFS0_Factory/moos"))
SECRETS_DIR = FACTORY_ROOT / "secrets"
credentials_path = SECRETS_DIR / "gmail_credentials.json"
token_path = SECRETS_DIR / "gmail_token.json"
```

## Security Notes

- This entire directory is gitignored (except README and .example files)
- Keep `.env` generated-only if needed for compatibility; do not hand-author it as workspace truth
- In production, use GCP Secret Manager instead
- Rotate keys regularly
- Never log or print secrets
