# Run Myriade in development

## Tech Stack Overview

- Frontend: Vue3, Tailwind, Vite
- Backend: Python with Flask, SQLAlchemy, Postgres
  - Agent library: [Autochat](https://github.com/BenderV/autochat)
- Database: Postgres (or SQLite)

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python
- [yarn](https://yarnpkg.com/) for frontend

### Backend Setup (in [`/service`](/service) directory)

1. **Install Dependencies**:

   ```bash
   uv sync
   ```

2. **Set Environment Variables**:
   in `.env.dev` file:

   ```bash
   AUTOCHAT_MODEL=claude-sonnet-4-20250514
   ANTHROPIC_API_KEY=<Your_Anthropic_API_Key>
   DATABASE_URL=postgresql://user:pass@localhost:5432/myriade
   ```

   or to use another provider (e.g. OpenAI):

   ```bash
   AUTOCHAT_PROVIDER=openai
   AUTOCHAT_MODEL=o4-mini
   OPENAI_API_KEY=<Your_OpenAI_API_Key>
   DATABASE_URL=postgresql://user:pass@localhost:5432/myriade
   ```

3. **Run the Backend**:
   ```bash
   bash start.sh dev
   ```

### Frontend Setup (in [`/view`](/view) directory)

Install Dependencies

```bash
yarn
```

Run the front-end

```bash
yarn dev
```

After completing the steps, open your browser and visit: [http://localhost:5173](http://localhost:5173)

## Telemetry

See the [docs/telemetry.md](./docs/telemetry.md) file for details.

## License

Myriade is licensed under the [FAIR](https://fair.io) License.

In a nutshell:

- **Free to tinker**: read the code, run it anywhere, fork it, and submit PRs.
- **Free to use in-house**: self-host Myriade for internal or personal projects with no strings attached.
- **But no commercial free-riding**: for the first 24 months after each release you must not offer Myriade (or a derivative) as a service that competes with the official product.
- **Automatic open-source switch**: exactly two years after a version ships, its licence flips to Apache-2.0, giving you full open-source freedoms—including commercial SaaS.

See the [LICENSE](./LICENSE) file for details.
