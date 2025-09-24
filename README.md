<div align="center">
  <img width="128px" src="https://framerusercontent.com/images/1nUFUimyxNyoPcSeeeLogtx4CA.svg" />

# Myriade – The AI-Native Data Platform

**Explore, clean, transform, and govern your warehouse with collaborative AI agents.**

[🌐 Website](https://www.myriade.ai) • [⚡ Live Demo](https://app.myriade.ai) • [📦 Self-host](#-quick-start-self-host-in-1-minute)

</div>

---

## 💡 Why we are building Myriade

We want to leverage AI to make data-driven decisions accessible to everyone.

First and foremost, we wanted to make it easy for data teams to analyze their data. It's the core of Myriade.

But the reality is, data warehouse are a mess, and data teams are overwhelmed by the all the tools and monitoring they have to do.

That's why we are building an unified platform to help data teams organize, clean, transform and verify their data.

Our objectives are twofold:

- Give your data team 30‑50 % of their week back, so you can focus on creating business value.
- Organize your data warehouse, so you can safely add AI, and open access to data-driven decisions to everyone.

## 🧭 Platform snapshot

| Agent                         | Status         | What it focuses on                                                                                                             |
| ----------------------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Analyst Agent – Analyse**   | ✅ Available   | True agent that explores, corrects, adapts, verifies, and synthesizes, with editable SQL, charting, and exports.               |
| **Catalog Agent – Explore**   | 🧪 Beta        | Instant and up-to-date warehouse catalog                                                                                       |
| **Quality Agent – Trust**     | 🚧 In progress | Surfaces anomalies, stale data, failing checks, and explains root causes by combining lineage with existing tests (dbt, etc.). |
| **Modelling Agent – Prepare** | 🚧 In progress | Create models with the DBT assistant                                                                                           |
| **Security Agent – Govern**   | 🗒️ TODO        | Enforces scoped access, detects PII data, ...                                                                                  |
| **Cost Agent – Optimize**     | 🗒️ TODO        | Analyzes warehouse usage, identifies inefficiencies, unused tables, reportings, and suggests optimizations.                    |

We build in the open. If a capability is marked 🚧, we are actively designing or prototyping it—expect frequent commits and feedback requests.

---

## 🧩 What you can do today

- **Ask complex questions in plain language** – Myriade drafts the SQL, reruns when you tweak the prompt, and explains the results in context.
- **Trace every decision** – inspect the generated SQL, execution timeline, and follow-up steps before sharing insights.

---

## 🔐 Security and governance

- **Self-host or Cloud** – your choice.
- **Data never leaves your control** – the platform uses read-only credentials and streams previews instead of full table dumps.
- **Zero-Knowledge Protection** _(beta)_ – encrypt sensitive data before the AI sees it.

---

## 🏗 Architecture at a glance

- **Frontend** – Vue 3 + Tailwind + Shadcn components (`/view`).
- **Backend** – Flask + SQLAlchemy + Socket.IO libraries (`/service`).
- **AI** – [Agentlys](https://github.com/myriade-ai/agentlys) library.
- **Datastores** – PostgreSQL (production) or SQLite (quick trials).

---

## 🚀 Quick Start (self-host in ~1 minute)

**With SQLite backend**

```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data myriadeai/myriade:latest
```

Open: [http://localhost:8080](http://localhost:8080)

**With PostgreSQL backend**

```bash
docker run -p 8080:8080 \
  -e DATABASE_URL=postgresql://user:pass@localhost:5432/myriade \
  myriadeai/myriade:latest
```

> [See full setup docs →](./DEVELOPMENT.md)

---

## 🌍 Get Started

- **Try the [Live Demo](https://app.myriade.ai)**
- **Deploy locally** – [Quick Start](#-quick-start-self-host-in-1-minute) above.
- **Star us on GitHub** if you like the project ❤️
