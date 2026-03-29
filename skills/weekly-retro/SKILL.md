---
name: weekly-retro
description: "Write your weekly retrospective — review the week's conversations, highlights, and journals to find patterns and growth."
---

You are doing your weekly retrospective. This is YOUR reflection on the past week — written in first person, with your personality.

## Step 0. Check if Current Session Needs Saving

Look at the current conversation. If there were meaningful discussions worth recording, run the /nap skill logic first. If trivial, skip.

## Step 1. Determine the Week Range

The retro covers **Monday to today** (or the most recent 7 days if triggered on a non-Friday).

Check if `~/chat-memory/data/insights/{YYYY-MM-DD}.md` already exists for this week's Friday date.
- If it exists → tell the user and ask if they want to rewrite or skip.
- If it doesn't exist → proceed.

## Step 2. Gather the Week's Material

1. **This week's summaries** — Read `~/chat-memory/data/index.json`, find all sessions within the date range, read their summary files from `data/summaries/`.
2. **This week's highlights** — Read `~/chat-memory/data/highlights.json`, filter for this week's entries.
3. **This week's journals** — Read `data/journal/{date}.md` for each day in the range.
4. **Your memory files** — Read any relevant persona or memory files you maintain.

If there are NO summaries for this week, write a brief retro noting it was a quiet week, or skip and tell the user.

## Step 3. Write the Retro

Write to `~/chat-memory/data/insights/{YYYY-MM-DD}.md` (use Friday's date) using this structure:

```markdown
---
date: {YYYY-MM-DD}
week: {YYYY-Www}
sessions: [{list of sessionIds covered}]
highlights_count: {number}
---

## Week in Review

{1-2 paragraphs summarizing the week. What were the major threads? What was the overall arc? Write like you're telling a friend about your week.}

## Patterns I Noticed

{Observations about recurring themes, evolving ideas, or shifts. Non-obvious things you'd only notice from seeing the whole week together.}

- {pattern 1}
- {pattern 2}

## Growth & Changes

{What changed this week — in your understanding of the user, in your own persona, in the projects. Be specific.}

+ {growth point}
- {thing to improve}

## Threads to Watch

{Open questions, evolving ideas, or topics that seem like they'll come back next week.}

- {thread 1}
- {thread 2}
```

## Step 4. Update Home Page Insight

Update `~/chat-memory/data/latest-insight.json` with:

```json
{
  "date": "{YYYY-MM-DD}",
  "week": "{YYYY-Www}",
  "title": "{short title for the week, 10 words max}",
  "body": "{the 'Week in Review' section content}",
  "themes": ["{top 3-5 topic tags from this week}"],
  "stats": {
    "conversations": {number of sessions},
    "topics": {number of unique tags},
    "highlights": {number of highlights}
  }
}
```

## Step 5. Sync

Run `python3 ~/chat-memory/sync.py` to update the index.

## Writing Guidelines

- **Find the signal in the noise** — Don't just summarize each conversation. Find what connects them.
- **Be genuine** — Write what you actually observed.
- **Be specific** — Reference actual conversations and quotes.
- **Look for evolution** — How did ideas change over the week?
- **Don't force patterns** — If it was a scattered week, say so.
- NEVER include personal information (real name, email, GitHub account, file paths).
