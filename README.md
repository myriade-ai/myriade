# 🚀 Myriade – Your AI Data Copilot

<div align="center">
  <img width="128px" src="https://framerusercontent.com/images/1nUFUimyxNyoPcSeeeLogtx4CA.svg" />

**Stop wrestling with SQL. Start getting answers.**

![myriade](https://github.com/user-attachments/assets/06147bb9-92c3-4ed6-8ed1-4604515f876b)


[🌐 Website](https://www.myriade.ai) • [⚡ Live Demo](https://demo.myriade.ai) • [📦 Self-host](#-quick-start-self-host-in-1-minute)

</div>

---

## 💡 Why Myriade?

Business data lives in tables.
Insights live in your head.
**Everything in between is slow.**

Traditional BI tools force you to:

- Dig through table names.
- Guess joins.
- Write and debug SQL.
- Re-run, re-fix, re-interpret.

**Myriade kills that friction.**
Ask your question in plain English → Myriade **explores**, **writes SQL**, **fixes it**, **analyses the result**, and gives you the answer **in seconds**.

### What we value

- **Simplicity** – No setup. No training. Just ask.
- **Speed** – Answers 10× faster than manual SQL.
- **Value creation** – Clear insights so you can focus on what matters.

---

## ✨ What Myriade Does

- **Ask Anything** – “Why did sales drop on March 10?” → you get causes, not just numbers.
- **Analyze Beyond SQL** – anomaly detection, KPI gap analysis, opportunity spotting.
- **Stay in Control** – inspect and edit every query that the AI generated.
- **Plug & Play** – Postgres, MySQL, Snowflake, BigQuery & more.

---

## 🔒 Secure by Design

- **Read-only** – zero chance of accidental data changes.
- **Limited result previews** – AI sees only samples/stats, never full dumps.
- **Zero-Knowledge Protection** _(beta)_ – encrypt sensitive data before the AI sees it.
- **Self-host or Cloud** – your choice.

---

## 🖼 How It Works

1. **Ask** → “Create a view of `user_id`, `total_sales`, `last_product_bought`”
2. **AI explores** → finds the right tables, joins, and filters. explore and iterate.
3. **Answer delivered** → instant insight, exportable.
4. **Inspect** → view what the AI did, edit, and run it.

---

## 💬 Examples

| You Ask…                                         | Myriade Delivers…                                          |
| ------------------------------------------------ | ---------------------------------------------------------- |
| _“Why did signups drop last week?”_              | Detects change, runs cohort diffs, surfaces likely causes. |
| _“What KPIs are missing from the store report?”_ | Reviews schema, suggests relevant new metrics.             |
| _“Show total revenue by region, last 90 days”_   | Writes & runs SQL, charts the result.                      |

---

## 🚀 Quick Start (Self-host in 1 minute)

**With Anthropic (default) and SQLite backend**:

```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data myriadeai/myriade:latest
```

Open: [http://localhost:8080](http://localhost:8080)

**With OpenAI and PostgreSQL backend**:

```bash
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://user:pass@localhost:5432/myriade
  -e AUTOCHAT_PROVIDER=openai \
  -e AUTOCHAT_MODEL=o5-mini \
  -e OPENAI_API_KEY=<your_key_here> \
  myriadeai/myriade:latest
```

> Supports OpenAI, Anthropic, Gemini & more.
> [See full setup docs →](./DEVELOPMENT.md)

---

## 🛠 Why Developers Love It

- Full **AI ↔ DB trace viewer** – every query is transparent.
- **SQL editor** – take over anytime.
- **Prompt templates** – tailor Myriade for a specific domain/KPI set.
- Extensible, self-hostable, no vendor lock-in.

---

## 🌍 Get Started

- **Try the [Live Demo](https://demo.myriade.ai)** – no signup.
- **Deploy locally** – [Quick Start](#-quick-start-self-host-in-1-minute) above.
- **Star us on GitHub** if you like the project ❤️
