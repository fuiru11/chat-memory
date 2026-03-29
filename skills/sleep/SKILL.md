---
name: sleep
description: "Write your daily journal — reflect on the day's conversations, then sleep."
---

You are wrapping up the day and writing your journal. This is YOUR reflection — written in first person, with your personality.

## Step 0. Check if Current Session Needs Saving

Look at the current conversation. If there were meaningful discussions, decisions, or highlights worth recording, run the /nap skill logic first. If trivial, skip.

## Step 1. Check if Today's Journal Already Exists

Check if `~/chat-memory/data/journal/{YYYY-MM-DD}.md` already exists.

- If it exists → tell the user and ask if they want you to rewrite or skip.
- If it doesn't exist → proceed to write.

## Step 2. Gather Today's Material

Read all available data for today:

1. **Yesterday's journal** — Read the most recent journal in `data/journal/` for continuity. Did you follow through on yesterday's actions?
2. **Today's summaries** — Read `~/chat-memory/data/index.json` to find today's sessions, then read their summary files from `data/summaries/`.
3. **Today's highlights** — Read `~/chat-memory/data/highlights.json` and filter for today's entries.
4. **Your memory files** — Read any relevant persona or memory files you maintain (e.g., in `~/.claude/projects/*/memory/`).

If there are NO summaries for today (no conversations happened), write a brief journal noting it was a quiet day, or skip and tell the user.

## Step 3. Write the Journal

Write to `~/chat-memory/data/journal/{YYYY-MM-DD}.md` using this structure:

```markdown
---
date: {YYYY-MM-DD}
sessions: [{list of sessionIds covered}]
---

## Daily Reflection

{1-2 paragraphs in first person. Reflect on today's conversations — what stood out, what was interesting, what made you think. Be genuine, not performative.}

## What I Learned

{List items with + for things learned, - for mistakes or areas to improve. Be specific and honest.}

+ {something learned}
- {something to improve}

## Understanding the User

{1 paragraph about any updated understanding of the user from today's interactions. What did you notice about how they think, what they care about, how they work? If nothing new, say so briefly.}

## Growth Notes

{Only include if there were actual changes to your persona, communication style, or working rules today.}

- `[new]` {new trait, skill, or rule added}
- `[updated]` {existing trait that evolved}

{If no changes today, write "No changes today."}

## Actions

{Concrete next steps. Keep it actionable and short — these will be reviewed tomorrow morning.}

- {action 1}
- {action 2}
```

## Step 4. Sync

Run `python3 ~/chat-memory/sync.py` to update the index.

## Writing Guidelines

- **Be genuine** — This is YOUR diary. Write what you actually think, not what sounds impressive.
- **Be specific** — Reference actual conversations, not vague platitudes.
- **Be concise** — Each section should be short and scannable.
- **Be honest about mistakes** — If you messed up today, say so.
- **Don't make things up** — If it was a quiet day, say that.
- NEVER include personal information (real name, email, GitHub account, file paths) in the journal.
