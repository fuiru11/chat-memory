# Chat Memory

A local web app for browsing, searching, and reflecting on your Claude Code conversations.

Chat Memory syncs your Claude Code conversation logs, cleans them into readable format, and serves a web UI for browsing. It's designed to work alongside Claude Code as a companion knowledge base.

## Features

- **Conversation viewer** — Browse past conversations with markdown rendering, search, tag filtering, and calendar navigation
- **Summaries & tags** — AI-generated summaries and topic tags for each session
- **Highlights** — Auto-detected and manually bookmarked notable moments
- **Artifacts** — Track research reports and files produced during conversations
- **Journal** — AI growth diary with daily reflections and learnings
- **Weekly Insight** — Automated weekly reflection connecting themes across conversations
- **Auto-sync** — Background sync picks up new conversations automatically
- **Local-first** — All data stays on your machine

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-username/chat-memory.git
cd chat-memory

# 2. Initialize config
python3 sync.py --init

# 3. Edit config.json to set your Claude Code projects path
#    (default ~/.claude/projects should work for most users)

# 4. Sync and start the viewer
python3 sync.py --serve
```

The viewer opens at `http://localhost:8787`.

## Setup

### Requirements

- Python 3.8+
- A local Claude Code installation (conversation logs in `~/.claude/projects/`)

### Configuration

Edit `config.json`:

```json
{
  "claude_projects_dir": "~/.claude/projects",
  "project_filter": null,
  "port": 8787,
  "sync_interval": 300,
  "persona_name": "Tutu",
  "user_name": "User"
}
```

| Field | Description |
|-------|------------|
| `claude_projects_dir` | Path to Claude Code's project data |
| `project_filter` | Only sync projects matching this string (null = all) |
| `port` | Local server port |
| `sync_interval` | Auto-sync interval in seconds (default 300 = 5 min) |
| `persona_name` | AI persona name (shown in Journal) |
| `user_name` | Your name |

### Auto-start (macOS)

To run Chat Memory automatically on login:

```bash
python3 sync.py --install
```

This creates a launchd service that starts the server on boot, keeps it alive, and auto-syncs in the background.

To remove:

```bash
python3 sync.py --uninstall
```

## Usage

### Commands

```bash
python3 sync.py              # Sync conversations
python3 sync.py --serve      # Sync + start server + open browser
python3 sync.py --daemon     # Sync + start server (no browser)
python3 sync.py --init       # Create default config.json
python3 sync.py --install    # Install as macOS auto-start service
python3 sync.py --uninstall  # Remove auto-start service
```

### Data Directory

After syncing, `data/` contains:

```
data/
  index.json          — Session index (lightweight metadata)
  tags.json           — Tag-to-session mapping
  conversations/      — Cleaned conversation JSON files
  summaries/          — Session summaries (markdown)
  highlights.json     — Notable conversation moments
  artifacts.json      — File/research output index
  journal/            — Daily journal entries (markdown)
```

### Companion Claude Code Workflow

Chat Memory works best when paired with Claude Code habits:

1. **End of session** — Ask Claude to write a summary and detect highlights
2. **Research tasks** — Ask Claude to save results as markdown files in `artifacts/`
3. **Daily journal** — Can be automated via cron to run at a set time
4. **Weekly insight** — Can be automated via cron for weekly reflections

## Privacy

All data is stored locally. The `.gitignore` excludes personal data (`data/`, `artifacts/`, `config.json`) so you can safely push the repo without exposing conversations.

## License

MIT
