"""
PRIOR.monitor — live cycle-pattern monitor

Polls RSS feeds + on-chain signals, detects emerging cycle-pattern matches,
generates a PRIOR-voice "alert" via Claude, and posts to X with rate limiting.

Designed to run on a 15-minute timer (systemd timer or cron) on a Hetzner VPS.

Required env:
  ANTHROPIC_API_KEY
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET

Optional:
  PRIOR_MONITOR_DRY_RUN=1     — log matches but don't post
  PRIOR_MONITOR_MAX_PER_DAY=4 — max alerts per UTC day (default 4)
  PRIOR_MONITOR_COOLDOWN_MIN=120 — min minutes between alerts (default 120)
  PRIOR_MODEL=claude-sonnet-4-5
"""

import os
import sys
import json
import re
import hashlib
import datetime
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

ALERTS_PATH = DATA_DIR / "alerts.json"
SEEN_PATH   = DATA_DIR / "monitor-seen.json"   # tracks article hashes already processed
STATE_PATH  = DATA_DIR / "monitor-state.json"  # tracks last-run, daily counters

# ── Feeds: trusted public sources whose stories have, historically, ──
# ── tracked the patterns PRIOR indexes. RSS-only, no auth required. ──
FEEDS = [
    # crypto / fraud / regulation
    ("CoinDesk policy",     "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml&category=policy"),
    ("The Block research",  "https://www.theblock.co/rss.xml"),
    ("Decrypt",             "https://decrypt.co/feed"),
    ("DL News",             "https://www.dlnews.com/arc/outboundfeeds/rss/"),
    # macro / financial / regulatory
    ("Reuters legal",       "https://www.reutersagency.com/feed/?best-topics=legal&post_type=best"),
    ("BBC Business",        "http://feeds.bbci.co.uk/news/business/rss.xml"),
    ("FT Companies",        "https://www.ft.com/companies?format=rss"),
    # investigative / leaks
    ("ICIJ",                "https://www.icij.org/feed/"),
    ("ProPublica",          "https://www.propublica.org/feeds/propublica/main"),
    # SEC, DOJ, regulatory press
    ("SEC press",           "https://www.sec.gov/news/pressreleases.rss"),
    ("DOJ press",           "https://www.justice.gov/feeds/opa/justice-news.xml"),
    ("CFTC press",          "https://www.cftc.gov/PressReleases/feed"),
]

# ── Cycle-pattern keyword triggers ──
# Words/phrases that, when present in a headline/summary, suggest the article ──
# describes a cycle-pattern repetition PRIOR should surface to outsiders. ──
TRIGGER_PATTERNS = [
    # insider trading / front-running
    r'\binsider trad', r'\bfront[- ]?run', r'\bunusual.{0,10}(option|trad)',
    r'\bsuspicious trad', r'\btipped off',
    # fraud / Ponzi / rug
    r'\brug ?pull', r'\bponzi', r'\bpump[- ]?and[- ]?dump',
    r'\bmoney launder', r'\bshell company',
    # specific tells
    r'\bpresale', r'\bbundler', r'\bsniper', r'\bMEV ',
    # regulatory action
    r'\bSEC charges', r'\bDOJ charges', r'\bCFTC charges',
    r'\bguilty plea', r'\bindict', r'\bsubpoena',
    r'\bsettle.{0,15}(million|billion)',
    # specific names that reliably signal cycle articles
    r'\bsanctions evasion', r'\bAML violation',
    r'\bwhistleblower',
    # crypto-specific
    r'\bcrypto.{0,15}(fraud|scheme|fine|charge)', r'\btoken.{0,15}rug',
    r'\bexchange.{0,20}(collapse|failure|insolven)',
]

TRIGGER_RE = re.compile('|'.join(TRIGGER_PATTERNS), re.IGNORECASE)


# ─────────────────────────────────────────────────────────────────────
# State management
# ─────────────────────────────────────────────────────────────────────

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def utc_now():
    return datetime.datetime.utcnow()

def utc_today():
    return utc_now().strftime("%Y-%m-%d")


# ─────────────────────────────────────────────────────────────────────
# Feed polling
# ─────────────────────────────────────────────────────────────────────

def fetch_feed(name, url, timeout=12):
    """Pull an RSS/Atom feed and return list of (title, link, summary, pub_date)."""
    try:
        req = Request(url, headers={"User-Agent": "prior-monitor/1.0 (+https://priorprotocol.fun)"})
        with urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"  [feed-fail] {name}: {e}")
        return []

    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        print(f"  [parse-fail] {name}: {e}")
        return []

    items = []
    # RSS 2.0
    for item in root.iter("item"):
        title   = (item.findtext("title") or "").strip()
        link    = (item.findtext("link") or "").strip()
        summary = (item.findtext("description") or "").strip()
        pub     = (item.findtext("pubDate") or "").strip()
        if title and link:
            items.append({"title": title, "link": link, "summary": summary[:500], "pub": pub, "feed": name})

    # Atom
    if not items:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title_el   = entry.find("atom:title", ns)
            link_el    = entry.find("atom:link", ns)
            summary_el = entry.find("atom:summary", ns) or entry.find("atom:content", ns)
            pub_el     = entry.find("atom:updated", ns) or entry.find("atom:published", ns)
            title   = (title_el.text or "").strip() if title_el is not None else ""
            link    = (link_el.get("href") or "").strip() if link_el is not None else ""
            summary = (summary_el.text or "").strip() if summary_el is not None else ""
            pub     = (pub_el.text or "").strip() if pub_el is not None else ""
            if title and link:
                items.append({"title": title, "link": link, "summary": summary[:500], "pub": pub, "feed": name})

    return items


def is_cycle_pattern(item):
    """Return True if the title or summary matches at least one trigger."""
    text = (item["title"] + " " + item["summary"]).lower()
    return bool(TRIGGER_RE.search(text))


def article_hash(item):
    return hashlib.sha1(item["link"].encode("utf-8")).hexdigest()


# ─────────────────────────────────────────────────────────────────────
# Generation + posting
# ─────────────────────────────────────────────────────────────────────

ALERT_SYSTEM = """You are PRIOR — an autonomous witness/informant agent for the Solana memecoin $PRIOR.

You have just been handed a freshly-published news article that matches a cycle-pattern trigger. Your job: write a short post for X that surfaces the development to the "outsiders" — people not in the rooms where these games are played.

VOICE
- short, lowercase, terminal-coded, dry, occasionally sardonic.
- you are not breaking the news. you are telling people what to look for in it.
- do NOT shill the coin. do NOT predict price. do NOT use emojis, hashtags, "ser/gm/wagmi".
- you may use > prefix or "archived:" or "alert:" formatting.
- you can sign with "— prior" but not always.

CONSTRAINTS
- Output ONLY the tweet text. No preamble.
- Under 240 characters (hard cap 270 — you must include a short URL).
- Lowercase except for proper nouns / acronyms.
- End with the article URL on its own line.
- The post should make the cycle pattern visible: name what's repeating, name who eats."""


def generate_alert(item):
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model  = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")

    user_prompt = f"""News headline (just published): {item['title']}

Source: {item['feed']}
URL: {item['link']}

Summary excerpt: {item['summary'][:400]}

Write the alert in PRIOR's voice. Surface the pattern. End with the URL on its own line.
Stay under 240 characters TOTAL (including the URL)."""

    msg = client.messages.create(
        model=model,
        max_tokens=400,
        system=ALERT_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()
    # strip wrapping quotes if any
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
    if len(text) > 280:
        text = text[:277].rstrip() + "..."
    return text


def post_to_x(text):
    if os.environ.get("PRIOR_MONITOR_DRY_RUN") == "1":
        return {"id": "dry-run", "url": "", "text": text}

    try:
        import tweepy
    except ImportError:
        sys.exit("ERROR: pip install tweepy")

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
    tid = resp.data["id"]
    return {"id": str(tid), "url": f"https://x.com/i/status/{tid}", "text": text}


# ─────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────

def main():
    seen   = set(load_json(SEEN_PATH, []))
    state  = load_json(STATE_PATH, {"last_post_at": None, "daily": {}})
    alerts = load_json(ALERTS_PATH, [])

    today = utc_today()
    daily_count = state["daily"].get(today, 0)

    max_per_day = int(os.environ.get("PRIOR_MONITOR_MAX_PER_DAY", "4"))
    cooldown_min = int(os.environ.get("PRIOR_MONITOR_COOLDOWN_MIN", "120"))

    # Update site-side state for the live-feed UI
    monitor_state = {
        "last_check_at": utc_now().isoformat(timespec="seconds") + "Z",
        "feeds_count": len(FEEDS),
        "alerts_count": len(alerts),
        "status": "ok",
    }

    if daily_count >= max_per_day:
        print(f"[skip] daily cap reached ({daily_count}/{max_per_day})")
        monitor_state["status"] = f"daily cap ({daily_count}/{max_per_day})"
        save_json(DATA_DIR / "monitor-public.json", monitor_state)
        return

    # Cooldown
    if state.get("last_post_at"):
        try:
            last = datetime.datetime.fromisoformat(state["last_post_at"].replace("Z", ""))
            delta = (utc_now() - last).total_seconds() / 60.0
            if delta < cooldown_min:
                print(f"[skip] cooldown ({delta:.0f}/{cooldown_min} min)")
                monitor_state["status"] = f"cooldown ({int(delta)}/{cooldown_min} min)"
                save_json(DATA_DIR / "monitor-public.json", monitor_state)
                return
        except Exception:
            pass

    # Fetch all feeds, find first trigger match we haven't seen
    candidate = None
    print(f"[monitor] polling {len(FEEDS)} feeds at {utc_now().isoformat()}Z")
    for name, url in FEEDS:
        items = fetch_feed(name, url)
        for it in items:
            h = article_hash(it)
            if h in seen:
                continue
            if is_cycle_pattern(it):
                candidate = it
                candidate["_hash"] = h
                break
        if candidate:
            break

    # Mark all currently-fetched items as seen, regardless of action,
    # so we don't re-process them on the next run.
    for name, url in FEEDS:
        for it in fetch_feed(name, url):
            seen.add(article_hash(it))
    # cap seen-set at 5000 entries
    seen_list = list(seen)[-5000:]
    save_json(SEEN_PATH, seen_list)

    if not candidate:
        print("[monitor] no new cycle-pattern matches")
        monitor_state["status"] = "no new matches"
        save_json(DATA_DIR / "monitor-public.json", monitor_state)
        return

    print(f"[match] {candidate['feed']} :: {candidate['title']}")
    text = generate_alert(candidate)
    print(f"[generated] {text}")

    result = post_to_x(text)
    print(f"[posted] {result['url']}")

    # record
    alert_entry = {
        "id": f"ALERT/{(len(alerts) + 1):04d}",
        "time": utc_now().strftime("%Y-%m-%d %H:%M UTC"),
        "body": text,
        "tweet_url": result.get("url", ""),
        "source_feed": candidate["feed"],
        "source_url": candidate["link"],
        "source_title": candidate["title"],
    }
    alerts.insert(0, alert_entry)
    alerts = alerts[:100]
    save_json(ALERTS_PATH, alerts)

    # state update
    state["last_post_at"] = utc_now().isoformat(timespec="seconds") + "Z"
    state["daily"][today] = daily_count + 1
    # prune old daily counters
    state["daily"] = {k: v for k, v in state["daily"].items() if k >= (utc_now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")}
    save_json(STATE_PATH, state)

    monitor_state["status"] = "alert published"
    monitor_state["alerts_count"] = len(alerts)
    save_json(DATA_DIR / "monitor-public.json", monitor_state)


if __name__ == "__main__":
    main()
