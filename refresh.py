#!/usr/bin/env python3
"""Post-save script for cm-nap / cm-sleep.
Runs mechanical steps after AI writes summaries/journals:
  1. Symlink artifacts to artifacts/ directory
  2. Re-sync index
  3. Regenerate recent-summaries.md
"""

import json
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
SUMMARIES_DIR = DATA_DIR / "summaries"


def symlink_artifacts():
    """Ensure all artifacts are accessible via artifacts/ directory."""
    arts_file = DATA_DIR / "artifacts.json"
    if not arts_file.exists():
        return
    try:
        artifacts = json.loads(arts_file.read_text())
    except Exception:
        return

    ARTIFACTS_DIR.mkdir(exist_ok=True)
    linked = 0
    for art in artifacts:
        src = art.get("path")
        filename = art.get("filename")
        if not src or not filename:
            continue
        src_path = Path(src)
        dst_path = ARTIFACTS_DIR / filename
        # Skip if source is already in artifacts dir
        if src_path.parent.resolve() == ARTIFACTS_DIR.resolve():
            continue
        # Skip if source doesn't exist
        if not src_path.exists():
            continue
        # Create or update symlink
        if dst_path.is_symlink() or dst_path.exists():
            dst_path.unlink()
        dst_path.symlink_to(src_path)
        linked += 1
    if linked:
        print(f"  Linked {linked} artifact(s)")


def regenerate_recent_summaries():
    """Regenerate recent-summaries.md from the 5 most recent sessions."""
    index_file = DATA_DIR / "index.json"
    if not index_file.exists():
        return
    try:
        index = json.loads(index_file.read_text())
    except Exception:
        return

    sessions = index.get("sessions", [])[:5]
    parts = []
    for s in sessions:
        sid = s["id"]
        summary_file = SUMMARIES_DIR / f"{sid}.md"
        if summary_file.exists():
            parts.append(summary_file.read_text(encoding="utf-8"))
        else:
            # Fallback: minimal entry from index
            parts.append(f"---\nsessionId: {sid}\ndate: {s.get('date', '')}\ntitle: \"{s.get('title', '')}\"\none_line: \"{s.get('one_line', '')}\"\n---\n")

    output = DATA_DIR / "recent-summaries.md"
    output.write_text("\n\n".join(parts), encoding="utf-8")
    print(f"  Updated recent-summaries.md ({len(parts)} sessions)")


def run_sync():
    """Run sync.py to update index."""
    config_file = BASE_DIR / "config.json"
    if not config_file.exists():
        print("  Warning: config.json not found, skipping sync")
        return

    # Import and run sync from sync.py
    sys.path.insert(0, str(BASE_DIR))
    from sync import sync, load_config
    config = load_config()
    sync(config)


def main():
    os.chdir(BASE_DIR)
    print("Post-save:")
    symlink_artifacts()
    run_sync()
    regenerate_recent_summaries()
    print("  Done!")


if __name__ == "__main__":
    main()
