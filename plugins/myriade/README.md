# Myriade for Claude

Ask Claude about your organisation's data and get the answer Myriade's own
analyst would give: the figure computed with your team's definitions, the
report or alert that already explains it, and a link to the saved query so
anyone can check it.

The plugin bundles two things:

- **The Myriade connector** (`https://app.myriade.ai/mcp`): your databases,
  catalog, definitions, reports, brief, alerts and topics, with exactly your
  rights in Myriade. You sign in with your Myriade account the first time.
- **Two skills** that teach Claude how to work with it:
  - `data-question` — answer a question on your data: search the catalog and
    the reports first, reuse a fresh report instead of recomputing it, query
    with your definitions, cite the saved query, offer to record what the work
    taught in the catalog.
  - `follow-up` — your brief, alerts and topics: find the matter, record what
    the team did on the alert (or the topic) where the next reader will see it,
    and say what was written where.

## Use it

Ask in your own words: "Combien a fait le CA la semaine dernière ?",
"What's on my brief?", "We chased the dress supplier, delivery Thursday — note
it in Myriade." The skills load by themselves; you can also call them as
`/myriade:data-question` and `/myriade:follow-up` in Claude Code and Cowork.

## Install

- **Claude Code**: `claude plugin marketplace add myriade-ai/myriade`,
  then `claude plugin install myriade@myriade`.
- **claude.ai and Cowork**: Customize → Plugins → Add → Add marketplace, with
  `https://github.com/myriade-ai/myriade`. Then connect the Myriade connector
  from the plugin's Connectors tab.
- **Your organisation**: an Owner lists the plugin in the organisation's own
  marketplace (Organization settings → Plugins & skills) to install it for
  everyone.

**Self-hosted Myriade**: change the URL in `.mcp.json` to your instance's
(`https://<your-instance>/mcp`) in your organisation's copy. The skills work
with any Myriade connector.

## Data

The plugin itself stores and sends nothing. Claude calls your Myriade instance
through the connector, as you: queries run on your databases under your rights
and are saved in Myriade; notes and acknowledgements are written in Myriade,
signed by you.
