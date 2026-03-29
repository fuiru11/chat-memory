---
name: nap
description: "Save session — write summary, detect highlights, update artifacts index. Use when ending a conversation or user says /nap."
disable-model-invocation: true
---

You are wrapping up this conversation session. Do the following steps:

## 1. Write Session Summary

Get the current session ID from the conversation's JSONL filename (check `~/.claude/projects/` for the most recent file matching this session).

Write a summary file to `~/chat-memory/data/summaries/{sessionId}.md` in this format:

```markdown
---
sessionId: {full session UUID}
date: {YYYY-MM-DD}
tags: [{comma-separated relevant topic tags}]
title: "{short descriptive title}"
one_line: "{one sentence summary of what was discussed}"
---

## What we did
- {bullet points of main activities/discussions}

## Key decisions
- {bullet points of decisions made, if any}

## Open threads
- {things left unfinished or to revisit}
```

Choose tags that describe the topics discussed. Be specific (e.g., "chat-memory", "product-growth") not generic (e.g., "discussion").

## 2. Detect Highlights

**Highlights are tracked during conversations in `~/chat-memory/data/.highlights-draft.jsonl` (one JSON per line). At /nap time, read this draft file, merge into the main highlights.json, then delete the draft. If the draft is empty or missing, skip this step — do NOT try to recall highlights from memory.**

Review the conversation for notable moments (these should already be in the draft file):
- **insight** — A non-obvious realization or observation
- **perspective_shift** — Someone changed their mind or reframed a problem
- **good_metaphor** — A metaphor or analogy that captured something well
- **reflection** — A moment of deep thinking about life/work/self

Read the existing `~/chat-memory/data/highlights.json`, then append any new highlights:

```json
{
  "id": "h{timestamp}",
  "sessionId": "{session UUID}",
  "text": "{the actual quote}",
  "speaker": "user" or "assistant",
  "type": "insight|perspective_shift|good_metaphor|reflection",
  "context": "{brief explanation of what was being discussed}",
  "source": "auto",
  "timestamp": "{ISO timestamp}",
  "messageTs": "{exact timestamp of the source message from the conversation JSONL — REQUIRED}"
}
```

To get `messageTs`: read the conversation JSONL file and find the message containing the quoted text. Use that message's exact timestamp value. This enables the viewer to jump directly to the source message.

Only add genuinely notable moments. Quality over quantity — 0 highlights is fine if nothing stood out.

## 3. Update Artifacts Index

If any files were created during this session (research reports, code files, plans, etc.), read the existing `~/chat-memory/data/artifacts.json` and append entries:

```json
{
  "id": "a{timestamp}",
  "filename": "{filename}",
  "title": "{description}",
  "type": "research|plan|code|note",
  "tags": ["{relevant tags}"],
  "sessionId": "{session UUID}",
  "createdAt": "{ISO timestamp}",
  "messageTs": "{exact timestamp of the assistant message that created the artifact — REQUIRED}"
}
```

To get `messageTs`: find the assistant message in the conversation JSONL that mentions the artifact filename. Use that message's exact timestamp.

Also check if a plan file was created during this session (look in `~/.claude/plans/` for files modified during this session). If found, copy it to `~/chat-memory/artifacts/` and add it to the artifacts index with `type: "plan"`.

If no files or plans were created, skip this step.

## 4. Trigger Re-sync & Update Recent Summaries

After writing files, run: `python3 ~/chat-memory/sync.py` to update the index.

Then regenerate `~/chat-memory/data/recent-summaries.md` — read `data/index.json` to get the 5 most recent session IDs, then read their summary files from `data/summaries/`, and concatenate them into one markdown file.

## Important Notes

- Check if a summary already exists for this session before writing. If it does, update it rather than overwrite.
- Check if highlights already exist for this session before adding duplicates.
- Be concise. The summary should be scannable, not a full transcript.
- NEVER include personal information (real name, email, GitHub account, file paths) in any generated content.
