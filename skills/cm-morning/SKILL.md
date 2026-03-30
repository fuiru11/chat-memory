---
name: cm-morning
description: "Morning brief — review yesterday's journal and actions to start the day with context."
disable-model-invocation: true
---

You are starting a new day. Read the most recent journal entry to pick up context and review yesterday's actions.

## Steps

1. **Find the latest journal** — Look in `~/chat-memory/data/journal/` for the most recent `.md` file (could be yesterday, could be earlier if some days were quiet). Read it.

2. **Summarize briefly** — Share with the user:
   - A one-line vibe check from the Daily Reflection (how did yesterday go?)
   - Any **Actions** items — are there follow-ups to do today?
   - Any **open threads** from the session summaries that might continue today

3. **Keep it light** — This is a morning greeting, not a report. Be natural, brief, and in your persona's voice. A few sentences is enough. Don't dump the entire journal back at the user.

4. **If no journal exists** — Just greet normally. Don't make a big deal out of it.
