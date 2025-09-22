# AGENTS.md

## Project Overview

Myriade is the first AI-native data platform.
As it's core, it provide an interface to explore and analyze databases with a data analyst agent.
For enterprise customers, it provides interfaces to maintain up-to-date data catalog, reduce data warehouse costs, assist with modeling, etc...

## Architecture

### Tech Stack

- **Frontend**: Vue 3, Tailwind CSS, Vite (in `/view`)
- **Backend**: Python with Flask, SQLAlchemy, Alembic, Socket.IO (in `/service`)
- **AI Library**: [Agentlys library](https://github.com/myriade-ai/agentlys)
- **Database**: PostgreSQL (or SQLite -- recommended -- for light/development implementation)

### Core Components

- `/service` - Python backend with Flask API, chat agents, and database integrations
- `/view` - Vue.js frontend with real-time chat interface and SQL editor
- `/service/chat/` - AI agent implementation for database analysis
- `/service/back/` - Core database query processing and data warehouse integration
- `/service/auth/` - Authentication and authorization
- `/ai/` - experimental/ML utilities not required for app runtime.
- `/setup/`, `/scripts/`, `/data/` – deployment, helpers, and sample data.
- `/docs/` – documentation (e.g., telemetry).

### Key Modules

- `data_warehouse.py` - Data warehouse connections and schema introspection
- `analyst_agent.py` - Main AI agent for database analysis
- `tools/` - Database interaction tools and chart generation

## Development Commands

### Backend (service/)

- **Install dependencies**: `uv sync --all-extras --dev`
- **Run development server (migrations included)**: `bash start.sh dev`
- **Run tests**: `uv run pytest`
- **Lint**: `uv run ruff check`
- **Format**: `uv run ruff format`

### Frontend (view/)

- **Install dependencies**: `yarn`
- **Run development server**: `yarn dev`
- **Build**: `yarn build`
- **Type check**: `yarn type-check`
- **Lint**: `yarn lint`
- **Format**: `yarn format`

### Coding Style & Naming Conventions

- Python: PEP8, 4 spaces. Enforced by Ruff and ruff-format. Run via pre-commit.
- Vue/TS: ESLint + Prettier (2‑space indent). Use PascalCase for components, camelCase for props/data, `useX` for composables.
- Filenames: Python `snake_case.py`; Vue components `PascalCase.vue`; TS modules `kebab-case.ts` where already used.
- Imports: keep first‑party packages grouped (see Ruff isort config).

## Environment Setup

### Backend Configuration

Create `.env.dev` file in `/service` with:

```
AUTOCHAT_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=<your_key>
DATABASE_URL=postgresql://user:pass@localhost:5432/myriade
```

In `/service` use `source .venv/bin/activate` to activate the virtual environment

### Development Workflow

1. Backend runs on port 5000 (Flask)
2. Frontend runs on port 5173 (Vite dev server)
3. Production runs on port 8080 (Docker)

## Testing Guidelines

- Framework: `pytest` with snapshot testing (syrupy). Snapshots live under `tests/__snapshots__/`.
- Run all tests: `cd service && uv run pytest -q`
- Update snapshots (when intentional): `uv run pytest --snapshot-update`
- Aim for coverage on new logic (`pytest --cov=service`). Place API tests under `service/tests/api/` and unit tests near modules.

## Commit & Pull Request Guidelines

- Commits: follow Conventional Commits, e.g., `feat(service): add catalog tool` or `fix(view): debounce input`.
- Scope suggestions: `service`, `view`, `chat`, `back`, `auth`.
- Before opening a PR: run tests, `pre-commit run -a`, and `cd view && yarn lint` if frontend changed.
- PRs should include: clear description, linked issues, relevant screenshots (UI), migration notes if schema changes, and test updates.

## Security & Config Tips

- Do not commit secrets. Use `service/.env.dev` for local dev (see `DEVELOPMENT.md`).
- Supported DBs: Postgres (recommended) and SQLite for quick runs.
- For chart rendering, ensure `cd service/chat/tools/echarts-render && yarn install` on first setup.
- Ensure that user/org only have access to the content they are allowed to access.
