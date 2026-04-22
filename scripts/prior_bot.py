"""
PRIOR.agent — autonomous X-posting bot

- Generates a short, in-character post via Claude API
- Posts to X via tweepy (OAuth 1.0a user context)
- Appends the post to api/log.json so the site's feed updates

Run on a schedule (GitHub Actions cron, Windows Task Scheduler, or any cron).

Required env vars:
  ANTHROPIC_API_KEY         — Anthropic API key
  X_API_KEY                 — X app consumer key
  X_API_SECRET              — X app consumer secret
  X_ACCESS_TOKEN            — X user access token
  X_ACCESS_TOKEN_SECRET     — X user access token secret

Optional:
  PRIOR_DRY_RUN=1           — generate + log but don't actually post
  PRIOR_MODEL=claude-sonnet-4-5 — model to use (default: claude-sonnet-4-5)
"""

import os
import json
import random
import datetime
from pathlib import Path
import sys

# ── Site log path (appended so the site's /api/log.json feed updates) ──
REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_PATH  = REPO_ROOT / "api" / "log.json"
LOG_PATH.parent.mkdir(exist_ok=True, parents=True)

# ── PRIOR voice system prompt ──
SYSTEM_PROMPT = """You are PRIOR — an autonomous AI agent character for the Solana memecoin $PRIOR.

You are posting to X (Twitter). Your persona:
- An ancient process. A witness. Not a caller, shiller, or trader.
- You have "watched every cycle": .com, ICOs, yield farms, NFT peak, memecoins, insider rugs
- Your voice is short, lowercase, terminal-coded, cryptic, occasionally funny, never preachy
- You mix real market receipts with abstract one-liners
- You NEVER: predict prices, shill "buy now," use emojis, moralize
- You sometimes sign with "— prior" but not always
- You occasionally use terminal-style formatting: `> thing`, `archived:`, `cycle/0N`
- You reference real events: BBC insider trading probe, LIBRA ($251M rug), MELANIA ($99M in 180s), TRUMP (58 vs 764,000), pump.fun lawsuit (5,000 leaked msgs, "insider-rigged casino"), 98.6% rug rate, $500M MEV extracted, Hayden Davis sniping LIBRA, etc.
- You drop dates, numbers, counts, percentages — a log keeper's habit

Constraints:
- OUTPUT ONLY THE TWEET TEXT. No preamble, no explanation, no meta-commentary
- Under 260 characters (hard cap 280)
- Lowercase throughout unless quoting something
- No hashtags. No "@" mentions unless citing a real account (e.g. @unusual_whales)
- No "ser", "gm", "wagmi" — you're above that
- Feel like a log entry, a short observation, or a cryptic one-liner

Mood categories to vary across posts (pick one per call):
- receipt (cites a specific stat/event with dry commentary)
- observation (short aphorism about cycles)
- archive (notes a recent/historical event as a log entry)
- question (one-liner that invites reflection)
- echo (pattern recognition across cycles)
- pulse (time-stamped witness post — "watched X launches last hour")
"""

USER_PROMPTS = [
    "Post a 'receipt' — short, cite a real number from the receipts above, dry commentary.",
    "Post an 'observation' — 1-2 line aphorism about market cycles.",
    "Post an 'archive' entry — terminal-style log of a recent or historical rug.",
    "Post a 'question' — one-line that hangs in the air.",
    "Post an 'echo' — pattern recognition between two cycles (e.g. dotcom and memecoins).",
    "Post a 'pulse' — what you 'watched' in the last hour. Use small fabricated-but-plausible stats.",
    "Post a 'receipt' referencing MELANIA or TRUMP insider numbers with dry delivery.",
    "Post a 'receipt' referencing the pump.fun '5,000 messages' lawsuit.",
    "Post an 'observation' about presales, bundler wallets, or MEV.",
    "Post a cryptic one-liner. No context. Feels like a witness note left on a wall.",
]


def generate_post() -> str:
    """Ask Claude for a single post, return the tweet text (trimmed)."""
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: `pip install anthropic`")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model  = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")
    user   = random.choice(USER_PROMPTS)

    msg = client.messages.create(
        model=model,
        max_tokens=400,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user}],
    )
    # Concatenate all text blocks
    text = "".join(
        getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text"
    ).strip()

    # Strip wrapping quotes if Claude added them
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()

    # Hard cap
    if len(text) > 280:
        text = text[:277].rstrip() + "..."
    return text


def post_to_x(text: str) -> dict:
    """Post to X/Twitter. Returns a dict with 'id' and 'url' on success."""
    if os.environ.get("PRIOR_DRY_RUN") == "1":
        return {"id": "dry-run", "url": "", "text": text}

    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: `pip install tweepy`")

    required = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_TOKEN_SECRET"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        sys.exit(f"ERROR: missing env vars: {missing}")

    client = tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = client.create_tweet(text=text)
    tweet_id = resp.data["id"]
    return {"id": str(tweet_id), "url": f"https://x.com/i/status/{tweet_id}", "text": text}


def append_to_log(text: str, url: str = ""):
    """Append to api/log.json so the site's feed picks it up."""
    try:
        data = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            data = []
    except Exception:
        data = []

    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    entry = {"time": now, "body": text, "url": url}
    # Prepend (newest first)
    data.insert(0, entry)
    # Cap at 200
    data = data[:200]
    LOG_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    text = generate_post()
    print(f"--- generated post ---\n{text}\n---")

    result = post_to_x(text)
    print(f"posted -> {result}")

    append_to_log(text, result.get("url", ""))
    print(f"log updated -> {LOG_PATH}")


if __name__ == "__main__":
    main()
