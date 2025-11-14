# 🛠 Myriade – Development Setup

> Build, run, and hack on your own AI data copilot.

---

## ⚙ Tech Stack

- **Frontend** – Vue 3, Tailwind CSS, Vite
- **Backend** – Python (Flask, SQLAlchemy, Postgres)

  - AI Agent Library: [Agentlys](https://github.com/myriade-ai/agentlys)

- **Databases** – Postgres (recommended) or SQLite

---

## 📋 Prerequisites

- [uv](https://docs.astral.sh/uv/) – Python package & env manager
- [yarn](https://yarnpkg.com/) – Frontend package manager
- PostgreSQL 14+ (or SQLite for quick local testing)
- An API key for your LLM provider (Anthropic, OpenAI, Gemini, etc.)

---

## 🚀 Backend Setup

**Location:** [`/service`](/service)

1. **Install dependencies**

   ```bash
   uv sync
   ```

   Install the charts tool package inside the backend

   ```bash
   cd chat/tools/echarts-render && yarn install
   ```

2. **Configure environment variables**
   Create `.env.dev` in `/service`:

   **Example – Anthropic (default)**

   ```bash
   AGENTLYS_PROVIDER=anthropic
   AGENTLYS_MODEL=claude-sonnet-4-5-20250929
   ANTHROPIC_API_KEY=<Your_Anthropic_API_Key>
   DATABASE_URL=postgresql://<db_user>:<strong_password>@localhost:5432/myriade
   ```

   **Example – OpenAI**

   ```bash
   AGENTLYS_PROVIDER=openai
   AGENTLYS_MODEL=o4-mini
   OPENAI_API_KEY=<Your_OpenAI_API_Key>
   DATABASE_URL=postgresql://<db_user>:<strong_password>@localhost:5432/myriade
   ```

   **Tip:** You can also use SQLite for a zero-config local dev:

   ```bash
   DATABASE_URL=sqlite:///./data/dev.db
   ```

3. **Run the backend**

   ```bash
   bash start.sh dev
   ```

---

## 💻 Frontend Setup

**Location:** [`/view`](/view)

1. **Install dependencies**

   ```bash
   yarn
   ```

2. **Run the dev server**

   ```bash
   yarn dev
   ```

3. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔍 Telemetry

See [`docs/telemetry.md`](./docs/telemetry.md) for what we collect and why.

---

## 📜 License

Myriade is licensed under the [Fair Core License](https://fair.io) [(FCL-1.0-ALv2)](http://fcl.dev):

- ✅ **Free to tinker** – read the code, run it, fork it, submit PRs.
- ✅ **Free to self-host** – personal use, or internal company use of basic features (chat).
- 🚫 **Enterprise features** – data catalog, modeling, quality reviews, etc. require a subscription via our auth.
- 🚫 **No competition** – for 24 months after release, you can’t offer Myriade (or a derivative) as a competing product.
- 🔄 **Open-source switch** – 2 years after each release, the license flips to Apache-2.0.

See [`LICENSE`](./LICENSE) for full details.
