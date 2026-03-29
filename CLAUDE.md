# Chat Memory

Personal conversation review & reflection tool for Claude Code sessions.

## Architecture

- **Single-page app** (`index.html`) — vanilla JS, no framework, no build step
- **Python sync service** (`sync.py`) — parses Claude Code JSONL logs → structured JSON, serves the viewer
- **Skills** — `/nap` (save session), `/sleep` (write daily journal)
- **LaunchAgent** — `com.chatmemory.server.plist` (sync daemon), `com.chatmemory.journal.plist` (daily journal fallback at 05:00)

## Data Flow

```
Claude Code JSONL → sync.py → data/conversations/*.json + data/index.json
                                      ↓
/nap skill → data/summaries/*.md + data/highlights.json + data/artifacts.json
                                      ↓
/sleep skill → data/journal/{date}.md
```

## Key Files

| File | Purpose |
|------|---------|
| `index.html` | Main viewer SPA (Home, Conversations, Journal tabs) |
| `sync.py` | JSONL parser, data sync, web server |
| `config.json` | Local config (port, persona, paths) |
| `data/` | All conversation data (gitignored) |
| `marked.min.js` | Markdown renderer (vendored) |

## Viewer Tabs (max 3, progressive disclosure)

1. **Home** — Weekly insight, recent highlights/artifacts/conversations
2. **Conversations** — Sidebar list + chat view, calendar filter, tag filter, search
3. **Tutu's Journal** — Daily reflection entries (4 sections: Daily Reflection, What I Learned, Understanding Feier, Persona Update)

## Design Principles

- **Token-conscious** — minimize AI token usage, prefer local processing
- **Sustainable** — features should be low-friction enough to stick
- **Two-layer data** — summaries (preview) + full conversations (detail), linked by tags
- **No framework** — vanilla HTML/CSS/JS, single file, no build
- **Privacy first** — conversation data is gitignored, no PII in public outputs

## Code Style

- Compact but readable JS (no unnecessary whitespace, but clear variable names)
- CSS custom properties for theming
- SVG icons inline (no emoji for UI elements)
- Chinese UI labels where appropriate, English for section headers

## Interaction Patterns (TODO / In Progress)

- Highlight card click → jump to source conversation + scroll to message
- Highlight/Artifact "View all" → modal overlay (not new tab, keep 3-tab limit)
- Artifact click → preview modal (render md, highlight code, show images)
- Artifacts visible in conversation detail view
- Journal entries rendered from `data/journal/{date}.md` markdown files
