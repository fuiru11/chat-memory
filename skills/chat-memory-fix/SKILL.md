---
name: chat-memory-fix
description: "Diagnose, repair, and migrate Chat Memory data. Run when something seems wrong or after upgrading."
disable-model-invocation: true
---

You are running a health check and repair on Chat Memory data. Work through each step, report findings, and offer fixes.

## Step 1: Health Check

Read and report the following in a clear summary:

### 1a. Schema Version
Read `~/chat-memory/data/version.json`. Report current schema version. If missing, report "no version file (pre-migration)".

### 1b. Data Inventory
Count items in each data file and present as a table:

| Data | Count | Location |
|------|-------|----------|
| Sessions | N | data/index.json → sessions[] |
| Summaries | N | data/summaries/*.md |
| Highlights | N | data/highlights.json |
| Artifacts | N | data/artifacts.json |
| Segments | N | data/segments.json |
| Topics | N | data/topics.json (keys) |
| Journal entries | N | data/journal/*.md |
| Weekly insights | N | data/insights/*.md |

### 1c. Missing Summaries
Compare session IDs in `data/index.json` against files in `data/summaries/`. List any sessions without a summary file.

### 1d. Broken Artifact Paths
For each artifact in `data/artifacts.json` where `path` is not null, check if the file exists. List any broken paths.

### 1e. Missing Journals
Check dates that have sessions (from index.json) but no journal file in `data/journal/`.

### 1f. Outdated Skills
Compare installed skills in `~/.claude/skills/` against the repo versions in `~/chat-memory/skills/`. For each skill, check if the files differ. Report any that are outdated.

### 1g. Orphaned Data
Check for:
- Summary files referencing sessions not in index.json
- Segments referencing sessions not in index.json
- Highlights referencing sessions not in index.json

## Step 2: Offer Fixes

Based on findings, present a fix menu. Only show options that are relevant:

### Pending Migrations
If version < latest or version.json missing:
"Schema migration needed. Run `python3 ~/chat-memory/sync.py` to migrate."
→ Run: `python3 ~/chat-memory/sync.py`

### Broken Artifact Paths
For each artifact with a broken path:
1. Search for the file by filename in the project directory, `~/`, and `~/chat-memory/artifacts/`
2. If found at new location → update the path in artifacts.json
3. If not found → set path to null, report the file as missing

### Missing Summaries
If there are sessions without summaries:
"Found N sessions without summaries. Generate them?"
→ For each, run `/backfill {sessionId}` (process up to 10 at a time, ask before continuing if more)

### Missing Journals
If there are dates without journal entries:
"Found N days without journal entries. Generate them?"
→ For each date (chronological order), generate a journal entry using the /sleep logic:
  - Read summaries for that date's sessions
  - Write journal to `data/journal/{date}.md`

### Outdated Skills
If any installed skills differ from repo versions:
"Found N outdated skills. Update them?"
→ For each, copy the repo version to `~/.claude/skills/{skill}/SKILL.md`

### Orphaned Data
If found:
"Found orphaned data (references to deleted sessions). Clean up?"
→ Remove orphaned entries from segments.json, highlights.json, and delete orphaned summary files

## Step 3: Final Sync & Report

Run: `python3 ~/chat-memory/sync.py`

Then re-run the inventory (Step 1b) and show a before/after comparison.

## Important Notes

- Always ask before making destructive changes (deleting data, overwriting files)
- Keep a count of what was fixed for the final report
- If nothing is wrong, just say "All good! No issues found." — don't make up problems
- NEVER include personal information in output
- For large numbers of missing summaries (>10), process in batches and confirm between batches
