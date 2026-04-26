"""
PRIOR · post a connected thread on X with optional media per tweet.

Reads a JSON array of tweet objects from PRIOR_THREAD_JSON env var
(or from a file path in PRIOR_THREAD_FILE).

Each tweet object can be:
  - a plain string                    {text: "..."}            (back-compat)
  - an object with text + media:      {"text": "...", "media": "memes/01-foo.jpg"}
  - an object with up to 4 images:    {"text": "...", "media": ["memes/01.jpg", "memes/02.jpg"]}

Posts the first tweet, chains each subsequent as a reply to the previous.

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


def normalize(item):
    """Coerce string or object into {text, media} shape. media is list of paths."""
    if isinstance(item, str):
        return {"text": item, "media": []}
    if isinstance(item, dict):
        text = str(item.get("text", "")).strip()
        media = item.get("media")
        if media is None:
            media = []
        elif isinstance(media, str):
            media = [media]
        elif not isinstance(media, list):
            media = []
        media = [str(m) for m in media if m][:4]   # X allows max 4 images per tweet
        return {"text": text, "media": media}
    return {"text": "", "media": []}


def main():
    raw = os.environ.get("PRIOR_THREAD_JSON", "").strip()
    if not raw:
        path = os.environ.get("PRIOR_THREAD_FILE", "").strip()
        if path:
            raw = Path(path).read_text(encoding="utf-8")
    if not raw:
        sys.exit("ERROR: set PRIOR_THREAD_JSON or PRIOR_THREAD_FILE")

    try:
        items = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.exit(f"ERROR: bad JSON: {e}")
    if not isinstance(items, list):
        sys.exit("ERROR: expected JSON array")

    tweets = [normalize(it) for it in items]

    # validate
    for i, t in enumerate(tweets, 1):
        if not t["text"] and not t["media"]:
            sys.exit(f"ERROR: tweet {i} is empty")
        if len(t["text"]) > 280:
            print(f"WARN: tweet {i} is {len(t['text'])} chars (>280). Truncating.")
            t["text"] = t["text"][:277].rstrip() + "..."
        for m in t["media"]:
            p = REPO_ROOT / m
            if not p.exists():
                sys.exit(f"ERROR: tweet {i} media missing: {m}")

    print(f"--- thread of {len(tweets)} tweets ---")
    for i, t in enumerate(tweets, 1):
        media_str = f" [+{len(t['media'])} img: {', '.join(t['media'])}]" if t["media"] else ""
        print(f"\n[{i}/{len(tweets)}] {len(t['text'])} chars{media_str}")
        print(t["text"])
    print("\n---")

    if os.environ.get("PRIOR_DRY_RUN") == "1":
        print("[dry-run] not posting")
        return

    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")

    # OAuth 1.0a for both media upload (v1.1) and tweet creation (v2)
    auth = tweepy.OAuth1UserHandler(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    api_v1 = tweepy.API(auth)

    client = tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )

    thread_id = datetime.datetime.now(datetime.timezone.utc).strftime("thread-%Y%m%d-%H%M")
    posted = []
    reply_to = None

    for i, t in enumerate(tweets, 1):
        media_ids = []
        for m in t["media"]:
            p = REPO_ROOT / m
            print(f"  [upload {i}] {m}")
            up = api_v1.media_upload(filename=str(p))
            media_ids.append(up.media_id_string)

        kwargs = {"text": t["text"]}
        if reply_to:
            kwargs["in_reply_to_tweet_id"] = int(reply_to)
        if media_ids:
            kwargs["media_ids"] = media_ids

        resp = client.create_tweet(**kwargs)
        tid = str(resp.data["id"])
        url = f"https://x.com/i/status/{tid}"
        print(f"[{i}/{len(tweets)}] posted: {url}")
        posted.append({"tid": tid, "url": url, "text": t["text"], "media": t["media"], "n": i})
        reply_to = tid

    # Append all to log.json (oldest tweet first in thread order, but log is newest-first)
    try:
        log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(log, list):
            log = []
    except Exception:
        log = []

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    for p in reversed(posted):
        entry = {
            "time":         now,
            "body":         p["text"],
            "url":          p["url"],
            "type":         "thread",
            "thread_id":    thread_id,
            "thread_n":     p["n"],
            "thread_total": len(tweets),
        }
        if p["media"]:
            entry["image"] = "/" + p["media"][0]   # site shows first image
        log.insert(0, entry)
    LOG_PATH.write_text(json.dumps(log[:200], indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n[done] {len(posted)} tweets posted as thread {thread_id}")
    print(f"[head] {posted[0]['url']}")


if __name__ == "__main__":
    main()
