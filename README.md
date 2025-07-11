# Myriade
[Myriade](https://www.myriade.ai) is the secure AI analytics copilot for your database.

Query any database in natural language, inspect every SQL the agent runs, and get instant, actionable insights.

![output](https://github.com/user-attachments/assets/e4a20de4-8b1e-4ec2-a692-cfdd02dd0533)

## ✨ Why Myriade?

Traditional BI tools still require you to **think about tables, joins, and SQL** before you get to insight. Myriade removes all that friction with an **AI‑native chat interface** that reads your question, explores your database safely in read‑only mode, writes and refines SQL, analyses the result set, and surfaces the answer—all in seconds.

- ⚡ **10× faster answers** – skip schema spelunking and boilerplate SQL.
- 🔒 **Secure by design** – read‑only credentials, limited previews, zero data retention.
- 🧠 **Beyond NL2SQL** – root‑cause analysis, anomaly detection, opportunity discovery.
- 🏗️ **Extensible** – works with Postgres, MySQL, Snowflake, BigQuery, ...

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

ℹ️ Note: get an Anthropic API key. If you don't have one, get it [here](https://www.anthropic.com/).

### Create .env file

```bash
cp .env.example .env
# Edit .env file with your values
```

### Run docker-compose

```bash
git clone https://github.com/myriade-ai/myriade.git
docker compose pull
docker compose up -d
```

### Open the app

```bash
http://localhost:5173
```
