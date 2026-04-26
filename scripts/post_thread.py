"""
PRIOR · post a connected thread on X.

Reads a JSON array of tweet strings from PRIOR_THREAD_JSON env var
(or from a file path in PRIOR_THREAD_FILE), posts the first tweet,
then chains each subsequent tweet as a reply to the previous one.

Each tweet is logged to data/log.json with type="thread" and a
thread_id field grouping them.

Required env: X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
Optional:     PRIOR_DRY_RUN=1
"""

import os
import sys
import json
import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH  = REPO_ROOT / "data" / "log.json"


def main():
    raw = os.environ.get("PRIOR_THREAD_JSON", "").strip()
    if not raw:
        path = os.environ.get("PRIOR_THREAD_FILE", "").strip()
        if path:
            raw = Path(path).read_text(encoding="utf-8")
    if not raw:
        sys.exit("ERROR: set PRIOR_THREAD_JSON or PRIOR_THREAD_FILE")

    try:
        tweets = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: bad JSON: {e}")

    if not isinstance(tweets, list) or not all(isinstance(t, str) for t in tweets):
        sys.exit("ERROR: expected a JSON array of strings")

    # Validate lengths
    for i, t in enumerate(tweets):
        if len(t) > 280:
            print(f"WARN: tweet {i+1} is {len(t)} chars (>280). Truncating.")
            tweets[i] = t[:277].rstrip() + "..."

    print(f"--- thread of {len(tweets)} tweets ---")
    for i, t in enumerate(tweets, 1):
        print(f"\n[{i}/{len(tweets)}] ({len(t)} chars)")
        print(t)
    print("\n---")

    if os.environ.get("PRIOR_DRY_RUN") == "1":
        print("[dry-run] not posting")
        return

    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")

    client = tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )

    # Post chain
    thread_id = datetime.datetime.now(datetime.timezone.utc).strftime("thread-%Y%m%d-%H%M")
    posted = []
    reply_to = None
    for i, t in enumerate(tweets, 1):
        kwargs = {"text": t}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = int(reply_to)
        resp = client.create_tweet(**kwargs)
        tid = str(resp.data["id"])
        url = f"https://x.com/i/status/{tid}"
        print(f"[{i}/{len(tweets)}] posted: {url}")
        posted.append({"tid": tid, "url": url, "text": t, "n": i})
        reply_to = tid

    # Append all to log.json
    try:
        log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(log, list):
            log = []
    except Exception:
        log = []

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    # Insert in reverse so the FIRST tweet ends up at top of feed (newest first)
    for p in reversed(posted):
        log.insert(0, {
            "time":      now,
            "body":      p["text"],
            "url":       p["url"],
            "type":      "thread",
            "thread_id": thread_id,
            "thread_n":  p["n"],
            "thread_total": len(tweets),
        })
    LOG_PATH.write_text(json.dumps(log[:200], indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[done] {len(posted)} tweets posted as thread {thread_id}")
    print(f"[head] {posted[0]['url']}")


if __name__ == "__main__":
    main()
