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
- Install Claude Code skills (`/nap`, `/sleep`, `/morning`, `/weekly-retro`)
- Run the first sync of your conversations
- Optionally set up auto-start on macOS

Then open the viewer:

```bash
python3 sync.py --serve
```

## What It Does

**Conversation Viewer** — Browse past conversations with markdown rendering, search, tag filtering, and calendar navigation.

**Summaries & Tags** — AI-generated summaries and topic tags for each session. Created when you run `/nap` at the end of a conversation.

**Highlights** — Notable moments (insights, perspective shifts, good metaphors) tracked during conversations and collected at `/nap` time.

**Daily Journal** (`/sleep`) — An end-of-day reflection written by your AI persona. Covers what happened, what was learned, and what to do next.

**Morning Brief** (`/morning`) — A quick recap of yesterday's journal and open action items.

**Weekly Retro** (`/weekly-retro`) — A weekly reflection that connects themes across conversations and tracks growth over time.

## Skills

Chat Memory ships with 4 Claude Code skills that get installed to `~/.claude/skills/`:

| Skill | When to use |
|-------|------------|
| `/nap` | End of a conversation — saves summary, highlights, artifacts |
| `/sleep` | End of the day — writes your daily journal |
| `/morning` | Start of the day — reviews yesterday's journal |
| `/weekly-retro` | End of the week — writes a weekly retrospective |

These skills work out of the box with generic defaults. To make them your own, see [Customization](#customization).

## Configuration

Edit `config.json` after setup:

```json
{
  "claude_projects_dir": "~/.claude/projects",
  "project_filter": null,
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
| `port` | Local server port |
| `sync_interval` | Auto-sync interval in seconds |
| `persona_name` | Your AI persona's name (shown in journals) |
| `user_name` | Your name |

## Customization

The default skills are generic. The real power comes from personalizing them — give your AI a name, a personality, custom journal sections that match how you think.

Tell Claude Code:

> Help me customize my Chat Memory skills. I want my AI persona to be called [name] with [personality traits]. I'd like the journal sections to reflect [what matters to you].

Claude will read the skill files in `~/.claude/skills/` and help you tailor them.

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
   ├── artifacts.json          (files created)
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
