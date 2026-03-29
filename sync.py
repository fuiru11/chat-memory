#!/usr/bin/env python3
"""
Chat Memory — Sync & Serve
Syncs Claude Code JSONL conversation logs into clean JSON for the viewer.

Usage:
  python3 sync.py              # Sync data
  python3 sync.py --serve      # Sync + start server + open browser
  python3 sync.py --daemon     # Sync + start server (no browser, for launchd)
  python3 sync.py --init       # Create default config.json
  python3 sync.py --install    # Install as macOS auto-start service
  python3 sync.py --uninstall  # Remove auto-start service
"""

import json
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "config.json"
DATA_DIR = BASE_DIR / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
SUMMARIES_DIR = DATA_DIR / "summaries"
JOURNAL_DIR = DATA_DIR / "journal"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
PLIST_NAME = "com.chatmemory.server"


# ===== Config =====

def load_config():
    if not CONFIG_FILE.exists():
        print("config.json not found. Run: python3 sync.py --init")
        sys.exit(1)
    try:
        config = json.loads(CONFIG_FILE.read_text())
    except json.JSONDecodeError as e:
        print(f"Error reading config.json: {e}")
        sys.exit(1)
    config["claude_projects_dir"] = Path(
        os.path.expanduser(config.get("claude_projects_dir", "~/.claude/projects"))
    )
    return config


def init_config():
    if CONFIG_FILE.exists():
        print("config.json already exists.")
        return
    default = {
        "claude_projects_dir": "~/.claude/projects",
        "project_filter": None,
        "port": 8787,
        "sync_interval": 300,
        "persona_name": "Claude",
        "user_name": "User",
    }
    CONFIG_FILE.write_text(json.dumps(default, indent=2, ensure_ascii=False))
    print(f"Created {CONFIG_FILE}")
    print("Edit it to set your preferences, then run: python3 sync.py --serve")


def utc_to_local_date(ts):
    """Convert UTC ISO timestamp to local date string (YYYY-MM-DD)."""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%Y-%m-%d")
    except Exception:
        return ts[:10] if ts else ""


# ===== JSONL Parsing =====

def is_system_message(content):
    if isinstance(content, str):
        text = content.strip()
        return any(text.startswith(t) for t in [
            "<command-name>", "<local-command-", "<system-reminder>",
            "[Request interrupted", "[Response interrupted",
        ])
    elif isinstance(content, list):
        has_human_text = False
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "tool_result":
                    continue
                if block.get("type") == "text":
                    text = block.get("text", "").strip()
                    if text and not any(text.startswith(t) for t in [
                        "<command-name>", "<local-command-", "<system-reminder>"
                    ]):
                        has_human_text = True
            elif isinstance(block, str):
                has_human_text = True
        return not has_human_text
    return False


SKIP_TEXTS = {"[Request interrupted by user]", "[Response interrupted by user]",
               "[Request interrupted]", "[Response interrupted]"}

def extract_user_text(content):
    if isinstance(content, str):
        text = re.sub(r'<[^>]+>.*?</[^>]+>', '', content, flags=re.DOTALL)
        text = re.sub(r'<[^>]+/>', '', text)
        text = text.strip()
        if text in SKIP_TEXTS:
            return ""
        return text
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "").strip()
                if text and not any(text.startswith(t) for t in [
                    "<command-name>", "<local-command-", "<system-reminder>"
                ]):
                    cleaned = re.sub(
                        r'<system-reminder>.*?</system-reminder>', '',
                        text, flags=re.DOTALL
                    ).strip()
                    if cleaned and cleaned not in SKIP_TEXTS:
                        parts.append(cleaned)
            elif isinstance(block, str):
                parts.append(block)
        return "\n".join(parts)
    return ""


def extract_assistant_content(content):
    text_parts = []
    tools = []
    if isinstance(content, str):
        return content, []
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            bt = block.get("type", "")
            if bt == "text":
                t = block.get("text", "").strip()
                if t:
                    text_parts.append(t)
            elif bt == "tool_use":
                name = block.get("name", "")
                if name and name not in tools:
                    tools.append(name)
    return "\n\n".join(text_parts), tools


def parse_jsonl(filepath):
    messages = []
    session_id = None
    slug = None

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if record.get("type") in ("file-history-snapshot", "system"):
                    continue

                if not session_id and record.get("sessionId"):
                    session_id = record["sessionId"]
                if not slug and record.get("slug"):
                    slug = record["slug"]

                msg = record.get("message", {})
                role = msg.get("role", "")
                content = msg.get("content", "")
                timestamp = record.get("timestamp", "")

                if role == "user":
                    if record.get("isMeta") or is_system_message(content):
                        continue
                    text = extract_user_text(content)
                    if not text:
                        continue
                    messages.append({
                        "role": "user",
                        "text": text,
                        "timestamp": timestamp,
                    })
                elif role == "assistant":
                    text, tools = extract_assistant_content(content)
                    if not text:
                        continue
                    m = {"role": "assistant", "text": text, "timestamp": timestamp}
                    if tools:
                        m["tools"] = tools
                    messages.append(m)
    except Exception as e:
        print(f"  Error parsing {filepath.name}: {e}")
        return None

    if not messages:
        return None

    return {
        "sessionId": session_id or filepath.stem,
        "slug": slug,
        "startTime": messages[0]["timestamp"],
        "endTime": messages[-1]["timestamp"],
        "messageCount": len(messages),
        "messages": messages,
    }


# ===== Summary & Index =====

def load_summary(sid):
    f = SUMMARIES_DIR / f"{sid}.md"
    if not f.exists():
        return None
    try:
        text = f.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    fm = {}
    for line in parts[1].strip().split("\n"):
        if ":" in line:
            k, v = line.split(":", 1)
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if v.startswith("[") and v.endswith("]"):
                v = [t.strip().strip('"').strip("'")
                     for t in v[1:-1].split(",") if t.strip()]
            fm[k] = v
    return fm


def auto_summary(conv):
    first_msg = ""
    for m in conv["messages"]:
        if m["role"] == "user":
            first_msg = m["text"][:60]
            break
    return {
        "sessionId": conv["sessionId"],
        "date": utc_to_local_date(conv["startTime"]) if conv["startTime"] else "",
        "tags": [],
        "title": first_msg or "Untitled",
        "one_line": first_msg or "",
    }


def session_id_to_filename(session_id):
    return session_id


# ===== Sync =====

def load_state():
    f = DATA_DIR / "sync-state.json"
    if f.exists():
        try:
            return json.loads(f.read_text())
        except Exception:
            return {"lastSync": None, "files": {}}
    return {"lastSync": None, "files": {}}


def save_state(state):
    state["lastSync"] = datetime.utcnow().isoformat() + "Z"
    (DATA_DIR / "sync-state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2))


def load_deleted():
    f = DATA_DIR / "deleted.json"
    if f.exists():
        try:
            return set(json.loads(f.read_text()))
        except Exception:
            return set()
    return set()


def save_deleted(deleted):
    (DATA_DIR / "deleted.json").write_text(
        json.dumps(sorted(deleted), ensure_ascii=False))


def extract_project_name(project_dir_name):
    """Extract readable project name from Claude Code's directory naming.
    Claude Code encodes paths as: -Users-name-path-to-project
    e.g. '-Users-alice' -> '' (home dir)
         '-Users-alice-my-project' -> 'my-project'
         '-Users-alice-work-repo' -> 'work-repo'
    """
    # Decode: replace leading dash, split by path separator pattern
    # The dir name is the cwd path with / replaced by -
    name = project_dir_name.lstrip("-")
    parts = name.split("-")
    # Find home dir end: Users-{username} or home-{username}
    try:
        if "Users" in parts:
            idx = parts.index("Users") + 2  # skip Users + username
        elif "home" in parts:
            idx = parts.index("home") + 2
        else:
            idx = 0
        remainder = parts[idx:]
        return "-".join(remainder) if remainder else ""
    except (ValueError, IndexError):
        return name


def find_jsonl_files(config):
    projects_dir = config["claude_projects_dir"]
    project_filter = config.get("project_filter")
    files = []
    if not projects_dir.exists():
        print(f"  Warning: {projects_dir} does not exist")
        return files
    for pdir in projects_dir.iterdir():
        if not pdir.is_dir():
            continue
        if project_filter and project_filter not in pdir.name:
            continue
        project_name = extract_project_name(pdir.name)
        for jf in pdir.glob("*.jsonl"):
            files.append((jf, project_name))
    return files


def sync(config, quiet=False):
    if not quiet:
        print("Syncing...")

    for d in [CONVERSATIONS_DIR, SUMMARIES_DIR, JOURNAL_DIR, ARTIFACTS_DIR]:
        d.mkdir(parents=True, exist_ok=True)

    state = load_state()
    deleted = load_deleted()
    jsonl_files = find_jsonl_files(config)
    if not quiet:
        print(f"  Found {len(jsonl_files)} JSONL files")

    all_summaries = {}
    session_projects = {}
    synced = 0

    for fp, project_name in jsonl_files:
        sid = session_id_to_filename(fp.stem)

        if sid in deleted:
            continue

        session_projects[sid] = project_name
        fstr = str(fp)
        mtime = fp.stat().st_mtime
        conv_file = CONVERSATIONS_DIR / f"{sid}.json"

        cached = state["files"].get(fstr, {})
        if cached.get("mtime") == mtime and conv_file.exists():
            try:
                conv = json.loads(conv_file.read_text())
            except Exception:
                conv = parse_jsonl(fp)
                if not conv:
                    continue
                conv_file.write_text(json.dumps(conv, ensure_ascii=False, indent=2))
        else:
            if not quiet:
                print(f"  Syncing: {fp.name}")
            conv = parse_jsonl(fp)
            if not conv:
                continue
            conv_file.write_text(json.dumps(conv, ensure_ascii=False, indent=2))
            state["files"][fstr] = {
                "mtime": mtime,
                "sessionId": sid,
                "messageCount": conv["messageCount"],
            }
            synced += 1

        summary = load_summary(sid) or auto_summary(conv)
        all_summaries[sid] = summary
        # Track startTime for sorting
        all_summaries[sid]["_startTime"] = conv.get("startTime", "")

    # Build index (sort by startTime desc for correct ordering within same date)
    sessions = sorted(
        [{"id": sid, "project": session_projects.get(sid, ""),
          "startTime": s.get("_startTime", ""),
          **{k: s[k] for k in ["date", "title", "one_line", "tags"]}}
         for sid, s in all_summaries.items()],
        key=lambda x: x.get("startTime", "") or x.get("date", ""), reverse=True
    )
    index = {"lastUpdated": datetime.utcnow().isoformat() + "Z", "sessions": sessions}
    (DATA_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))

    # Build tags
    tags = {}
    for sid, s in all_summaries.items():
        for t in s.get("tags", []):
            tags.setdefault(t, []).append(sid)
    (DATA_DIR / "tags.json").write_text(json.dumps(tags, ensure_ascii=False, indent=2))

    # Enrich sessions with topicIds from segments
    seg_file = DATA_DIR / "segments.json"
    if seg_file.exists():
        try:
            segments = json.loads(seg_file.read_text())
            session_topics = {}
            for seg in segments:
                sid = seg.get("sessionId")
                tid = seg.get("topicId")
                if sid and tid:
                    session_topics.setdefault(sid, set()).add(tid)
            for s in sessions:
                s["topicIds"] = sorted(session_topics.get(s["id"], []))
            # Rewrite index with topicIds
            (DATA_DIR / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
        except (json.JSONDecodeError, KeyError):
            pass

    # Init data files if missing
    for fname, default in [("highlights.json", "[]"), ("artifacts.json", "[]"),
                           ("segments.json", "[]"), ("topics.json", "{}")]:
        f = DATA_DIR / fname
        if not f.exists():
            f.write_text(default)

    save_state(state)
    if not quiet:
        print(f"  Done! Synced {synced} new/updated, {len(sessions)} total sessions")
    elif synced:
        print(f"  Auto-synced {synced} conversations")


# ===== Server with delete API =====

def serve(config, open_browser=True):
    import http.server
    import webbrowser
    import threading

    port = config.get("port", 8787)
    os.chdir(BASE_DIR)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/api/delete":
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = json.loads(self.rfile.read(length))
                    sid = body.get("id")
                    if sid:
                        deleted = load_deleted()
                        deleted.add(sid)
                        save_deleted(deleted)
                        # Remove conversation file
                        conv_file = CONVERSATIONS_DIR / f"{sid}.json"
                        if conv_file.exists():
                            conv_file.unlink()
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"ok": True}).encode())
                    else:
                        self.send_response(400)
                        self.end_headers()
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            pass  # Silence request logs

    server = http.server.HTTPServer(("localhost", port), Handler)
    url = f"http://localhost:{port}/"
    print(f"Server running at {url}")

    if open_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()

    # Auto-sync in background
    sync_interval = config.get("sync_interval", 300)

    def auto_sync():
        import time
        while True:
            time.sleep(sync_interval)
            try:
                sync(config, quiet=True)
            except Exception as e:
                print(f"  Auto-sync error: {e}")

    t = threading.Thread(target=auto_sync, daemon=True)
    t.start()
    print(f"Auto-sync every {sync_interval}s")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped")
        server.shutdown()


# ===== macOS launchd install =====

def install_service():
    import subprocess

    config = load_config()
    # Find a reliable python3 (avoid pyenv shims which may not work in launchd)
    python_candidates = [
        "/usr/local/bin/python3",
        "/opt/homebrew/bin/python3",
        "/usr/bin/python3",
        sys.executable,
    ]
    python_path = next((p for p in python_candidates if os.path.isfile(p)), sys.executable)
    script_path = str(BASE_DIR / "sync.py")
    log_path = str(BASE_DIR / "server.log")
    working_dir = str(BASE_DIR)

    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{script_path}</string>
        <string>--daemon</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{working_dir}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>"""

    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_dir.mkdir(parents=True, exist_ok=True)
    plist_file = plist_dir / f"{PLIST_NAME}.plist"

    # Unload if already running
    subprocess.run(["launchctl", "unload", str(plist_file)],
                   capture_output=True)

    plist_file.write_text(plist_content)
    subprocess.run(["launchctl", "load", str(plist_file)])

    print(f"Installed and started: {PLIST_NAME}")
    print(f"  Server: http://localhost:{config.get('port', 8787)}/")
    print(f"  Logs: {log_path}")
    print(f"  To uninstall: python3 sync.py --uninstall")


def uninstall_service():
    import subprocess

    plist_file = Path.home() / "Library" / "LaunchAgents" / f"{PLIST_NAME}.plist"
    if plist_file.exists():
        subprocess.run(["launchctl", "unload", str(plist_file)],
                       capture_output=True)
        plist_file.unlink()
        print(f"Uninstalled: {PLIST_NAME}")
    else:
        print("Service not installed.")


# ===== Main =====

if __name__ == "__main__":
    if "--init" in sys.argv:
        init_config()
    elif "--install" in sys.argv:
        install_service()
    elif "--uninstall" in sys.argv:
        uninstall_service()
    else:
        cfg = load_config()
        sync(cfg)
        if "--serve" in sys.argv:
            serve(cfg)
        elif "--daemon" in sys.argv:
            serve(cfg, open_browser=False)
