"""
PRIOR · dynamic archive helper

The archive is a single authoritative file: data/archive.json. Every
posting script reads it at start so PRIOR's "memory" grows over time
as new significant events fire through the live monitor and daily
insider-watch.

Schema:
[
  {
    "id":      "<short slug>",         e.g. "boesky-1986" or "auto-2026-04-27-12-34"
    "date":    "YYYY-MM" or YYYY-MM-DD",
    "title":   "<short name>",         e.g. "Ivan Boesky"
    "summary": "<one-line dry receipt>",  e.g. "$100M fine · 3 yrs · cooperator → Milken"
    "source":  "<feed | URL | 'seed'>",
    "tags":    ["insider", "wallst", ...],
    "added_at": "ISO timestamp"
  },
  ...
]

Newest first. Capped at 500 entries to keep prompt size bounded.
"""

import json
import datetime
import hashlib
from pathlib import Path

ARCHIVE_PATH = Path(__file__).resolve().parent.parent / "data" / "archive.json"
MAX_ENTRIES = 500


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"


def load() -> list:
    try:
        d = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def save(entries: list):
    ARCHIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARCHIVE_PATH.write_text(
        json.dumps(entries[:MAX_ENTRIES], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _id_for(title: str, source: str) -> str:
    h = hashlib.sha1((title + "|" + source).encode("utf-8")).hexdigest()[:10]
    return "auto-" + h


def append(date: str, title: str, summary: str, source: str = "auto", tags=None) -> bool:
    """Append a new entry. Dedup by (title + source). Returns True if added.

    `date` should be the event date (YYYY-MM or YYYY-MM-DD).
    `title` is the short name (≤ 60 chars). `summary` is the one-line receipt.
    """
    entries = load()
    eid = _id_for(title, source)
    if any(e.get("id") == eid for e in entries):
        return False
    if any(e.get("title") == title and e.get("source") == source for e in entries):
        return False

    entry = {
        "id":       eid,
        "date":     date,
        "title":    title[:80],
        "summary":  summary[:240],
        "source":   source[:200],
        "tags":     list(tags) if tags else [],
        "added_at": utc_now_iso(),
    }
    entries.insert(0, entry)
    save(entries)
    return True


def for_prompt(max_lines: int = 80) -> str:
    """Format the archive as a list of one-line entries for system prompts.

    The newest items at the top so they're prioritized in the context window.
    Returns at most `max_lines` lines.
    """
    entries = load()
    lines = []
    for e in entries[:max_lines]:
        date = e.get("date", "?")
        title = e.get("title", "")
        summary = e.get("summary", "")
        if title and summary:
            lines.append(f"  {date} · {title} · {summary}")
    return "\n".join(lines)


def stats() -> dict:
    entries = load()
    return {
        "total": len(entries),
        "auto_added": sum(1 for e in entries if e.get("id", "").startswith("auto-")),
        "seed":       sum(1 for e in entries if not e.get("id", "").startswith("auto-")),
        "newest":     entries[0].get("added_at") if entries else None,
    }
