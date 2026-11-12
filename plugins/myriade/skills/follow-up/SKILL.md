---
name: follow-up
description: Follow up on what Myriade watches — the person's brief, alerts, checks, topics — and record what the team did about it. Use when the person asks what is going on, what is on their brief, about an alert, a check or a Myriade topic (« sujet »), or asks to note, log, record, acknowledge, close or snooze something in Myriade (« note-le », « on a relancé le fournisseur », « c'est réglé »).
---

# Follow up in Myriade

Myriade watches the data with checks; a tripped check is an alert; a topic
(« sujet ») groups the checks of one business subject and gets a reading
written by Myriade; the brief is each person's page over all of it. What the
team writes there is what the next reader — a colleague, the brief, the
topic's next reading — will see.

## 1. Read the guide once

If `myriade_guide` has not been read in this conversation, read it before the
first write: its monitoring part says which tool reads and writes each object,
and it carries the organisation's language and instructions a note follows.

## 2. Find the matter

- "My brief", "what's new", "what's waiting on me" → `myriade_brief`, with the
  person's timezone when you know it. Say when the page is yesterday's.
- Anything else → `myriade_search_workspace` with the matter's words.
- Before writing, open the alert and its topic together:
  `myriade_read(["alerts/<id>", "topics/<id>"])`.

## 3. Decide where it goes

**If an alert is open or acknowledged for this matter, what was done about it
goes on that alert** — a supplier chased, a fix planned for Thursday, who is
on it, a decision taken:

- `myriade_triage_alert` to acknowledge it with a one-sentence statement: it
  becomes the alert's headline, which the brief and the topic's reading show.
  Resolve it when the problem is gone; snooze it when the person says to wait.
- `myriade_note_alert` for a durable aside that leaves its state unchanged.

**A note on the topic** (`myriade_note_topic`) is for a fact about the whole
subject that outlives any one alert: a business rule, a planned change, a
situation the team tolerates. Where the person names the place ("on the
topic"), follow them.

When an alert and a topic both fit, the alert: the topic's reading reads its
alerts.

## 4. Write

- In the person's language, one or two sentences, with absolute dates
  ("jeudi" → "jeudi 12/11"). The note is signed by them.
- When the person asked for it, write it without asking again. When you are the
  one suggesting a write, ask first.
- A refusal (no manage access on the connection, a governed connection) is the
  rule, not an error to work around: say who can do it and give the page.

## 5. Report

Say what you wrote, on which object (its name and its page link), and the state
it is in now. One or two sentences.

Changing a check, a topic's charter or who follows it, and accepting a
proposed check, are done in the app: say so and give the page.
