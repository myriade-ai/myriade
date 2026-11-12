---
name: data-question
description: Answer a question about the organisation's own data or business with the Myriade connector — a figure, a KPI, a trend, a breakdown, a comparison, why something moved, which table holds what. Use whenever Myriade's tools (myriade_search_workspace, myriade_query…) are connected and the person asks about their sales, customers, orders, stock, revenue or any business metric, even without naming Myriade.
---

# Answer a data question with Myriade

Myriade holds this organisation's databases, its catalog and its definitions.
For a question about their data it is the source: its definitions win over a
generic method, and its reports and alerts are what the team already knows.

## 1. Read the guide once

If `myriade_guide` has not been read in this conversation, read it before the
first query. It carries what Myriade's own chat starts from — the
organisation's language, instructions and memory, who the person is — with
the analyst's own rules for searching, querying and answering, the instance
URL, and what the person may do. Do not restate it to the person.

## 2. Search, and read what comes back in this order

One `myriade_search_workspace` call with every business word of the question.
Then, before any SQL:

1. **A term or metric** for the concept → its definition is the rule.
2. **A report** that answers the question. When it is fresh (`maintained`, or
   updated by a person in the last few days) and covers the period asked,
   answer from it: open it with `myriade_read`, give its figure, cite it, and
   query only what it does not cover. Do not rebuild a maintained report to
   check it unless the person asks or its figure contradicts something you saw.
   An older report still gives the method and the definitions: reuse them,
   recompute the numbers.
3. **An alert, check or topic** on the matter → it may already explain the
   move (a load that did not run, a store that stopped sending tickets). Say so.
4. **Tables** → read the 2–5 the query needs in one `myriade_read` call.

## 3. Query

- Aggregate in SQL. `myriade_query` returns at most 50 rows; never total,
  average or rank from rows marked `truncated`.
- Check the period the table actually covers (`MIN`/`MAX` of its date) when a
  result is empty or looks low: a modelled table can lag behind its sources.
- Give each query a short `title`: it is saved in Myriade under that name.

## 4. Answer

Follow the guide's answer rules (figure first, the assumption in one line).
Then cite what the figure rests on, as links the person can open:

- the saved query: `query_url` from the result, else `<instance>/query/<query_id>`;
- the report or term used: `<instance>/reports/<id>`, or the path the tool printed.

Name a Myriade object by its name in the app (the report « Point hebdo des
ventes », the topic « Ventes magasins »), not by its table or uuid alone.

## 5. What the work taught

When the data contradicted or completed the catalog — a stale model, a
column's real meaning, a join, a filter everyone needs — say it in one line and
offer to record it in Myriade. Write it only once the person agrees, after
reading the server's documentation skill (`myriade_read_skill`); the guide
says which catalog tool applies to their rights.

When the analysis is worth keeping or sharing, offer a Myriade report
(`myriade_create_report`) rather than a local file: the team finds it in
Myriade, with its queries. Make a local file (chart, spreadsheet) when the
person asks for a file.
