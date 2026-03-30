# Chat Memory

A local tool for browsing, reflecting on, and learning from your Claude Code conversations.

Chat Memory syncs your Claude Code conversation logs into a clean web viewer, and adds AI-powered journaling — daily reflections, weekly retrospectives, and highlight tracking — so your conversations compound into lasting knowledge.

<!-- TODO: screenshot -->

## Quick Start

```bash
git clone https://github.com/YOUR-USERNAME/chat-memory.git
cd chat-memory
chmod +x setup.sh && ./setup.sh
```

The setup script will:
- Create your config and data directories
- Install Claude Code skills (`/cm-nap`, `/cm-sleep`, `/cm-morning`, `/cm-weekly-retro`)
- Run the first sync of your conversations
- Optionally set up auto-start on macOS

Then open the viewer:

```bash
python3 sync.py --serve
```

## Upgrading

```bash
cd chat-memory
git pull
python3 sync.py
```

Migrations run automatically on startup. If you see `Running migration vN → vN+1...`, that's normal — your data is being updated to the latest format.

If something seems wrong after upgrading, run `/cm-fix` in Claude Code.

## What It Does

**Conversation Viewer** — Browse past conversations with markdown rendering, search, tag filtering, and calendar navigation.

**Summaries & Tags** — AI-generated summaries and topic tags for each session. Created when you run `/cm-nap` at the end of a conversation.

**Highlights** — Notable moments (insights, perspective shifts, good metaphors) tracked during conversations and collected at `/cm-nap` time.

**Daily Journal** (`/cm-sleep`) — An end-of-day reflection written by your AI persona. Covers what happened, what was learned, and what to do next.

**Morning Brief** (`/cm-morning`) — A quick recap of yesterday's journal and open action items.

**Weekly Retro** (`/cm-weekly-retro`) — A weekly reflection that connects themes across conversations and tracks growth over time.

## Skills

Chat Memory ships with 4 Claude Code skills that get installed to `~/.claude/skills/`:

| Skill | When to use |
|-------|------------|
| `/cm-nap` | End of a conversation — saves summary, highlights, artifacts |
| `/cm-sleep` | End of the day — writes your daily journal |
| `/cm-morning` | Start of the day — reviews yesterday's journal |
| `/cm-weekly-retro` | End of the week — writes a weekly retrospective |
| `/cm-backfill` | Generate summaries for historical sessions (e.g., `/cm-backfill abc123`) |
| `/cm-fix` | Diagnose and repair data issues, run migrations |

These skills work out of the box with generic defaults. To make them your own, see [Customization](#customization).

## Configuration

Edit `config.json` after setup:

```json
{
  "claude_projects_dir": "~/.claude/projects",
  "project_filter": null,
  "project_exclude": null,
  "port": 8787,
  "sync_interval": 300,
  "persona_name": "Claude",
  "user_name": "User"
}
```

| Field | Description |
|-------|------------|
| `claude_projects_dir` | Path to Claude Code's project data |
| `project_filter` | Only sync projects matching this string (`null` = all) |
| `project_exclude` | Exclude projects matching this string or array of strings (`null` = none) |
| `port` | Local server port |
| `sync_interval` | Auto-sync interval in seconds |
| `persona_name` | Your AI persona's name (shown in journals) |
| `user_name` | Your name |

## Customization

The default skills are generic. The real power comes from personalizing them — give your AI a name, a personality, custom journal sections that match how you think.

Tell Claude Code:

> Help me customize my Chat Memory skills. I want my AI persona to be called [name] with [personality traits]. I'd like the journal sections to reflect [what matters to you].

Claude will read the skill files in `~/.claude/skills/` and help you tailor them.

## Connecting to Your Sessions

After setup, Claude Code doesn't automatically know your Chat Memory data exists. To give it context continuity across sessions, add these two things:

### 1. CLAUDE.md — startup reading list

Add this to your project or user-level `CLAUDE.md`:

```markdown
## Session Startup

On session start, read these files for context:
1. Latest journal entry from `~/chat-memory/data/journal/` (most recent file)
2. First entry in `~/chat-memory/data/recent-summaries.md` (last session summary)
```

This costs ~2-3k tokens per session — negligible compared to a typical conversation.

### 2. Memory reference — data map

Create a memory file at `~/.claude/projects/YOUR-PROJECT/memory/reference_chat_memory.md`:

```markdown
---
name: Chat Memory Data Guide
description: Where Chat Memory data lives, what each file does, and when to read it
type: reference
---

| File | Location | Purpose | When to read |
|------|----------|---------|--------------|
| Journal | ~/chat-memory/data/journal/{date}.md | Daily reflection & action items | Session start (latest) |
| Summaries | ~/chat-memory/data/recent-summaries.md | Last 5 session summaries | Session start (first entry) |
| Index | ~/chat-memory/data/index.json | All session index | When searching history |
| Highlights | ~/chat-memory/data/.highlights-draft.jsonl | In-progress highlight drafts | During /cm-nap |
| Segments | ~/chat-memory/data/segments.json | Searchable conversation fragments | When searching past content |
| Topics | ~/chat-memory/data/topics.json | Cross-session topic threads | When tracing a topic over time |
```

Then add a line to your `MEMORY.md` index pointing to this file.

## Commands

```bash
python3 sync.py              # Sync conversations
python3 sync.py --serve      # Sync + start server + open browser
python3 sync.py --daemon     # Sync + start server (no browser, for auto-start)
python3 sync.py --init       # Create default config.json
python3 sync.py --install    # Install as macOS auto-start service
python3 sync.py --uninstall  # Remove auto-start service
```

## Auto-Start (macOS)

To run Chat Memory automatically on login:

```bash
python3 sync.py --install
```

This creates a LaunchAgent that keeps the server running and auto-syncs in the background. The setup script offers this as an option during install.

## Architecture

```
Claude Code JSONL logs
        |
    sync.py (parse + clean)
        |
   data/ directory
   ├── conversations/*.json    (full messages)
   ├── summaries/*.md          (AI summaries)
   ├── highlights.json         (notable moments)
   ├── artifacts.json          (files created, with paths)
   ├── segments.json           (searchable conversation chunks)
   ├── topics.json             (cross-session topic threads)
   ├── version.json            (schema version for migrations)
   ├── journal/*.md            (daily reflections)
   └── insights/*.md           (weekly retros)
        |
   index.html (web viewer)
   ├── Home        — weekly insight, recent highlights
   ├── Conversations — browse, search, filter
   └── Journal     — daily + weekly reflections
```

## Requirements

- Python 3.8+ (stdlib only, no pip install needed)
- Claude Code (for conversation logs and skills)
- A modern browser

## Privacy

All data stays on your machine. The `.gitignore` excludes personal data (`data/`, `artifacts/`, `config.json`) so you can safely push without exposing conversations.

## License

MIT
