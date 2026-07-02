"""Dedup state, persisted to a small JSON file cached between CI runs
(via GitHub Actions cache; not committed to git).

Shape:
    {
      "initialized": true,
      "seen": { "<commentId>": "<iso8601 timestamp when first seen>" }
    }

`initialized` exists so the very first run can silently seed everything it
currently sees WITHOUT firing a notification per old comment (otherwise the
first poll would flood you with the entire backlog).
"""

import json
import os
from datetime import datetime, timedelta, timezone
from typing import Dict


def _now() -> datetime:
    return datetime.now(timezone.utc)


def load(path: str) -> dict:
    if not os.path.exists(path):
        return {"initialized": False, "seen": {}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupt/empty file -> start clean rather than crash the run.
        return {"initialized": False, "seen": {}}
    data.setdefault("initialized", False)
    data.setdefault("seen", {})
    data.setdefault("assignees", {})
    return data


def save(path: str, state: dict) -> None:
    # Stable key order keeps git diffs minimal and readable.
    state["seen"] = dict(sorted(state["seen"].items()))
    state["assignees"] = dict(sorted(state.get("assignees", {}).items()))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
        f.write("\n")


def is_seen(state: dict, comment_id: str) -> bool:
    return comment_id in state["seen"]


def mark_seen(state: dict, comment_id: str) -> None:
    state["seen"][comment_id] = _now().isoformat()


def prune(state: dict, days: int) -> None:
    """Drop remembered IDs older than `days` to bound file size."""
    cutoff = _now() - timedelta(days=days)
    kept: Dict[str, str] = {}
    for cid, ts in state["seen"].items():
        try:
            seen_at = datetime.fromisoformat(ts)
        except ValueError:
            # Unparseable timestamp -> keep it (safer than re-notifying).
            kept[cid] = ts
            continue
        if seen_at >= cutoff:
            kept[cid] = ts
    state["seen"] = kept