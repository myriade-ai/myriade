# Myriade - The secure AI analytics copilot for your database.

Query any database in natural language, inspect every SQL the agent runs, and get instant, actionable insights

[![image](https://img.shields.io/github/license/myriade-ai/myriade)](https://github.com/myriade-ai/myriade/blob/master/LICENSE)
[![Actions status](https://github.com/myriade-ai/myriade/actions/workflows/test.yml/badge.svg)](https://github.com/myriade-ai/myriade/actions)

## ✨ Why Myriade?

Traditional BI tools still require you to **think about tables, joins, and SQL** before you get to insight. Myriade removes all that friction with an **AI‑native chat interface** that reads your question, explores your database safely in read‑only mode, writes and refines SQL, analyses the result set, and surfaces the answer—all in seconds.

- ⚡ **10× faster answers** – skip schema spelunking and boilerplate SQL.
- 🔒 **Secure by design** – read‑only credentials, limited previews, zero data retention.
- 🧠 **Beyond NL2SQL** – root‑cause analysis, anomaly detection, opportunity discovery.
- 🏗️ **Extensible** – works with Postgres, MySQL, Snowflake, BigQuery and more.

## 🔐 Security Model

0. **Local hosting** – Install Myriade on your own hardware.
1. **Read‑only DB users** – Myriade never mutates your production data.
2. **Limited result preview** – the agent sees row samples & column stats, not full dumps.
3. **Zero‑Knowledge Protection** – encrypt sensitive data before sending it to the LLM.

## 📦 Features

- **Simple set up:** Run Myriade locally in < 5 minutes.
- **Natural‑language chat** to query your data database.
- **AI ↔️ DB trace viewer** so you can inspect every query the agent runs.
- **SQL editor** for power users with AI autocorrect & explain.
- **Prompt templates** ("Projects") to tailor the agent to a domain or KPI set.
- **Data quality control panel** (coming soon).
- **Zero‑Knowledge Protection** (opt‑in, coming soon).

## 💬 Usage Examples

| Ask…                                                           | Myriade does…                                             |
| -------------------------------------------------------------- | --------------------------------------------------------- |
| _"Why did sales drop on 2025‑03‑10?"_                          | scans fact tables, runs cohort diffs, returns root causes |
| _"Create a view of user_id, total_sales, last_product_bought"_ | generates SQL, saves the view, returns preview            |
| _"What KPIs are missing in the store report?"_                 | reviews schema, suggests additional metrics               |

---

## 🚀 Quick Start

### Pre-requisites

ℹ️ Note: get an OpenAI API key. If you don't have one, get it [here](https://www.openai.com/).

### Docker installation

```bash
docker-compose up -d
```

### Manual installation

#### Backend Setup (in [`/service`](/service) directory)

1. **Install Dependencies**:

   ```bash
   uv sync
   ```

2. **Set Environment Variables**:
   in `service/.env.sh` file:

   ```bash
   export AUTOCHAT_MODEL=<Your_OpenAI_Model>
   export OPENAI_API_KEY=<Your_OpenAI_API_Key>
   export DATABASE_URL=<Your_Postgres_Database_URL>
   ```

or to use another provider:

```bash
export AUTOCHAT_PROVIDER=<Your_Provider>
export ANTHROPIC_API_KEY=<Your_Anthropic_API_Key>
```

3. **Run the Backend**:
   ```bash
   bash start.sh dev
   ```

#### Frontend Setup (in [`/view`](/view) directory)

Install Dependencies

```bash
yarn
```

Run the front-end

```bash
yarn dev
```

After completing the steps, open your browser and visit: [http://localhost:5173](http://localhost:5173)
