#!/bin/bash
# Chat Memory — One-time setup script
# Run this after cloning the repo: ./setup.sh

set -e

CHAT_MEMORY_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$CHAT_MEMORY_DIR/skills"
SKILLS_DST="$HOME/.claude/skills"

echo "=== Chat Memory Setup ==="
echo ""

# --- Check Python ---
if ! command -v python3 &>/dev/null; then
  echo "Error: Python 3 is required. Install it first."
  exit 1
fi

PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 8 ]; }; then
  echo "Error: Python 3.8+ required (found $PY_VERSION)"
  exit 1
fi
echo "[ok] Python $PY_VERSION"

# --- Check Claude Code ---
CLAUDE_BIN=""
for candidate in "$HOME/.local/bin/claude" "$HOME/.claude/local/claude" "$(command -v claude 2>/dev/null)"; do
  if [ -n "$candidate" ] && [ -x "$candidate" ]; then
    CLAUDE_BIN="$candidate"
    break
  fi
done
if [ -z "$CLAUDE_BIN" ]; then
  echo "[warn] Claude Code CLI not found — skills will be installed but cron scripts won't work until you install Claude Code"
else
  echo "[ok] Claude Code: $CLAUDE_BIN"
fi

# --- Check Claude projects dir ---
if [ ! -d "$HOME/.claude/projects" ]; then
  echo "[warn] ~/.claude/projects not found — have you used Claude Code at least once?"
fi

# --- Init config ---
if [ -f "$CHAT_MEMORY_DIR/config.json" ]; then
  echo "[ok] config.json already exists"
else
  python3 "$CHAT_MEMORY_DIR/sync.py" --init
  echo "[ok] config.json created — edit it to set persona_name and user_name"
fi

# --- Create data directories ---
mkdir -p "$CHAT_MEMORY_DIR/data/conversations"
mkdir -p "$CHAT_MEMORY_DIR/data/summaries"
mkdir -p "$CHAT_MEMORY_DIR/data/journal"
mkdir -p "$CHAT_MEMORY_DIR/data/insights"
mkdir -p "$CHAT_MEMORY_DIR/artifacts"
echo "[ok] Data directories ready"

# --- Install skills ---
mkdir -p "$SKILLS_DST"
SKILLS_INSTALLED=0
for skill in nap sleep morning weekly-retro backfill chat-memory-fix; do
  src="$SKILLS_SRC/$skill/SKILL.md"
  dst="$SKILLS_DST/$skill/SKILL.md"
  if [ ! -f "$src" ]; then
    echo "[warn] Skill template not found: $src"
    continue
  fi
  if [ -f "$dst" ]; then
    if ! diff -q "$src" "$dst" >/dev/null 2>&1; then
      echo "[update] Skill '$skill' has a newer version"
      cp "$src" "$dst"
      SKILLS_INSTALLED=$((SKILLS_INSTALLED + 1))
    else
      echo "[ok] Skill '$skill' is up to date"
    fi
  else
    mkdir -p "$SKILLS_DST/$skill"
    cp "$src" "$dst"
    echo "[ok] Installed skill: $skill"
    SKILLS_INSTALLED=$((SKILLS_INSTALLED + 1))
  fi
done

# --- Generate cron helper scripts ---
if [ -n "$CLAUDE_BIN" ]; then
  cat > "$CHAT_MEMORY_DIR/daily-journal.sh" << SCRIPT
#!/bin/bash
# Daily journal fallback — runs at 05:00 via launchd
TODAY=\$(date +%Y-%m-%d)
JOURNAL_FILE="$CHAT_MEMORY_DIR/data/journal/\${TODAY}.md"
LOG_FILE="$CHAT_MEMORY_DIR/journal-cron.log"
log() { echo "[\$(date '+%Y-%m-%d %H:%M:%S')] \$1" >> "\$LOG_FILE"; }
if [ -f "\$JOURNAL_FILE" ]; then log "Journal for \${TODAY} already exists, skipping."; exit 0; fi
if ! grep -q "\"\${TODAY}\"" "$CHAT_MEMORY_DIR/data/index.json" 2>/dev/null; then log "No sessions for \${TODAY}, skipping."; exit 0; fi
log "Generating journal for \${TODAY}..."
cd "\$HOME"
$CLAUDE_BIN -p "/sleep" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>> "\$LOG_FILE"
[ -f "\$JOURNAL_FILE" ] && log "Journal generated." || log "WARNING: journal not created."
SCRIPT
  chmod +x "$CHAT_MEMORY_DIR/daily-journal.sh"

  cat > "$CHAT_MEMORY_DIR/weekly-retro.sh" << SCRIPT
#!/bin/bash
# Weekly retro fallback — runs Friday via launchd
FRIDAY=\$(date +%Y-%m-%d)
INSIGHT_FILE="$CHAT_MEMORY_DIR/data/insights/\${FRIDAY}.md"
LOG_FILE="$CHAT_MEMORY_DIR/journal-cron.log"
log() { echo "[\$(date '+%Y-%m-%d %H:%M:%S')] [weekly] \$1" >> "\$LOG_FILE"; }
if [ -f "\$INSIGHT_FILE" ]; then log "Weekly insight for \${FRIDAY} already exists, skipping."; exit 0; fi
if [ ! -f "$CHAT_MEMORY_DIR/data/index.json" ]; then log "No index.json, skipping."; exit 0; fi
log "Generating weekly retro for \${FRIDAY}..."
cd "\$HOME"
$CLAUDE_BIN -p "/weekly-retro" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>> "\$LOG_FILE"
[ -f "\$INSIGHT_FILE" ] && log "Weekly insight generated." || log "WARNING: insight not created."
SCRIPT
  chmod +x "$CHAT_MEMORY_DIR/weekly-retro.sh"
  echo "[ok] Cron helper scripts generated"
fi

# --- First sync ---
echo ""
echo "Running first sync..."
python3 "$CHAT_MEMORY_DIR/sync.py"

# --- Optional: Backfill summaries ---
if [ -n "$CLAUDE_BIN" ]; then
  SESSION_COUNT=$(python3 -c "
import json, os
idx_path = os.path.join('$CHAT_MEMORY_DIR', 'data', 'index.json')
if os.path.exists(idx_path):
    idx = json.load(open(idx_path))
    print(len(idx.get('sessions', [])))
else:
    print(0)
" 2>/dev/null || echo "0")

  if [ "$SESSION_COUNT" -gt 0 ]; then
    echo ""
    echo "Found $SESSION_COUNT sessions. Generate summaries for recent ones?"
    echo "  This uses Claude to analyze conversations and create summaries,"
    echo "  highlights, and topic segments — making the viewer much more useful."
    echo ""
    echo "  [1] Last 5 sessions (recommended)"
    echo "  [2] Last 1 day"
    echo "  [3] Custom number"
    echo "  [4] Skip"
    read -p "Choice [1-4]: " BACKFILL_CHOICE
    echo

    if [ "$BACKFILL_CHOICE" != "4" ]; then
      # Determine how many sessions
      BACKFILL_N=5
      if [ "$BACKFILL_CHOICE" = "2" ]; then
        BACKFILL_N="1d"
      elif [ "$BACKFILL_CHOICE" = "3" ]; then
        read -p "How many recent sessions? " BACKFILL_N
      fi

      # Get session IDs
      BACKFILL_IDS=$(python3 -c "
import json, os
from datetime import datetime, timedelta
idx_path = os.path.join('$CHAT_MEMORY_DIR', 'data', 'index.json')
idx = json.load(open(idx_path))
sessions = idx.get('sessions', [])
n = '$BACKFILL_N'
if n == '1d':
    cutoff = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'
    selected = [s for s in sessions if s.get('startTime', '') >= cutoff]
else:
    selected = sessions[:int(n)]
for s in selected:
    print(s['id'])
" 2>/dev/null)

      if [ -n "$BACKFILL_IDS" ]; then
        BACKFILL_COUNT=$(echo "$BACKFILL_IDS" | wc -l | tr -d ' ')
        echo "Generating summaries for $BACKFILL_COUNT sessions..."
        for SID in $BACKFILL_IDS; do
          SHORT_ID=$(echo "$SID" | cut -c1-8)
          echo "  Processing $SHORT_ID..."
          $CLAUDE_BIN -p "/backfill $SID" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>/dev/null
        done
        echo "[ok] Backfill complete"

        # Offer journal generation
        echo ""
        read -p "Generate journal entries for these days? (Y/n) " JOURNAL_CHOICE
        echo
        if [[ ! "$JOURNAL_CHOICE" =~ ^[Nn]$ ]]; then
          DATES=$(python3 -c "
import json, os
idx_path = os.path.join('$CHAT_MEMORY_DIR', 'data', 'index.json')
idx = json.load(open(idx_path))
backfill_ids = set('''$BACKFILL_IDS'''.split())
dates = set()
for s in idx['sessions']:
    if s['id'] in backfill_ids and s.get('date'):
        dates.add(s['date'])
for d in sorted(dates):
    print(d)
" 2>/dev/null)
          for DATE in $DATES; do
            if [ ! -f "$CHAT_MEMORY_DIR/data/journal/$DATE.md" ]; then
              echo "  Writing journal for $DATE..."
              $CLAUDE_BIN -p "/sleep" --allowedTools "Bash,Read,Write,Edit,Glob,Grep" 2>/dev/null
            else
              echo "  [skip] Journal for $DATE already exists"
            fi
          done
          echo "[ok] Journals generated"
        fi
      fi
    else
      echo "[skip] No backfill — you can run /backfill later in Claude Code"
    fi
  fi
fi

# --- Optional: macOS LaunchAgent ---
echo ""
if [ "$(uname)" = "Darwin" ]; then
  read -p "Install as macOS auto-start service? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 "$CHAT_MEMORY_DIR/sync.py" --install
    echo "[ok] LaunchAgent installed"
  else
    echo "[skip] No auto-start — run manually: python3 sync.py --serve"
  fi
fi

# --- Done ---
echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit config.json to set your persona_name and user_name"
echo "  2. Start the viewer: python3 sync.py --serve"
echo "  3. In Claude Code, try: /nap, /morning, /sleep"
echo ""
echo "To personalize your skills, tell Claude:"
echo '  "Help me customize my Chat Memory skills in ~/.claude/skills/"'
