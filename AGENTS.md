# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Myriade is a secure AI analytics copilot for databases. It provides a natural language chat interface that explores databases safely in read-only mode, writes and refines SQL, analyzes result sets, and surfaces actionable insights.

## Architecture

### Tech Stack

- **Frontend**: Vue 3, Tailwind CSS, Vite (in `/view`)
- **Backend**: Python with Flask, SQLAlchemy, PostgreSQL (in `/service`)
- **AI Library**: Autochat for agent functionality
- **Database**: PostgreSQL (or SQLite for development)

### Core Components

- `/service` - Python backend with Flask API, chat agents, and database integrations
- `/view` - Vue.js frontend with real-time chat interface and SQL editor
- `/service/chat/` - AI agent implementation for database analysis
- `/service/back/` - Core database query processing and data warehouse integration
- `/service/auth/` - Authentication and authorization
- `/ai/` - AI training data and conversation management

## Development Commands

### Backend (service/)

- **Install dependencies**: `uv sync`
- **Run development server**: `bash start.sh dev`
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

## Key Modules

### Chat Agent (`/service/chat/`)

- `analyst_agent.py` - Main AI agent for database analysis
- `tools/` - Database interaction tools and chart generation
- `dbt_utils.py` - DBT integration utilities

### Database Layer (`/service/back/`)

- `query.py` - SQL query execution and processing
- `data_warehouse.py` - Data warehouse connections and schema introspection
- `rewrite_sql.py` - SQL query optimization and rewriting

### API Layer (`/service/`)

- `app.py` - Main Flask application
- `main.py` - Application entry point
- Flask-SocketIO for real-time communication

## Testing

- Backend tests in `/service/tests/` using pytest
- Syrupy for snapshot testing
- Test database connection and query functionality
- API endpoint testing with test fixtures

## Security Considerations

- Read-only database access by default
- Limited result previews (samples and stats, not full dumps)
- Zero-knowledge protection for sensitive data (opt-in)
- Local hosting support for security compliance
