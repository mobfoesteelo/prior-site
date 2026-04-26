"""Post a single arbitrary tweet (manifesto, pin, announcement).

Reads PRIOR_POST_TEXT from env, posts via OAuth 1.0a, logs to data/log.json.
"""
import os
import sys
import json
import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH  = REPO_ROOT / "data" / "log.json"
LOG_PATH.parent.mkdir(exist_ok=True, parents=True)


def main():
    text = os.environ.get("PRIOR_POST_TEXT", "").strip()
    if not text:
        sys.exit("ERROR: PRIOR_POST_TEXT not set")
    if len(text) > 280:
        print(f"WARN: text is {len(text)} chars, X limit is 280. Truncating.")
        text = text[:277].rstrip() + "..."

    print(f"--- post text ---\n{text}\n---")

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
    resp = client.create_tweet(text=text)
    tid = resp.data["id"]
    url = f"https://x.com/i/status/{tid}"
    print(f"posted -> {url}")

    # Log it
    try:
        log = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(log, list):
            log = []
    except Exception:
        log = []

    log.insert(0, {
        "time": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "body": text,
        "url":  url,
    })
    LOG_PATH.write_text(json.dumps(log[:200], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"logged -> {LOG_PATH}")


if __name__ == "__main__":
    main()
