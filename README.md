<div align="center">
  <img align="center" width="128px" src="https://framerusercontent.com/images/1nUFUimyxNyoPcSeeeLogtx4CA.svg" />
	<h1 align="center"><b>Myriade</b></h1>
	<p align="center">
		<a href="https://www.myriade.ai"><strong>Myriade</strong></a> is the secure AI analytics copilot for your database.
    <br /><br />
    Query any database in natural language, inspect every SQL the agent runs, and get instant, actionable insights.
  </p>

![output](https://github.com/user-attachments/assets/e4a20de4-8b1e-4ec2-a692-cfdd02dd0533)

👉👉👉 [Live Demo](https://demo.myriade.ai) 👈👈👈

</div>

## ✨ Why Myriade?

Traditional BI tools still require you to **think about tables, joins, and SQL** before you get to insight.

Myriade removes all that friction with an **AI‑native chat interface** that reads your question, explores your database safely in read‑only mode, writes and refines SQL, analyses the result set, and surfaces the answer—all in seconds.

- ⚡ **10× faster answers** – let the agent do the heavy lifting (schema exploration, SQL generation, result analysis, etc.).
- 🔒 **Secure by design** – read‑only, limited previews, zero knowledge protection, ...
- 🧠 **Beyond NL2SQL** – root‑cause analysis, anomaly detection, opportunity discovery, ...
- 🏗️ **Extensible** – works with Postgres, MySQL, Snowflake, BigQuery & more to come.

## 🔐 Security Model

- **Local hosting** – Install Myriade on your own hardware.
- **Read‑only** – Myriade never mutates your production data (opt‑in).
- **Limited result preview** – the agent sees row samples & column stats, not full dumps.
- **Zero‑Knowledge Protection** – encrypt sensitive data before sending it to the LLM (opt‑in, beta).

## 📦 Features

- **Simple set up** – Run Myriade locally in < 5 minutes.
- **Natural‑language chat** – to query your data database.
- **AI ↔️ DB trace viewer** – so you can inspect every query the agent runs.
- **SQL editor** – take over and edit the SQL the agent generates.
- **Prompt templates** ("Projects") – to tailor the agent to a domain or KPI set.
- **Data Quality control panel** – (coming soon).

## 💬 Usage Examples

| Ask…                                                           | Myriade does…                                             |
| -------------------------------------------------------------- | --------------------------------------------------------- |
| _"Why did sales drop on 2025‑03‑10?"_                          | scans fact tables, runs cohort diffs, returns root causes |
| _"Create a view of user_id, total_sales, last_product_bought"_ | generates SQL, saves the view, returns preview            |
| _"What KPIs are missing in the store report?"_                 | reviews schema, suggests additional metrics               |

---

## 🚀 Quick Start

This will help you run Myriade locally, without the user management support.

### Pre-requisites

At this time, we recommend using **Anthropic** to get the best results. Get an Anthropic API key if you don't have one [here](https://www.anthropic.com/).

Note: you can also use any other LLM provider (OpenAI, Gemini, etc.). Check the [docker-compose.yml](./docker-compose.yml) file for the available environment variables.

### Basic run with SQLite backend

```bash
docker run -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -e ANTHROPIC_API_KEY=your_key_here
  myriadeai/myriade:latest
```

This will create a SQLite database in the `data` folder.

### Run with OpenAI provider

```bash
docker run -p 8080:8080 \
  -e AUTOCHAT_PROVIDER=openai \
  -e AUTOCHAT_MODEL=o4-mini \
  -e OPENAI_API_KEY=your_key_here \
  myriadeai/myriade:latest
```

### Run with PostgreSQL backend

```bash
docker run -p 8080:8080 \
  -e ANTHROPIC_API_KEY=your_key_here \
  -e DATABASE_URL=postgresql://user:pass@localhost:5432/myriade \
  myriadeai/myriade:latest
```

### Access the application

Open your browser to: http://localhost:8080

### Environment variables

- `ANTHROPIC_API_KEY` - Required for AI functionality
- `DATABASE_URL` - Optional, for PostgreSQL backend
- `HOST` - The public URL of your deployment (default: http://localhost:8080)
- `GUNICORN_THREADS` - Optional, for Gunicorn threads (default: 4)
- `AUTOCHAT_PROVIDER` - Optional, for AI provider (default: anthropic)
- `AUTOCHAT_MODEL` - Optional, for AI model (default: claude-sonnet-4-20250514)
- `OPENAI_API_KEY` - Optional, for OpenAI models

### Open the app

```bash
http://localhost:8080
```

Connect your database & profit

## Running for Development

If you're a developer looking to modify Myriade or set up a local development environment, follow the instructions in [DEVELOPMENT.md](./DEVELOPMENT.md).
