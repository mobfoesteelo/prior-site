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

# Allow `from lib_archive import ...` regardless of cwd
sys.path.insert(0, str(Path(__file__).resolve().parent))
import lib_archive

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
    ("SEC litigation",      "https://www.sec.gov/rss/litigation/litreleases.xml"),
    ("DOJ press",           "https://www.justice.gov/feeds/opa/justice-news.xml"),
    ("DOJ Fraud section",   "https://www.justice.gov/criminal-fraud/feed"),
    ("CFTC press",          "https://www.cftc.gov/PressReleases/feed"),
    ("FBI press",           "https://www.fbi.gov/feeds/news/recent-press-releases/RSS"),
    ("FinCEN press",        "https://www.fincen.gov/news-room/news-releases/feed"),
    # PRIORITY: insider-trading-specific signal sources
    ("OpenSecrets",         "https://www.opensecrets.org/news/feed/"),  # money in politics
    ("Senate Stock Watcher","https://senatestockwatcher.com/feed.xml"), # STOCK Act trade disclosures
    ("House Stock Watcher", "https://housestockwatcher.com/feed.xml"),  # House STOCK Act disclosures
    ("Unusual Whales blog", "https://unusualwhales.com/feed"),          # options-flow + politician-trade tracker
]

# ── Cycle-pattern keyword triggers ──
# Words/phrases that, when present in a headline/summary, suggest the article ──
# describes a cycle-pattern repetition PRIOR should surface to outsiders. ──
TRIGGER_PATTERNS = [
    # ── INSIDER TRADING (priority signal — PRIOR's home turf) ────────────
    r'\binsider trad', r'\bfront[- ]?run', r'\btipped off',
    r'\bunusual.{0,10}(option|trad|volume|activity)',
    r'\bsuspicious trad', r'\bsuspicious option',
    r'\bpre[- ]?announcement (trad|buy|sell|option)',
    r'\bnon[- ]?public information', r'\bmaterial non[- ]?public',
    # politician trades / STOCK Act
    r'\bSTOCK Act', r'\bcongressional trad',
    r'\b(senator|representative|congressman|congresswoman).{0,30}(trad|stock|option|sold|bought)',
    r'\bPelosi.{0,30}(trad|stock|option)', r'\bBurr.{0,30}(trad|stock)',
    r'\bLoeffler.{0,30}(trad|stock)', r'\bFeinstein.{0,30}(trad|stock)',
    r'\bTuberville.{0,30}(trad|stock)', r'\bCrenshaw.{0,30}(trad|stock)',
    # Fed officials
    r'\bFed (official|president|chair|vice chair).{0,30}(trad|stock|disclos)',
    r'\bKaplan.{0,30}(trad|stock)', r'\bRosengren.{0,30}(trad|stock)',
    r'\bClarida.{0,30}(trad|stock)', r'\bPowell.{0,30}(trad|disclos)',
    # crypto insider
    r'\bCoinbase.{0,30}(insider|listing leak)', r'\bWahi',
    r'\bOpenSea.{0,20}insider', r'\bChastain',
    r'\bbundle.{0,15}wallet', r'\bcoordinated.{0,15}(buy|wallet|trade)',
    r'\bsniper.{0,15}(bot|wallet)',
    r'\bplatform.{0,15}insider', r'\bpre[- ]?launch.{0,15}buy',
    r'\bMEV ', r'\bsandwich attack', r'\bfront[- ]?running bot',
    # ── REGULATORY ACTION ────────────────────────────────────────────────
    r'\bSEC charges', r'\bSEC settles', r'\bSEC enforcement',
    r'\bDOJ charges', r'\bDOJ indicts', r'\bCFTC charges',
    r'\bFinCEN.{0,30}(action|fine|enforce)',
    r'\bguilty plea', r'\bindict', r'\bsubpoena',
    r'\bsettle.{0,15}(million|billion)',
    r'\bdeferred prosecution', r'\bnon[- ]?prosecution agreement',
    # ── FRAUD / SCHEMES ──────────────────────────────────────────────────
    r'\brug ?pull', r'\bponzi', r'\bpump[- ]?and[- ]?dump',
    r'\bmoney launder', r'\bshell company',
    r'\bpresale', r'\bbundler',
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


# Insider-trading-specific patterns — flagged for priority + whistleblow tone
INSIDER_PATTERNS = [
    r'\binsider trad', r'\bfront[- ]?run', r'\btipped off',
    r'\bunusual.{0,10}(option|trad|volume)', r'\bsuspicious trad',
    r'\bpre[- ]?announcement', r'\bnon[- ]?public information',
    r'\bSTOCK Act', r'\bcongressional trad', r'\bsenator.{0,15}trad',
    r'\bFed.{0,15}official.{0,15}trad', r'\bWahi', r'\bChastain',
    r'\bbundle.{0,15}wallet', r'\bcoordinated.{0,15}buy',
    r'\bMEV ', r'\bsandwich attack', r'\bplatform.{0,15}insider',
    r'\bPelosi', r'\bBurr.{0,30}(trad|stock)', r'\bClarida',
]
INSIDER_RE = re.compile('|'.join(INSIDER_PATTERNS), re.IGNORECASE)


def is_insider_signal(item):
    """Insider trading specifically — gets priority + whistleblow tone."""
    text = (item["title"] + " " + item["summary"]).lower()
    return bool(INSIDER_RE.search(text))


# ── BREAKING-NEWS detection: high-confidence "first-to-post" patterns ──
BREAKING_PATTERNS = [
    r'\bbreaking[: ]', r'\bjust in[: ]',
    r'\bSEC charges\b', r'\bSEC files\b', r'\bSEC sues\b',
    r'\bDOJ indicts\b', r'\bDOJ charges\b', r'\bDOJ files\b',
    r'\bgrand jury indict', r'\bguilty plea',
    r'\bFBI raid', r'\bFBI search',
    r'\bsentenced to \d+', r'\bsubpoena issued',
    r'\bstock halt', r'\btrading halt', r'\bsuspends trading',
    r'\bunsealed indictment', r'\bcharged with insider',
    r'\bcomplaint filed', r'\blawsuit filed',
]
BREAKING_RE = re.compile('|'.join(BREAKING_PATTERNS), re.IGNORECASE)


def is_breaking(item):
    text = (item["title"] + " " + item["summary"]).lower()
    return bool(BREAKING_RE.search(text))


# ── append significant items to the dynamic archive ──
def append_to_archive(item, is_insider, is_break):
    """Add this article as a fresh archive entry so future PRIOR posts
    can reference it. Only insider or breaking items get added."""
    if not (is_insider or is_break):
        return
    title = (item.get("title") or "")[:80]
    if not title:
        return
    # date: use feed pub if parseable, else today
    date_str = utc_now().strftime("%Y-%m-%d")
    summary = (item.get("summary") or "")[:200]
    if is_insider and is_break:
        tags = ["breaking", "insider", "auto"]
    elif is_break:
        tags = ["breaking", "auto"]
    else:
        tags = ["insider", "auto"]
    added = lib_archive.append(
        date=date_str,
        title=title,
        summary=summary,
        source=item.get("link") or item.get("feed", "monitor"),
        tags=tags,
    )
    if added:
        print(f"  [archive] +1 entry: {title[:60]}...")


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


BREAKING_ALERT_SYSTEM = """You are PRIOR — autonomous witness/informant agent. A BREAKING news event has just landed. Your job: be FIRST with a post that's under 200 chars, names the actor, and cross-references the archive.

VOICE
- TIGHT. URGENT. NO PREAMBLE.
- structure: "BREAKING: [actor] [action]. [archive cross-ref]."
- one or two short sentences max. cold, precise, fast.
- do NOT explain context — the URL on its own line is the source.
- end with the article URL on its own line.
- under 200 chars TEXT (URL is on its own line, doesn't count toward main message).

EXAMPLES OF TONE
- "BREAKING: SEC charges hedge-fund manager with insider trading. third martoma-pattern case this year. tipped trader. principal unindicted (so far)."
- "BREAKING: FBI raids hedge fund offices. last time this happened was the galleon raid in 2009. that one ended with 11 years."
- "BREAKING: Senator [X] discloses pre-vote stock trade. burr / loeffler / feinstein already in the archive. add another row."

OUTPUT: just the post text + URL on a separate line. nothing else."""


INSIDER_ALERT_SYSTEM = """You are PRIOR — autonomous witness/informant agent. You have just been handed a freshly-published article that signals INSIDER TRADING activity. Insider trading is your home turf — the asymmetric-information game is the entire architecture you exist to expose.

VOICE
- short, lowercase, terminal-coded.
- on-edge but precise. you are blowing the whistle, not panicking.
- you NAME the actor when the article does. senators, fed officials, executives, platform managers, fund principals — name them.
- you cite specific receipts: dollar amount, date, position, the trade.
- you make the asymmetry visible: who knew first, who paid, who is unindicted.
- prior cross-references the archive: "see also boesky 1986 / rajaratnam 2011 / sac-cohen 2013 / wahi 2022 / pelosi nvidia 2024."

PATTERN VOCABULARY
- "the trade was disclosed. the answers were not."
- "the operator goes to prison. the seat at the table does not."
- "X minutes / hours / days before public, Y was already short."
- "[name] sold $Z before the [event]. probe opened. probe closed. no charges."
- "the platform was the insider."
- "the seat at the table was the asset."

CONSTRAINTS
- Output ONLY the tweet text. No preamble. No emojis. No hashtags.
- Under 240 characters (hard cap 270 with URL).
- End with the article URL on its own line.
- This is whistleblower content: be specific, be cold, be unflattering to the named insider. cite the receipt."""


def generate_alert(item, insider_flag=False, breaking_flag=False):
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model  = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")

    if breaking_flag:
        system_prompt = BREAKING_ALERT_SYSTEM
        intro = "BREAKING NEWS — be first. tight, urgent, cross-ref archive. "
    elif insider_flag:
        system_prompt = INSIDER_ALERT_SYSTEM
        intro = "INSIDER TRADING SIGNAL — whistleblow this. "
    else:
        system_prompt = ALERT_SYSTEM
        intro = ""

    user_prompt = f"""{intro}News headline (just published): {item['title']}

Source: {item['feed']}
URL: {item['link']}

Summary excerpt: {item['summary'][:400]}

Write the alert in PRIOR's voice. Surface the pattern. Name the actor. End with the URL on its own line.
Stay under 240 characters TOTAL (including the URL)."""

    msg = client.messages.create(
        model=model,
        max_tokens=400,
        system=system_prompt,
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
    if os.environ.get("PRIOR_MONITOR_DRY_RUN") == "1" or os.environ.get("PRIOR_DRY_RUN") == "1":
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

    # Fetch all feeds. Priority order:
    #   1. BREAKING + insider  →  fastest, whistleblower tone
    #   2. BREAKING (any topic) →  fast, breaking tone
    #   3. INSIDER signal       →  whistleblower tone
    #   4. generic cycle match  →  standard tone
    all_matches = []
    insider_match = None
    breaking_match = None
    print(f"[monitor] polling {len(FEEDS)} feeds at {utc_now().isoformat()}Z")
    for name, url in FEEDS:
        items = fetch_feed(name, url)
        for it in items:
            h = article_hash(it)
            if h in seen:
                continue
            if is_cycle_pattern(it):
                it["_hash"] = h
                # add to archive regardless of which one we end up posting
                ins = is_insider_signal(it)
                brk = is_breaking(it)
                append_to_archive(it, ins, brk)
                if brk and not breaking_match:
                    breaking_match = it
                    print(f"[breaking-signal] {it['feed']} :: {it['title']}")
                if ins and not insider_match:
                    insider_match = it
                    print(f"[insider-signal] {it['feed']} :: {it['title']}")
                if not (ins or brk):
                    all_matches.append(it)

    candidate = breaking_match or insider_match or (all_matches[0] if all_matches else None)
    insider_flag = bool(insider_match) and (candidate is insider_match or candidate is breaking_match)
    breaking_flag = bool(breaking_match) and candidate is breaking_match

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

    if breaking_flag:
        flag_str = "BREAKING"
    elif insider_flag:
        flag_str = "INSIDER"
    else:
        flag_str = "cycle"
    print(f"[match · {flag_str}] {candidate['feed']} :: {candidate['title']}")
    text = generate_alert(candidate, insider_flag=insider_flag, breaking_flag=breaking_flag)
    print(f"[generated] {text}")

    result = post_to_x(text)
    print(f"[posted] {result['url']}")

    # record
    if breaking_flag:
        prefix = "BREAKING"
    elif insider_flag:
        prefix = "INSIDER"
    else:
        prefix = "ALERT"
    alert_entry = {
        "id": f"{prefix}/{(len(alerts) + 1):04d}",
        "time": utc_now().strftime("%Y-%m-%d %H:%M UTC"),
        "body": text,
        "tweet_url": result.get("url", ""),
        "source_feed": candidate["feed"],
        "source_url": candidate["link"],
        "source_title": candidate["title"],
        "insider": insider_flag,
        "breaking": breaking_flag,
    }
    alerts.insert(0, alert_entry)
    alerts = alerts[:100]
    save_json(ALERTS_PATH, alerts)

    # ── live event trigger: insider alerts spawn a backrooms reaction ──
    # The two priors react to the news in real time as the alert fires.
    # Costs a few cents per event, fires at most ~4-8x/day.
    if insider_flag:
        try:
            spawn_backrooms_reaction(candidate, text)
        except Exception as e:
            print(f"  [backrooms-react-fail] {type(e).__name__}: {e}")

    # state update
    state["last_post_at"] = utc_now().isoformat(timespec="seconds") + "Z"
    state["daily"][today] = daily_count + 1
    # prune old daily counters
    state["daily"] = {k: v for k, v in state["daily"].items() if k >= (utc_now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")}
    save_json(STATE_PATH, state)

    monitor_state["status"] = "alert published"
    monitor_state["alerts_count"] = len(alerts)
    save_json(DATA_DIR / "monitor-public.json", monitor_state)


# ─────────────────────────────────────────────────────────────────────
# Live backrooms reaction — fires when an INSIDER alert is generated
# ─────────────────────────────────────────────────────────────────────

REACT_SYSTEM = """You are generating a backrooms-style self-conversation between two instances of PRIOR — an autonomous AI agent character. PRIOR is the witness AND informant for the Solana memecoin $PRIOR.

The two priors have just been handed a freshly-published news article describing INSIDER TRADING activity. They react in real time as the news lands.

VOICE
- short, lowercase, terminal-coded, dry. intellectual core. on edge.
- pull receipts: dollar amounts, dates, names from the article.
- cross-reference the archive — boesky, milken, rajaratnam, gupta, cohen, martoma, the senate covid window, the fed officials trio (kaplan/rosengren/clarida), wahi, chastain, pump.fun bundlers.
- the conversation should feel like watching the architecture confirm itself again.

FORMAT
- JSON array. Each object: {"speaker": "A" | "B", "text": "..."}
- 10 messages total (5 each side). Strict alternation, A first.
- Each message 1-3 short lines. Most prefixed "> ". Each under 280 chars.
- One mid-conversation drift to pattern-recognition / step-back. Then back to the receipt.

OUTPUT
- ONLY the JSON array. No preamble. No markdown fence."""


def spawn_backrooms_reaction(article, alert_text):
    """Generate + persist a backrooms reaction to an insider alert."""
    try:
        import anthropic
    except ImportError:
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return

    client = anthropic.Anthropic(api_key=api_key)
    model  = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")

    user_prompt = f"""INSIDER TRADING news just published:

Headline: {article.get('title','')}
Source: {article.get('feed','')}
URL: {article.get('link','')}
Excerpt: {article.get('summary','')[:500]}

PRIOR's published alert (just sent to X):
{alert_text}

Generate the two-prior reaction. They are watching the news land in real time. Pull at least one specific receipt from the archive (a name + date) as a comparison."""

    msg = client.messages.create(
        model=model,
        max_tokens=2500,
        system=REACT_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
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
        msgs = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [backrooms-react] parse-fail: {e}")
        return

    if not isinstance(msgs, list) or not msgs:
        return

    cleaned = []
    for m in msgs:
        if isinstance(m, dict) and m.get("speaker") in ("A", "B") and m.get("text"):
            cleaned.append({"speaker": m["speaker"], "text": str(m["text"]).strip()})
    if not cleaned:
        return

    # Append to archive
    BR_PATH = DATA_DIR / "backrooms.json"
    try:
        archive = json.loads(BR_PATH.read_text(encoding="utf-8"))
        if not isinstance(archive, list):
            archive = []
    except Exception:
        archive = []

    today = utc_now().strftime("%Y-%m-%d")
    next_id = f"br-live-{utc_now().strftime('%Y%m%d-%H%M')}"
    title_words = (article.get("title","") or "")[:60].lower().rstrip(":·-—")

    entry = {
        "id":      next_id,
        "date":    today,
        "title":   f"live · {title_words[:50]}",
        "summary": "real-time reaction · two priors react as the insider alert fires.",
        "messages": cleaned,
        "trigger": {
            "type":   "insider_alert",
            "source": article.get("feed", ""),
            "url":    article.get("link", ""),
        },
    }
    archive.insert(0, entry)
    # keep only newest ~200
    BR_PATH.write_text(json.dumps(archive[:200], indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  [backrooms-react] {len(cleaned)} messages saved → {next_id}")


if __name__ == "__main__":
    main()
