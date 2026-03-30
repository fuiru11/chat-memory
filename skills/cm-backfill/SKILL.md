---
name: cm-backfill
description: "Generate summary, highlights, segments, topics, and artifacts for historical sessions. Use after setup or to fill gaps."
disable-model-invocation: true
---

You are generating retrospective data for historical conversation sessions that were not processed with `/cm-nap` at the time.

## Input

You will be given one or more session IDs (space-separated after the skill name, e.g., `/cm-backfill abc123 def456`). If no IDs are given, report an error and stop.

## For Each Session

Process sessions one at a time, reporting progress.

### Step 0: Check if Already Processed

Check if `~/chat-memory/data/summaries/{sessionId}.md` exists with proper frontmatter.
- If yes → print "Session {sessionId}: already has summary, skipping" and move to next.
- If no → proceed.

### Step 1: Read the Conversation

Read `~/chat-memory/data/conversations/{sessionId}.json`. If the file doesn't exist, print an error and skip this session.

### Step 2: Write Summary

Write to `~/chat-memory/data/summaries/{sessionId}.md`:

```markdown
---
sessionId: {full session UUID}
date: {YYYY-MM-DD, from the conversation's startTime}
tags: [{comma-separated relevant topic tags}]
title: "{short descriptive title}"
one_line: "{one sentence summary}"
---

## What we did
- {bullet points}

## Key decisions
- {bullet points, if any}

## Open threads
- {things left unfinished}
```

### Step 3: Segment the Conversation

Split into segments (chunks about the same topic). Same rules as /cm-nap:
- 2-6 segments per hour. Short conversations can be a single segment.
- Each segment: topic name, summary, startTs, endTs.

Read existing `~/chat-memory/data/segments.json` and `~/chat-memory/data/topics.json`. Append new segments, match or create topics.

Segment format:
```json
{
  "id": "seg-{first 8 chars of sessionId}-{index}",
  "sessionId": "{session UUID}",
  "index": 0,
  "topic": "{natural topic name}",
  "summary": "{1-2 sentences}",
  "startTs": "{ISO timestamp}",
  "endTs": "{ISO timestamp}",
  "topicId": "topic-{slugified-name}"
}
```

Topic format:
```json
{
  "topic-{slug}": {
    "id": "topic-{slug}",
    "name": "{topic name}",
    "description": "{one-line description}",
    "segments": ["seg-id"],
    "lastUpdated": "{YYYY-MM-DD}"
  }
}
```

### Step 4: Extract Highlights

Scan the conversation text for genuinely notable moments:
- **insight** — Non-obvious realizations
- **perspective_shift** — Someone changed their mind or reframed a problem
- **good_metaphor** — Metaphors that captured something well
- **reflection** — Deep thinking about life/work/self

Be conservative — only add truly standout moments. 0 highlights is fine.

Read existing `~/chat-memory/data/highlights.json`, append:
```json
{
  "id": "h{date}{letter}",
  "sessionId": "{session UUID}",
  "text": "{exact quote from conversation}",
  "speaker": "user|assistant",
  "type": "insight|perspective_shift|good_metaphor|reflection",
  "context": "{brief explanation}",
  "source": "backfill",
  "timestamp": "{ISO timestamp of the message}",
  "messageTs": "{exact timestamp from conversation message — REQUIRED}"
}
```

### Step 5: Extract Artifacts

Check the conversation messages for Write/Edit tool calls that created files. For each file created:

Read existing `~/chat-memory/data/artifacts.json`, append:
```json
{
  "id": "a{date}{letter}",
  "filename": "{filename}",
  "path": "{absolute file path from the tool call, or null}",
  "title": "{description}",
  "type": "research|plan|code|note|design",
  "tags": ["{relevant tags}"],
  "sessionId": "{session UUID}",
  "createdAt": "{ISO timestamp}",
  "messageTs": "{exact timestamp of the message}"
}
```

To find artifacts: look for messages with `tools` array containing "Write" or "Edit". The surrounding text usually mentions the filename. For the `path`, check if the file still exists at the original location.

Skip config files, temporary files, and minor edits. Only record meaningful outputs.

### Step 6: Sync

After processing all sessions, run:
```bash
python3 ~/chat-memory/sync.py
```

Then regenerate `~/chat-memory/data/recent-summaries.md` — read `data/index.json` for the 5 most recent session IDs, read their summaries, and concatenate.

## Important Notes

- Do NOT overwrite existing summaries. Skip sessions that already have one.
- Do NOT duplicate highlights or artifacts that already exist for a session.
- Be concise. Summaries should be scannable.
- NEVER include personal information (real name, email, GitHub account) in generated content.
- Mark highlight source as `"backfill"` (not `"auto"`) to distinguish from real-time captures.
