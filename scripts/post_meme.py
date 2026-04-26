"""
PRIOR · meme posting engine

Picks an unposted image from memes/ and posts it to X with the caption
from the matching .txt sidecar file.

Required env vars:
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

Optional:
  PRIOR_DRY_RUN=1   — log + mark, but do not actually post

Convention:
  memes/01-tuskegee.png    ← image
  memes/01-tuskegee.txt    ← caption

State:
  data/memes-state.json    ← {"posted": ["01-tuskegee.png", ...]}
  data/log.json            ← appended with type="meme" entries
"""

import os
import sys
import json
import datetime
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent.parent
MEMES_DIR  = REPO_ROOT / "memes"
DATA_DIR   = REPO_ROOT / "data"
STATE_PATH = DATA_DIR / "memes-state.json"
LOG_PATH   = DATA_DIR / "log.json"

DATA_DIR.mkdir(exist_ok=True, parents=True)

IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_BYTES = 5 * 1024 * 1024  # X image size cap


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def utc_now_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def find_next_meme(state):
    """Return (image_path, caption_path) for the next unposted meme, or (None, None)."""
    posted = set(state.get("posted", []))

    images = sorted(
        p for p in MEMES_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMG_EXTS
    )
    for img in images:
        if img.name in posted:
            continue
        if img.stat().st_size > MAX_BYTES:
            print(f"[skip] {img.name} exceeds 5MB cap ({img.stat().st_size} bytes)")
            continue
        cap_path = img.with_suffix(".txt")
        if not cap_path.exists():
            print(f"[skip] {img.name} has no .txt sidecar — needs a caption")
            continue
        return img, cap_path
    return None, None


def post_to_x(image_path: Path, caption: str) -> dict:
    """Upload media via X v1.1, post via v2. Returns {id, url, text}."""
    if os.environ.get("PRIOR_DRY_RUN") == "1":
        return {"id": "dry-run", "url": "", "text": caption}

    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")

    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: missing env vars: {missing}")

    # v1.1 API for media upload
    auth = tweepy.OAuth1UserHandler(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    api_v1 = tweepy.API(auth)

    print(f"[upload] {image_path.name} ({image_path.stat().st_size} bytes)")
    media = api_v1.media_upload(filename=str(image_path))
    media_id = media.media_id_string
    print(f"[uploaded] media_id={media_id}")

    # v2 API for tweet creation with media
    client = tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = client.create_tweet(text=caption, media_ids=[media_id])
    tweet_id = resp.data["id"]
    return {"id": str(tweet_id), "url": f"https://x.com/i/status/{tweet_id}", "text": caption}


def append_log(caption: str, image_filename: str, url: str = ""):
    """Append meme post to data/log.json."""
    log = load_json(LOG_PATH, [])
    if not isinstance(log, list):
        log = []

    entry = {
        "time":  utc_now_str(),
        "body":  caption,
        "url":   url,
        "type":  "meme",
        "image": f"/memes/{image_filename}",
    }
    log.insert(0, entry)
    log = log[:200]
    save_json(LOG_PATH, log)


def main():
    if not MEMES_DIR.exists():
        print(f"[noop] {MEMES_DIR} does not exist")
        return

    state = load_json(STATE_PATH, {"posted": []})
    if "posted" not in state:
        state["posted"] = []

    image, caption_file = find_next_meme(state)
    if image is None:
        print("[noop] no unposted memes in queue")
        return

    caption = caption_file.read_text(encoding="utf-8").strip()
    if not caption:
        print(f"[skip] {caption_file.name} is empty")
        return
    if len(caption) > 280:
        print(f"[trim] caption {len(caption)} chars > 280, truncating")
        caption = caption[:277].rstrip() + "..."

    print(f"--- meme: {image.name} ---")
    print(caption)
    print("---")

    result = post_to_x(image, caption)
    print(f"posted -> {result}")

    # Mark posted (even on dry-run, so we cycle through)
    if os.environ.get("PRIOR_DRY_RUN") != "1":
        state["posted"].append(image.name)
        save_json(STATE_PATH, state)
        append_log(caption, image.name, result.get("url", ""))
        print(f"[state] {len(state['posted'])} memes posted total")
    else:
        print("[dry-run] not marking as posted, not logging")


if __name__ == "__main__":
    main()
