# Factory Secrets

This directory contains sensitive credentials. **Never commit actual secrets.**

## Files (create locally):

### `api_keys.env`
```env
# Google AI Studio
GEMINI_API_KEY=your-key-here

# OpenAI (optional)
OPENAI_API_KEY=sk-...

# Anthropic (optional)
ANTHROPIC_API_KEY=sk-ant-...
```

### `gcp-service-account.json`
Download from Google Cloud Console → IAM → Service Accounts → Keys

Then set:
```env
GOOGLE_APPLICATION_CREDENTIALS=D:/factory/secrets/gcp-service-account.json
```

## Usage in Code

```python
from agent_factory.parts.config.settings import load_workspace_settings

settings = load_workspace_settings()
api_key = settings.get_secret("GEMINI_API_KEY")
```

## Security Notes

- This entire directory is gitignored
- In production, use GCP Secret Manager instead
- Rotate keys regularly
- Never log or print secrets
