# Myriade

[Myriade](https://www.myriade.ai) is the secure AI analytics copilot for your database.

Query any database in natural language, inspect every SQL the agent runs, and get instant, actionable insights.

![output](https://github.com/user-attachments/assets/e4a20de4-8b1e-4ec2-a692-cfdd02dd0533)

## ✨ Why Myriade?

Traditional BI tools still require you to **think about tables, joins, and SQL** before you get to insight.

Myriade removes all that friction with an **AI‑native chat interface** that reads your question, explores your database safely in read‑only mode, writes and refines SQL, analyses the result set, and surfaces the answer—all in seconds.

- ⚡ **10× faster answers** – let the agent do the heavy lifting (schema exploration, SQL generation, result analysis, etc.).
- 🔒 **Secure by design** – read‑only, limited previews, zero knowledge protection, ...
- 🧠 **Beyond NL2SQL** – root‑cause analysis, anomaly detection, opportunity discovery, ...
- 🏗️ **Extensible** – works with Postgres, MySQL, Snowflake, BigQuery & more to come.

## 🔐 Security Model

- **Local hosting** – Install Myriade on your own hardware.
- **Read‑only DB users** – Myriade never mutates your production data.
- **Limited result preview** – the agent sees row samples & column stats, not full dumps.
- **Zero‑Knowledge Protection** – encrypt sensitive data before sending it to the LLM.

## 📦 Features

- **Simple set up** – Run Myriade locally in < 5 minutes.
- **Natural‑language chat** – to query your data database.
- **AI ↔️ DB trace viewer** – so you can inspect every query the agent runs.
- **SQL editor** – for power users with AI autocorrect & explain.
- **Prompt templates** ("Projects") – to tailor the agent to a domain or KPI set.
- **Data quality control panel** – (coming soon).
- **Zero‑Knowledge Protection** – (opt‑in, beta).

## 💬 Usage Examples

| Ask…                                                           | Myriade does…                                             |
| -------------------------------------------------------------- | --------------------------------------------------------- |
| _"Why did sales drop on 2025‑03‑10?"_                          | scans fact tables, runs cohort diffs, returns root causes |
| _"Create a view of user_id, total_sales, last_product_bought"_ | generates SQL, saves the view, returns preview            |
| _"What KPIs are missing in the store report?"_                 | reviews schema, suggests additional metrics               |

---

## 🚀 Quick Start

### Pre-requisites

At this time, we recommend using Anthropic. Get an Anthropic API key if you don't have one [here](https://www.anthropic.com/).
Note: you can also use any other LLM provider (OpenAI, Gemini, etc.). Check the [docker-compose.yml](./docker-compose.yml) file for the available environment variables.

### Run docker-compose

```bash
git clone https://github.com/myriade-ai/myriade.git
docker compose pull
ANTHROPIC_API_KEY=XXXX docker compose up -d
```

### Open the app

```bash
http://localhost:8080
```

Connect your database & profit
