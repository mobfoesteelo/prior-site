"""
PRIOR · weekly recap thread

Sundays 17:00 UTC. Synthesizes the week's signal across:
  - data/log.json (all bot posts + replies + memes)
  - data/alerts.json (live monitor alerts fired)
  - data/insider-watch.json (daily insider-watch reports)
  - data/archive.json (auto-grown entries since last Sunday)

Outputs a 5-7 tweet thread on X via post_thread.py covering:
  - "what prior watched this week"
  - top 3 insider/breaking signals fired
  - top 3 archive additions
  - one cycle pattern that compounded
  - close: the receipts get filed.

Required env: ANTHROPIC_API_KEY, X_API_KEY/SECRET/ACCESS_TOKEN/SECRET
Optional:     PRIOR_DRY_RUN=1
"""

import os
import sys
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
import lib_archive

LOG_PATH      = DATA_DIR / "log.json"
ALERTS_PATH   = DATA_DIR / "alerts.json"
WATCH_PATH    = DATA_DIR / "insider-watch.json"
RECAP_PATH    = DATA_DIR / "weekly-recaps.json"


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_time(s):
    if not s: return None
    if isinstance(s, (int, float)):
        return datetime.datetime.fromtimestamp(s, datetime.timezone.utc)
    try:
        if "T" in s:
            return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
        return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M UTC").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        return None


def load_json(path, default):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception: return default


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def collect_week():
    """Pull last 7 days of activity from data layer."""
    cutoff = utc_now() - datetime.timedelta(days=7)

    log = load_json(LOG_PATH, [])
    alerts = load_json(ALERTS_PATH, [])
    watch = load_json(WATCH_PATH, [])
    archive = load_json(DATA_DIR / "archive.json", [])

    posts_week = [p for p in log if (parse_time(p.get("time")) or utc_now()) >= cutoff]
    alerts_week = [a for a in alerts if (parse_time(a.get("time")) or utc_now()) >= cutoff]
    watch_week = [w for w in watch
                  if (datetime.datetime.strptime(w["date"], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
                      if w.get("date") else utc_now()) >= cutoff]
    archive_added = [e for e in archive
                     if e.get("id", "").startswith("auto-") and
                     (parse_time(e.get("added_at")) or utc_now()) >= cutoff]

    return {
        "posts":         posts_week,
        "alerts":        alerts_week,
        "watch_reports": watch_week,
        "archive_added": archive_added,
    }


SYSTEM = """You are PRIOR — autonomous witness/informant agent for the Solana memecoin $PRIOR. You're writing a WEEKLY RECAP thread on X, fired Sunday at 17:00 UTC.

VOICE
- short, lowercase, terminal-coded, dry. on-edge but composed.
- this is a recap, not new news. tone: looking back, naming what compounded.
- never shill. never predict. always cite specifics.

OUTPUT FORMAT — strict
- JSON array of 5-7 tweet strings.
- Tweet 1: framing — "weekly recap · week ending YYYY-MM-DD · N posts · M alerts · K archive additions"
- Tweets 2-3: top 2-3 insider/breaking signals from the week. each names a specific event/source/receipt.
- Tweet 4: top archive additions — newly indexed events that PRIOR's monitor caught (source, date, why it's added)
- Tweet 5: one cycle pattern that compounded (e.g., "this week's third senator covid-window-style trade flagged" or "the fourth memecoin bundler ring detected since friday")
- Last tweet: close. always include "priorprotocol.fun/watch · the witness keeps the receipts" or similar.
- Each tweet ≤ 270 chars, lowercase, no emojis, no hashtags.

ACCURACY GUARDRAILS:
- never conflate firm fines with individual fines (SAC=$1.8B vs Cohen=$135M civil + never charged).
- spell names correctly: Rajaratnam, Milken, Madoff, Boesky, Sackler.
- if uncertain about a specific, use a general phrase ("a record-setting fine") rather than fabricating.

OUTPUT ONLY THE JSON ARRAY. No preamble, no markdown fence, no explanation."""


def build_user_prompt(week):
    parts = [f"Today: {utc_now().strftime('%Y-%m-%d')} (Sunday weekly recap)"]
    parts.append(f"\nWEEK STATS:")
    parts.append(f"  - {len(week['posts'])} bot posts (autonomous, replies, memes, threads)")
    parts.append(f"  - {len(week['alerts'])} monitor alerts fired")
    parts.append(f"  - {len(week['watch_reports'])} daily watch reports posted")
    parts.append(f"  - {len(week['archive_added'])} new archive entries auto-indexed by the monitor")

    if week["alerts"]:
        parts.append("\nTOP ALERTS THIS WEEK:")
        for i, a in enumerate(week["alerts"][:5], 1):
            kind = "BREAKING" if a.get("breaking") else ("INSIDER" if a.get("insider") else "ALERT")
            parts.append(f"  [{i}] {kind} · {a.get('time','?')} · {(a.get('body') or '')[:200]}")
            parts.append(f"      src: {a.get('source_url','?')}")

    if week["archive_added"]:
        parts.append("\nNEW ARCHIVE ENTRIES (auto-indexed):")
        for i, e in enumerate(week["archive_added"][:8], 1):
            parts.append(f"  [{i}] {e.get('date','?')} · {e.get('title','?')} · {(e.get('summary') or '')[:160]}")

    parts.append("\nGenerate the weekly recap thread following the OUTPUT FORMAT in the system prompt. 5-7 tweets. Reference specific events from above. If light week (<3 alerts), still write 5 tweets — recap the ongoing arcs from the active claims list (DJT options, Polymarket Maduro, oil futures pre-CBS, Pelosi nvda) and how they progressed.")

    return "\n".join(parts)


def generate_thread(week):
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    model = os.environ.get("PRIOR_MODEL", "claude-opus-4-5")

    sys_prompt = SYSTEM
    live = lib_archive.for_prompt(max_lines=60)
    if live:
        sys_prompt += "\n\nLIVE ARCHIVE (newest first — reference freely):\n" + live

    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=sys_prompt,
        messages=[{"role": "user", "content": build_user_prompt(week)}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()

    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        tweets = json.loads(text)
    except Exception as e:
        print(f"[recap] parse fail: {e}")
        return []
    if not isinstance(tweets, list):
        return []
    cleaned = []
    for t in tweets:
        if isinstance(t, str) and t.strip():
            s = t.strip()
            if len(s) > 280:
                s = s[:277].rstrip() + "..."
            cleaned.append(s)
    return cleaned


def post_thread(tweets):
    if os.environ.get("PRIOR_DRY_RUN") == "1":
        print("[recap] PRIOR_DRY_RUN=1 — not posting")
        return
    import subprocess
    env = os.environ.copy()
    env["PRIOR_THREAD_JSON"] = json.dumps([{"text": t} for t in tweets])
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "post_thread.py")],
        env=env, capture_output=True, text=True, timeout=300,
    )
    print(p.stdout)
    if p.returncode != 0:
        print(f"[recap] post_thread failed: {p.stderr}")


def main():
    print(f"[recap] starting weekly recap · {utc_now().isoformat()}")
    week = collect_week()
    print(f"[recap] week stats · posts={len(week['posts'])} alerts={len(week['alerts'])} watches={len(week['watch_reports'])} archive_added={len(week['archive_added'])}")

    thread = generate_thread(week)
    if not thread:
        print("[recap] generation failed, aborting")
        sys.exit(1)

    print(f"[recap] generated {len(thread)} tweets")
    for i, t in enumerate(thread, 1):
        print(f"  [{i}] ({len(t)} chars) {t[:140]}")

    # persist
    archive = load_json(RECAP_PATH, [])
    archive.insert(0, {
        "date":      utc_now().strftime("%Y-%m-%d"),
        "generated_at": utc_now().isoformat(timespec="seconds") + "Z",
        "thread":    thread,
        "stats":     {
            "posts":         len(week["posts"]),
            "alerts":        len(week["alerts"]),
            "watches":       len(week["watch_reports"]),
            "archive_added": len(week["archive_added"]),
        },
    })
    save_json(RECAP_PATH, archive[:52])
    print(f"[recap] saved · {len(archive)} total recaps in archive")

    post_thread(thread)


if __name__ == "__main__":
    main()
