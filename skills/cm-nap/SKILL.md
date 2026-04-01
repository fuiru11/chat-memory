---
name: cm-nap
description: "Save session — write summary, detect highlights, update artifacts index. Use when ending a conversation or user says /cm-nap."
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

## 1.5. Segment the Conversation

Split this conversation into **segments** — chunks of consecutive messages about the same topic or activity. A topic shift happens when:
- The user explicitly changes subject ("ok let's move on to...", "另一个事情...")
- The discussion naturally shifts focus (e.g., from design discussion to implementation)
- There's a clear context switch (e.g., from coding to philosophical chat)

For each segment, record:
- **topic**: A short, natural name — how a user would refer to it in hindsight. Good: "wireframe 设计评审", "sync.py 时区修复", "AI 记忆 vs 人类记忆". Bad: "technical discussion", "coding", "chat".
- **summary**: 1-2 sentences of what happened and what was decided
- **startTs**: timestamp of the first message in the segment (from conversation JSONL)
- **endTs**: timestamp of the last message in the segment (from conversation JSONL)

### Guidelines
- Aim for **2-6 segments per hour** of conversation. Don't over-split.
- Short conversations (<10 messages) can be a single segment.
- Skip tool-only noise (e.g., a sequence of file reads with no discussion).

### Write segments and link to topics

1. Read existing `~/chat-memory/data/segments.json` (create as `[]` if missing).
2. Read existing `~/chat-memory/data/topics.json` (create as `{}` if missing).
3. For each new segment:
   - Check if it matches an existing topic: compare the segment's topic name against each topic's `name` and `description`. Match if they're clearly about the same evolving subject (e.g., "Viewer 点击交互" and "highlight 点击跳转" are the same topic).
   - **If match**: set `topicId` to the existing topic's id, append segment id to the topic's `segments` array, update `lastUpdated`.
   - **If no match**: create a new topic with `id: "topic-{slugified-name}"`, set `name`, `description` (one-line summary of what this topic covers), `segments: [segId]`, `lastUpdated`.
   - Prefer merging into existing topics over creating new ones.
4. Append segments to `segments.json`. Write updated `topics.json`.

### Segment data format

```json
{
  "id": "seg-{first 8 chars of sessionId}-{index}",
  "sessionId": "{session UUID}",
  "index": 0,
  "topic": "wireframe 设计评审",
  "summary": "画了 Home/Conversations/Journal 三个页面的 wireframe，确定了渐进式披露的布局",
  "startTs": "{ISO timestamp of first message}",
  "endTs": "{ISO timestamp of last message}",
  "topicId": "topic-wireframe-design"
}
```

### Topic data format

```json
{
  "topic-wireframe-design": {
    "id": "topic-wireframe-design",
    "name": "Wireframe 设计",
    "description": "Chat Memory viewer 的页面布局和交互设计",
    "segments": ["seg-d1ce14af-2"],
    "lastUpdated": "2026-03-30"
  }
}
```

## 2. Detect Highlights

**Two sources of highlights:**
1. **Draft file** — `~/chat-memory/data/.highlights-draft.jsonl` (one JSON per line), captured during conversation. If present, read and merge into highlights.json, then delete the draft.
2. **Conversation review** — Read the conversation JSONL and scan for notable moments. This is the primary source — always do this, even if the draft file exists (the draft may be incomplete).

Look for:
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
  "path": "{absolute file path — from the Write/Edit tool call's file_path parameter, or null if unknown}",
  "title": "{description}",
  "type": "research|plan|code|note",
  "tags": ["{relevant tags}"],
  "sessionId": "{session UUID}",
  "createdAt": "{ISO timestamp}",
  "messageTs": "{exact timestamp of the assistant message that created the artifact — REQUIRED}"
}
```

To get `path`: look at the Write or Edit tool calls in this conversation. The `file_path` parameter of the tool call that created or last modified this file is the path. Use the absolute path. If the file was created outside of tool calls or the path is unclear, set to `null`.

To get `messageTs`: find the assistant message in the conversation JSONL that mentions the artifact filename. Use that message's exact timestamp.

Also check if a plan file was created during this session (look in `~/.claude/plans/` for files modified during this session). If found, copy it to `~/chat-memory/artifacts/` and add it to the artifacts index with `type: "plan"` and `path` set to the artifacts/ copy path.

If no files or plans were created, skip this step.

## 4. Post-save

Run the post-save script to sync index, symlink artifacts, and regenerate recent-summaries:

```bash
python3 ~/chat-memory/refresh.py
```

## Important Notes

- Check if a summary already exists for this session before writing. If it does, update it rather than overwrite.
- Check if highlights already exist for this session before adding duplicates.
- Be concise. The summary should be scannable, not a full transcript.
- NEVER include personal information (real name, email, GitHub account, file paths) in any generated content.
