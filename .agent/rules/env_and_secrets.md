# Environment & Secrets Conventions

> How environment variables and secrets are managed in the Factory.

---

## .env Files

- `.env` files are **never tracked** by git (added to `.gitignore`)
- `.env.example` files **are tracked** as templates (no real values)
- Each workspace that needs env vars has its own `.env` + `.env.example`

## Secrets

- API keys live in `secrets/api_keys.env` (gitignored)
- `secrets/.gitignore` allows only `.gitignore`, `README.md`, and `*.example`
- Template: `secrets/api_keys.env.example`

## Loading

- Python backends use `pydantic-settings` with `env_prefix` to load `.env`
- Frontend uses `NEXT_PUBLIC_*` prefix for client-side env vars
- Chrome extension env vars are build-time only

## .agent/configs vs .env

- `.agent/configs/` documents config **shape** for agents (not runtime values)
- `.env` contains **runtime values** for servers
- These are complementary: configs describe what exists, .env provides values

## Key Environment Variables

| Variable | Location | Purpose |
|----------|----------|---------|
| `GEMINI_API_KEY` | `secrets/api_keys.env` | Google AI Studio API |
| `GOOGLE_APPLICATION_CREDENTIALS` | `secrets/api_keys.env` | GCP service account path |
| `COLLIDER_DATABASE_URL` | `FFS2/.env` | SQLite/Postgres connection |
| `COLLIDER_SECRET_KEY` | `FFS2/.env` | JWT signing key |
| `NEXT_PUBLIC_API_BASE` | `FFS3/.env` | Backend API URL for frontend |
