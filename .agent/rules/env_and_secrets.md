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

- Go backends (MOOS) use `os.Getenv()` or config files to load env vars
- Python backends use `pydantic-settings` with `env_prefix` to load `.env`
- Frontend (FFS3) uses `VITE_*` prefix for client-side env vars (Vite 7)
- Chrome extension env vars are build-time only

## .agent/configs vs .env

- `.agent/configs/` documents config **shape** for agents (not runtime values)
- `.env` contains **runtime values** for servers
- These are complementary: configs describe what exists, .env provides values

## Key Environment Variables

| Variable                         | Location               | Purpose                                        |
| -------------------------------- | ---------------------- | ---------------------------------------------- |
| `GEMINI_API_KEY`                 | `secrets/api_keys.env` | Google AI Studio API                           |
| `ANTHROPIC_API_KEY`              | `secrets/api_keys.env` | Anthropic Claude API                           |
| `OPENAI_API_KEY`                 | `secrets/api_keys.env` | OpenAI API (optional)                          |
| `GOOGLE_APPLICATION_CREDENTIALS` | `secrets/api_keys.env` | GCP service account path                       |
| `COLLIDER_DATABASE_URL`          | `FFS2/.env`            | SQLite/Postgres connection                     |
| `COLLIDER_SECRET_KEY`            | `FFS2/.env`            | JWT signing key                                |
| `VITE_DATA_SERVER_URL`           | `FFS3/.env`            | Data server URL for frontend                   |
| `VITE_AGENT_RUNNER_URL`          | `FFS3/.env`            | Agent runner URL for frontend                  |
| `MOOS_HTTP_ADDR`                 | `MOOS/.env`            | MOOS HTTP listen address                       |
| `MOOS_WS_ADDR`                   | `MOOS/.env`            | MOOS WebSocket listen address                  |
| `MOOS_MODEL_PROVIDER`            | `MOOS/.env`            | Default LLM provider (gemini/anthropic/openai) |
