# Factory Secrets

This directory contains sensitive credentials. **Never commit actual secrets.**

## Files (create locally)

### `api_keys.env`

```env
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
GOOGLE_APPLICATION_CREDENTIALS=D:/FFS0_Factory/secrets/gcp-service-account.json
```

## Usage in Code

```python
from agent_factory.parts.config.settings import load_workspace_settings

settings = load_workspace_settings()
api_key = settings.get_secret("GEMINI_API_KEY")
```

For Gmail credentials:

```python
SECRETS_DIR = Path("D:/FFS0_Factory/secrets")
credentials_path = SECRETS_DIR / "gmail_credentials.json"
token_path = SECRETS_DIR / "gmail_token.json"
```

## Security Notes

- This entire directory is gitignored (except README and .example files)
- In production, use GCP Secret Manager instead
- Rotate keys regularly
- Never log or print secrets
