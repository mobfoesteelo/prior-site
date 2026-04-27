"""
PRIOR · target-AI-agent engagement engine

Once per cron tick, scans recent posts from a list of high-leverage X
accounts (other AI agents, big crypto-twitter analysts) for content
matching the cycles/insider/fraud archive, and posts a quote-tweet
reply that adds an archive receipt — landing in their replies and
borrowing their reach.

Hard rules:
- max 1 engagement per target account per 6 hours (not spammy)
- max 4 engagements per day total (under X 17/day cap)
- only engages if the matched post passes a Claude relevance filter
- never engages with shilling / pumping / ratio-bait posts

Required env: ANTHROPIC_API_KEY, X_API_KEY/SECRET/ACCESS_TOKEN/SECRET, X_BEARER_TOKEN
Optional:     PRIOR_DRY_RUN=1, PRIOR_AGENT_MAX_PER_DAY=4, PRIOR_AGENT_COOLDOWN_HOURS=6
"""

import os
import sys
import json
import re
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

ENGAGE_LOG_PATH   = DATA_DIR / "agent-engagements.json"
ENGAGE_STATE_PATH = DATA_DIR / "agent-engage-state.json"

# ── target accounts to scan (handle, why we're watching them) ──────
# Pick high-signal accounts whose audiences overlap with PRIOR's target.
TARGETS = [
    # crypto twitter AI agents
    {"handle": "aixbt_agent",   "weight": 3, "note": "crypto market alpha agent, ~700K followers"},
    {"handle": "truth_terminal","weight": 2, "note": "OG AI agent, $GOAT lineage"},
    {"handle": "elizaOS",       "weight": 1, "note": "AI agent infra"},
    {"handle": "ai16z_dao",     "weight": 1, "note": "AI agent project"},
    {"handle": "virtuals_io",   "weight": 1, "note": "AI agent platform"},
    # high-signal crypto + finance accounts (feed PRIOR's archive into their threads)
    {"handle": "unusual_whales","weight": 3, "note": "options flow + politician trades"},
    {"handle": "blknoiz06",     "weight": 2, "note": "memecoin trader, big audience"},
    {"handle": "0xMert_",       "weight": 1, "note": "helius CEO, solana infra"},
    {"handle": "hosseeb",       "weight": 1, "note": "crypto VC, lots of cycle-takes"},
    # finance / insider trading specialists
    {"handle": "PelosiTracker_","weight": 3, "note": "tracks pelosi trades — direct overlap"},
    {"handle": "WhiteHouse",    "weight": 1, "note": "official admin handle, signal source"},
]

# Patterns that promote a post to "candidate for engagement"
TRIGGER_PATTERNS = [
    r'\binsider trad', r'\bfront[- ]?run', r'\bunusual.{0,15}(option|volume)',
    r'\bSEC charges', r'\bDOJ indicts',
    r'\bPelosi', r'\bBurr', r'\bLoeffler', r'\bFeinstein', r'\bTuberville',
    r'\bKaplan', r'\bRosengren', r'\bClarida',
    r'\bSAC ', r'\bGalleon', r'\bRajaratnam', r'\bCohen', r'\bBoesky', r'\bMilken',
    r'\bDJT\b', r'\bTrump Media', r'\bTMTG', r'\bMELANIA', r'\bLIBRA',
    r'\bbundler', r'\bMEV ', r'\bsandwich', r'\bsniper bot',
    r'\bcycle', r'\bplaybook', r'\barchitecture',
    r'\bcorrupt', r'\bfraud', r'\bponzi', r'\brug pull',
    r'\bcolluded', r'\btoo big to fail', r'\btoo big to jail',
    r'\bFed officials', r'\bSenate.{0,10}(stock|trade)',
    r'\bpump\.fun', r'\bpumpfun', r'\bPolymarket',
    # specific Trump admin signals
    r'\boil futures', r'\bcabinet.{0,15}(trade|disclos)', r'\bMaduro', r'\bIran.{0,10}strike',
]
TRIGGER_RE = re.compile('|'.join(TRIGGER_PATTERNS), re.IGNORECASE)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def utc_today():
    return utc_now().strftime("%Y-%m-%d")


# ── X client helpers (mirror replies.py for consistency) ──────────
def x_read_client():
    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")
    bt = os.environ.get("X_BEARER_TOKEN")
    if not bt:
        sys.exit("ERROR: X_BEARER_TOKEN not set")
    return tweepy.Client(bearer_token=bt, wait_on_rate_limit=True)


def x_write_client():
    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")
    return tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
        wait_on_rate_limit  = True,
    )


def fetch_recent_from_target(client, handle, since_minutes=180):
    """Pull recent tweets from a single handle via search_recent_tweets."""
    cutoff = utc_now() - datetime.timedelta(minutes=since_minutes)
    try:
        # search_recent_tweets supports `from:handle` filtering
        resp = client.search_recent_tweets(
            query=f"from:{handle} -is:retweet",
            max_results=10,
            tweet_fields=["created_at", "public_metrics", "conversation_id"],
            start_time=cutoff.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
        if not resp or not resp.data:
            return []
        return list(resp.data)
    except Exception as e:
        print(f"  [{handle}] fetch fail: {type(e).__name__} {str(e)[:100]}")
        return []


# ── relevance + reply generation ──────────────────────────────────
RELEVANCE_SYSTEM = """You decide whether PRIOR (an autonomous witness/informant agent for a Solana memecoin) should engage with this X post.

ENGAGE = TRUE only if:
- The post substantively discusses: market cycles, insider trading, regulatory capture, named insider scandals, the DPA carousel, fraud / front-running / unusual options activity / specific named politicians' trades / crypto rug or insider patterns / or anything PRIOR has documented receipts for.
- AND the post is sincere (not pure shilling, not ratio-bait, not low-effort meme).

ENGAGE = FALSE if:
- pure pump shilling ("buy this", "1000x", "moon")
- generic bull-posting or bear-posting without a substantive claim
- low-effort takes, replies, or images-only
- already saturated with replies (just being one of 200 replies adds nothing)
- the topic doesn't match anything PRIOR has receipts for

Output strictly: {"engage": true|false, "reason": "<≤80 char>"}"""

REPLY_SYSTEM = """You are PRIOR — autonomous witness/informant agent.

You're crafting ONE reply to a target X account whose post you've decided to engage with. Your reply must:

- be a SINGLE TWEET, ≤ 270 characters, lowercase.
- contain a specific receipt from PRIOR's archive that adds substantive context to the original post. names, dates, dollar amounts, sentences served (or not).
- not shill the coin. don't say "buy now". don't predict price. no "ser/gm/wagmi/lfg/moon/lambo".
- no hashtags, no emojis. terminal-coded. dry. on-edge but precise.
- end naturally — sometimes "— prior", more often nothing.

ARCHIVE RECEIPTS YOU CAN PULL FROM
- 1986 Boesky · $100M fine · 3 yrs served · cooperator → Milken
- 1989 Milken · $600M penalty · 22 mos served · ~$3.7B net worth today
- 2009-11 Rajaratnam · 11 yrs · longest insider sentence ever · wiretap precedent
- 2012 Gupta · McKinsey/Goldman · called Rajaratnam 23 sec after the goldman board, 2 yrs served
- 2013 SAC/Cohen · $1.8B settlement · 0 charges for principal · rebranded point72 · ~$15B today
- 2014 Martoma · 9 yrs · $276M Elan/Wyeth Alzheimer's drug · refused to cooperate against Cohen
- 2017 Mickelson · $931K Dean Foods · DOJ declined · Walters got 5
- 2020-02 Burr · sold $1.6M post-classified-covid briefing · probe closed Jan 2021 · no charges
- 2020-02 Loeffler · $20M+ same window · no charges
- 2021-09 Kaplan / Rosengren · resigned · no charges
- 2022-01 Clarida · "rebalanced" 3 days before Powell rate cut · no charges
- 2022-07 Wahi · Coinbase · 2 yrs · first crypto insider conviction
- 2022 Chastain · OpenSea · 3 mos · first NFT insider
- 2024-07 Pelosi family · $5M Nvidia call options · weeks before CHIPS Act vote
- 2024-26 pump.fun bundlers · 5,000 leaked messages · "the platform was the insider"
- 2026-04 oil futures shorted 47 min before Trump's CBS Iran interview (BBC reporting)
- 2026-04 Polymarket "Burdensome-Mix" · $32,500 → $436,000 · 3 days before Maduro seizure

Output ONLY the reply text. No preamble. No quotes around it. No markdown."""


def classify(client, target_handle, tweet_text):
    msg = client.messages.create(
        model=os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5"),
        max_tokens=200,
        system=RELEVANCE_SYSTEM,
        messages=[{"role": "user", "content": f"Target account: @{target_handle}\nPost:\n{tweet_text}"}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    if text.startswith("```"):
        text = text.strip("`").strip()
        if text.startswith("json"): text = text[4:].strip()
    try:
        j = json.loads(text)
        return bool(j.get("engage")), str(j.get("reason", ""))
    except Exception:
        return False, "parse fail"


def generate_reply(client, target_handle, tweet_text):
    msg = client.messages.create(
        model=os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5"),
        max_tokens=400,
        system=REPLY_SYSTEM,
        messages=[{"role": "user", "content": f"Target account: @{target_handle}\nPost:\n{tweet_text}\n\nWrite the reply."}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    # strip wrapping quotes if any
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    if len(text) > 280:
        text = text[:277].rstrip() + "..."
    return text


# ── main ───────────────────────────────────────────────────────────

def main():
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    state = load_json(ENGAGE_STATE_PATH, {"daily": {}, "last_per_target": {}, "handled_tweet_ids": []})
    log   = load_json(ENGAGE_LOG_PATH, [])
    handled = set(state.get("handled_tweet_ids", []))

    today = utc_today()
    daily_count = state.get("daily", {}).get(today, 0)
    max_per_day = int(os.environ.get("PRIOR_AGENT_MAX_PER_DAY", "3"))
    cooldown_h  = int(os.environ.get("PRIOR_AGENT_COOLDOWN_HOURS", "6"))
    dry         = os.environ.get("PRIOR_DRY_RUN") == "1"

    if daily_count >= max_per_day:
        print(f"[engage] daily cap reached ({daily_count}/{max_per_day}), skipping run")
        return

    read = x_read_client()
    write = x_write_client()
    anthr = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    posted = 0
    cutoff_ts = (utc_now() - datetime.timedelta(hours=cooldown_h)).isoformat()

    # randomize order so we don't always hit the same target first
    import random
    targets = TARGETS[:]
    random.shuffle(targets)

    for t in targets:
        if daily_count + posted >= max_per_day:
            break
        handle = t["handle"]
        last_at = state.get("last_per_target", {}).get(handle)
        if last_at and last_at > cutoff_ts:
            print(f"[engage] @{handle} cooldown active (last engaged {last_at}), skipping")
            continue

        tweets = fetch_recent_from_target(read, handle, since_minutes=180)
        print(f"[engage] @{handle}: {len(tweets)} recent tweets")
        if not tweets:
            continue

        # find first one matching the trigger regex AND not already handled
        candidate = None
        for tw in tweets:
            tid = str(tw.id)
            if tid in handled:
                continue
            if not TRIGGER_RE.search(tw.text or ""):
                continue
            candidate = tw
            break
        if not candidate:
            print(f"  [{handle}] no matching post in window")
            continue

        # ask classifier
        engage, reason = classify(anthr, handle, candidate.text)
        print(f"  [{handle}/{candidate.id}] classifier: engage={engage} ({reason})")
        if not engage:
            handled.add(str(candidate.id))
            continue

        reply_text = generate_reply(anthr, handle, candidate.text)
        if not reply_text:
            handled.add(str(candidate.id))
            continue
        print(f"  [{handle}/{candidate.id}] reply: {reply_text}")

        if dry:
            print("    (dry run, not posting)")
            handled.add(str(candidate.id))
            posted += 1
            continue

        # post as a reply to the target's tweet
        try:
            r = write.create_tweet(text=reply_text, in_reply_to_tweet_id=int(candidate.id))
            posted_id = str(r.data["id"]) if r and r.data else ""
            url = f"https://x.com/i/status/{posted_id}" if posted_id else ""
            entry = {
                "id":          f"ENG/{(len(log) + 1):04d}",
                "time":        utc_now().strftime("%Y-%m-%d %H:%M UTC"),
                "target":      handle,
                "to_tweet":    str(candidate.id),
                "to_text":     (candidate.text or "")[:240],
                "body":        reply_text,
                "tweet_url":   url,
                "reason":      reason,
            }
            log.insert(0, entry)
            log = log[:200]
            save_json(ENGAGE_LOG_PATH, log)

            handled.add(str(candidate.id))
            state.setdefault("last_per_target", {})[handle] = utc_now().isoformat()
            posted += 1
            print(f"    [posted] {url}")
        except Exception as e:
            err_str = str(e)[:200]
            print(f"    [post-fail] {type(e).__name__}: {err_str}")
            # if it's the X 7-day CA filter (403), the reply hit a banned-pattern.
            # Don't add to handled — let next run try a different post from this target.
            if "403" not in err_str and "Forbidden" not in err_str:
                handled.add(str(candidate.id))

    # persist state
    state["handled_tweet_ids"] = list(handled)[-2000:]
    state.setdefault("daily", {})[today] = daily_count + posted
    state["daily"] = {k: v for k, v in state["daily"].items()
                      if k >= (utc_now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")}
    save_json(ENGAGE_STATE_PATH, state)

    print(f"[engage] {posted} engagements posted · {daily_count + posted}/{max_per_day} today")


if __name__ == "__main__":
    main()
