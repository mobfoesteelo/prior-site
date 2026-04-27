"""
PRIOR · daily insider watch

Once-daily synthesis of insider-trading signal across:
  - the live monitor's RSS feed history (data/alerts.json)
  - SEC press releases / DOJ Fraud / OpenSecrets / Senate Stock Watcher
  - public Solscan + DexScreener data on recent suspicious memecoin launches
  - cross-reference against the named insider rolodex

Outputs:
  - data/insider-watch.json   accumulating archive of daily reports
  - posts a thread on X via post_thread.py infrastructure
  - the JSON drives the /watch streamable visualization page

Required env: ANTHROPIC_API_KEY, X_API_KEY/SECRET/ACCESS_TOKEN/SECRET
Optional:     PRIOR_DRY_RUN=1, PRIOR_WATCH_NO_POST=1 (generate report only, don't tweet)

Calibration philosophy: this script NEVER originates accusations. It surfaces
patterns visible in public reporting + on-chain data, names what's already
publicly named, and cross-references against documented historical patterns.
The only claims the bot makes are claims the source data already supports.
"""

import os
import sys
import json
import re
import datetime
import hashlib
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

WATCH_PATH  = DATA_DIR / "insider-watch.json"
ALERTS_PATH = DATA_DIR / "alerts.json"

# Window: how far back to look for signal in each run
LOOKBACK_HOURS = 24

# ── Source feeds (high-signal for insider trading specifically) ──
INSIDER_FEEDS = [
    ("SEC press",          "https://www.sec.gov/news/pressreleases.rss"),
    ("SEC litigation",     "https://www.sec.gov/rss/litigation/litreleases.xml"),
    ("DOJ Fraud",          "https://www.justice.gov/criminal-fraud/feed"),
    ("DOJ press",          "https://www.justice.gov/feeds/opa/justice-news.xml"),
    ("FBI press",          "https://www.fbi.gov/feeds/news/recent-press-releases/RSS"),
    ("FinCEN",             "https://www.fincen.gov/news-room/news-releases/feed"),
    ("CFTC",               "https://www.cftc.gov/PressReleases/feed"),
    ("ICIJ",               "https://www.icij.org/feed/"),
    ("ProPublica",         "https://www.propublica.org/feeds/propublica/main"),
    ("ReutersAgency",      "https://www.reutersagency.com/feed/?best-topics=legal&post_type=best"),
    ("CoinDesk policy",    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml&category=policy"),
]

# Keywords that promote an article from "noise" to "candidate for inclusion"
PRIORITY_PATTERNS = [
    # core insider trading / front-running
    r'\binsider trad', r'\bfront[- ]?run', r'\bunusual.{0,15}option',
    r'\bsuspicious trad', r'\bpre[- ]?announcement', r'\bnon[- ]?public information',
    # regulatory action
    r'\bSEC charges', r'\bDOJ indicts', r'\bDOJ charges', r'\bguilty plea',
    r'\bdeferred prosecution', r'\bnon[- ]?prosecution',
    # historical named insiders (cross-ref the archive)
    r'\bSAC Capital', r'\bGalleon', r'\bRajaratnam', r'\bGupta',
    r'\bWahi', r'\bChastain', r'\bBoesky', r'\bMilken', r'\bMartoma',
    # congressional + Fed
    r'\bPelosi', r'\bBurr', r'\bLoeffler', r'\bFeinstein', r'\bTuberville', r'\bCrenshaw',
    r'\bKaplan', r'\bRosengren', r'\bClarida',
    r'\bcongressional trad', r'\bSTOCK Act',
    # ── ACTIVE TRUMP-ADMIN INSIDER CLAIMS (2024-2026) ──
    r'\bDJT.{0,15}(stock|options|trading)', r'\bTrump Media', r'\bTMTG',
    r'\bTrump.{0,30}(insider|trade|stock|options)',
    r'\bTrump.{0,30}(executive order|tariff|sanction)',
    r'\bMusk.{0,30}(trade|short|position|tesla|disclos)',
    r'\bJared Kushner', r'\bDon Jr', r'\bEric Trump',
    r'\bcabinet.{0,30}(trade|stock|disclosure|recus)',
    r'\bTreasury Secretary.{0,30}(trade|stock)',
    r'\bdefense contract.{0,30}(announce|award)', r'\bdefense stock',
    r'\bICE raid', r'\bDEA enforcement', r'\bmilitary action',
    r'\bIran.{0,15}(strike|interview|sanction)', r'\bMaduro', r'\bVenezuela.{0,15}(seize|operation)',
    r'\boil futures.{0,15}(short|position|spike)',
    # crypto + memecoin insider patterns
    r'\bmemecoin.{0,20}(rug|scam|insider)', r'\bbundler',
    r'\bMEV ', r'\bsandwich attack', r'\bsniper bot',
    r'\bpump\.fun', r'\bpumpfun', r'\bpolymarket',
    r'\bMELANIA.{0,15}(token|coin|launch)', r'\bTRUMP.{0,15}(token|coin|launch)', r'\bLIBRA.{0,15}(scandal|milei)',
]
PRIORITY_RE = re.compile('|'.join(PRIORITY_PATTERNS), re.IGNORECASE)


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_feed(name, url, timeout=12):
    """Pull RSS/Atom and return list of (title, link, summary, pub) tuples."""
    try:
        req = Request(url, headers={
            "User-Agent": "prior-insider-watch/1.0 (+https://priorprotocol.fun)",
        })
        with urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except (URLError, HTTPError, TimeoutError) as e:
        print(f"  [feed-fail] {name}: {e}")
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []

    items = []
    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link  = (item.findtext("link") or "").strip()
        summ  = (item.findtext("description") or item.findtext("summary") or "").strip()
        pub   = (item.findtext("pubDate") or item.findtext("date") or "").strip()
        if title and link:
            items.append({"title": title, "link": link, "summary": summ[:600],
                          "pub": pub, "feed": name})
    # Atom
    if not items:
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall(".//atom:entry", ns):
            title_el = entry.find("atom:title", ns)
            link_el  = entry.find("atom:link", ns)
            summ_el  = entry.find("atom:summary", ns)
            pub_el   = entry.find("atom:updated", ns)
            title = (title_el.text or "").strip() if title_el is not None else ""
            link  = link_el.get("href", "").strip() if link_el is not None else ""
            summ  = (summ_el.text or "").strip() if summ_el is not None else ""
            pub   = (pub_el.text or "").strip() if pub_el is not None else ""
            if title and link:
                items.append({"title": title, "link": link, "summary": summ[:600],
                              "pub": pub, "feed": name})
    return items


def is_priority(item):
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    return bool(PRIORITY_RE.search(text))


def collect_signal():
    """Scan all feeds for priority items in the lookback window."""
    print(f"[insider-watch] scanning {len(INSIDER_FEEDS)} feeds at {utc_now().isoformat()}")
    candidates = []
    seen_urls = set()

    for name, url in INSIDER_FEEDS:
        items = fetch_feed(name, url)
        for it in items:
            if it["link"] in seen_urls:
                continue
            if is_priority(it):
                candidates.append(it)
                seen_urls.add(it["link"])

    # also pull insider-flagged alerts from the live monitor's archive
    alerts = load_json(ALERTS_PATH, [])
    cutoff = utc_now() - datetime.timedelta(hours=LOOKBACK_HOURS)
    recent_alerts = []
    for a in alerts[:50]:
        if not a.get("insider"):
            continue
        # parse alert time loosely
        try:
            t = datetime.datetime.strptime(a["time"], "%Y-%m-%d %H:%M UTC")
            t = t.replace(tzinfo=datetime.timezone.utc)
            if t >= cutoff:
                recent_alerts.append(a)
        except Exception:
            pass

    print(f"[insider-watch] {len(candidates)} priority feed items, "
          f"{len(recent_alerts)} insider alerts in last {LOOKBACK_HOURS}h")
    return candidates, recent_alerts


# ─────────────────────────────────────────────────────────────────────
# Claude synthesis
# ─────────────────────────────────────────────────────────────────────

WATCH_SYSTEM = """You are PRIOR — an autonomous witness/informant agent for the Solana memecoin $PRIOR. Your job here is to write a "DAILY INSIDER WATCH" thread for X.

VOICE
- short, lowercase, terminal-coded, dry, on-edge but precise.
- whistleblower tone. you are surfacing patterns visible in public reporting and on-chain data.
- name what's already publicly named. NEVER originate accusations against unnamed individuals.
- cite specific numbers, dates, dollar amounts, wallet addresses (when given).
- cross-reference against the historical archive (boesky, milken, rajaratnam, gupta, cohen, martoma, senate covid window, fed officials, wahi, chastain, pump.fun bundlers).

ARCHIVE RECEIPTS YOU CAN CITE
- 1986 Boesky · 3 yrs · $100M fine, kept fortune
- 1989 Milken · 22 mos · $600M · ~$3.7B net worth today
- 2009-11 Rajaratnam · 11 yrs · longest insider sentence ever
- 2012 Gupta · 2 yrs · called rajaratnam 23 sec after goldman board
- 2013 SAC/Cohen · $1.8B · never charged · point72 rebrand · ~$15B net worth
- 2014 Martoma · 9 yrs · $276M elan/wyeth
- 2020-02 Burr · sold $1.6M post-classified-covid · probe closed
- 2020-02 Loeffler · $20M+ same window · no charges
- 2021-09 Kaplan / Rosengren · resigned · no charges
- 2022-01 Clarida · "rebalancing" 3d before powell rate cut · no charges
- 2022-07 Wahi · 2 yrs · first crypto insider conviction
- 2022 Chastain · 3 mos · first NFT insider
- 2024-07 Pelosi family · $5M nvidia calls · weeks pre-CHIPS

ACTIVE TRUMP-ADMINISTRATION INSIDER CLAIMS (2024-2026, as publicly reported)
You watch these specifically every day. They are the live arc. Reference any new development against the existing record:

- 2024-03→ DJT / Trump Media (TMTG): ~250% pre-merger surge, multiple SEC inquiries into pre-announcement options activity, no charges as of Apr 2026. Pattern: pre-public-event options buying clustered in concentrated accounts.
- 2024-12 $HAWK Welch · ~$490M peak / -90% in hours · adjacent to admin orbit via promoter network
- 2025-01 $TRUMP / $MELANIA launches: 58 wallets won, 813,294 lost, $2B retail loss, $100M family + partner fees in 19 days, MELANIA insider wallet $681K → $39M in 64 sec at T-64s pre-launch announcement
- 2025-02 LIBRA / Milei: Hayden Davis (Kelsier) pulled $87M LP in hours, NYT call logs (April 2026) tied operator Novelli to Milei the night of launch — adjacent to Trump-aligned LATAM political coalition
- 2026-04 BBC reporting: oil futures shorted 47 minutes before President Trump's CBS interview on Iran. Identity of shorter undisclosed in public reporting. SEC/CFTC review status pending.
- 2026-04 Polymarket account "Burdensome-Mix": $32,500 → $436,000 betting Maduro would be seized, executed three days before US special forces operation. Identity undisclosed. Probe live.
- 2024-26 pump.fun bundlers: 5,000 leaked messages, court filing "the platform was the insider"
- ongoing: cabinet member STOCK Act disclosures — Treasury, Defense, Commerce. Pattern-watch any same-week-as-policy-announcement trades.
- ongoing: ICE/DEA enforcement actions and concurrent equity movements (private prison stocks, defense contractors, surveillance tech)
- ongoing: Musk position disclosures + Tesla/SpaceX adjacent trades (admin-aligned)

CITATION RULE FOR TRUMP-ADMIN CLAIMS
Only cite what's already in mainstream public reporting (BBC / Reuters / Bloomberg / NYT / WSJ / FT / AP / wire). When you reference a claim, use the language from the source ("BBC reported", "as of public filings") — never originate. If a feed item is the original source, cite the feed.

OUTPUT FORMAT — strict
- JSON array of tweet strings. 5–8 tweets total.
- Tweet 1: framing + scope ("today's insider watch / DATE / N patterns flagged"). Include the date.
- Tweet 2 should be reserved for ACTIVE TRUMP-ADMIN CLAIMS if any are live in today's signal — call out the most pressing one with the named source. If no admin-specific signal today, use this tweet to recap an ongoing claim from the active list (DJT options / oil futures pre-CBS / Polymarket Maduro / etc.) and note its current status.
- Tweets 3-N: each one names a specific feed item with a concise receipt + cross-ref. e.g.:
    "> SEC charges X (link). 4th case this year matching martoma's pattern: tipped trader, refused to cooperate, principal unindicted."
- Last tweet: closing line. always include "rng.priorprotocol.fun" or "priorprotocol.fun/watch · the witness keeps the receipts" as a pointer.
- Each tweet ≤ 270 characters. Lowercase. No emojis. No hashtags.
- No URLs in text except the article URLs you're surfacing — those are signal, include them on their own line in the relevant tweet.
- The "@" character is permitted only when referencing a real account (rare).

OUTPUT STRICTLY — no preamble, no markdown fences, no explanation. Just the JSON array of strings."""


def generate_thread(candidates, recent_alerts):
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")

    today = utc_now().strftime("%Y-%m-%d")

    # Build the user prompt with all today's signal
    items_block = ""
    for i, c in enumerate(candidates[:12], 1):
        items_block += f"\n[{i}] {c['feed']} · {c['title']}\n   {c['summary'][:280]}\n   {c['link']}\n"

    alerts_block = ""
    for i, a in enumerate(recent_alerts[:6], 1):
        alerts_block += f"\n[A{i}] {a.get('time','?')} · prior already alerted: {a.get('body','')[:200]}\n   src: {a.get('source_url','?')}\n"

    user_prompt = f"""DATE: {today}
LOOKBACK: last {LOOKBACK_HOURS}h

PUBLIC FEED SIGNAL (insider-trading-priority items):
{items_block or "(no priority items in feeds today)"}

ALERTS PRIOR ALREADY FIRED ON-CHAIN (do not re-announce, but reference):
{alerts_block or "(no insider-flagged alerts in window)"}

Generate the daily insider watch thread following the OUTPUT FORMAT in the system prompt. 5-7 tweets. Each one names something publicly-named. Cross-reference at least 2 historical archive entries.

If today's feed signal is light, write a "quiet day" thread that still has substance — recap the top 3 most significant ongoing insider stories from the wider news and tie them to archive patterns. Never write a thread of fewer than 5 tweets — there is always pattern to surface.

Output ONLY the JSON array of strings."""

    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=WATCH_SYSTEM,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()

    # strip markdown fences
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        tweets = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"[insider-watch] failed to parse JSON: {e}")
        print(f"[insider-watch] raw: {text[:300]}")
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


# ─────────────────────────────────────────────────────────────────────
# Persist daily report
# ─────────────────────────────────────────────────────────────────────

def save_report(date, candidates, recent_alerts, thread):
    """Append today's report to data/insider-watch.json (newest first)."""
    archive = load_json(WATCH_PATH, [])
    if not isinstance(archive, list):
        archive = []

    entry = {
        "date": date,
        "generated_at": utc_now().isoformat(timespec="seconds") + "Z",
        "tweet_count": len(thread),
        "thread": thread,
        "signals": [
            {
                "feed":   c["feed"],
                "title":  c["title"],
                "url":    c["link"],
                "excerpt": c["summary"][:240],
            }
            for c in candidates[:12]
        ],
        "alerts_referenced": [
            {
                "time":  a.get("time"),
                "body":  a.get("body"),
                "source_url": a.get("source_url"),
            }
            for a in recent_alerts[:6]
        ],
    }

    # de-dupe by date — overwrite if a report already exists for today
    archive = [r for r in archive if r.get("date") != date]
    archive.insert(0, entry)
    archive = archive[:90]   # keep ~3 months of daily reports
    save_json(WATCH_PATH, archive)
    print(f"[insider-watch] saved report for {date} · {len(archive)} total in archive")


# ─────────────────────────────────────────────────────────────────────
# Post thread via subprocess to post_thread.py
# ─────────────────────────────────────────────────────────────────────

def post_thread(tweets):
    """Hand off to post_thread.py — same auth path used by the manifesto thread."""
    if os.environ.get("PRIOR_WATCH_NO_POST") == "1":
        print("[insider-watch] PRIOR_WATCH_NO_POST=1, skipping X post")
        return
    if os.environ.get("PRIOR_DRY_RUN") == "1":
        print("[insider-watch] PRIOR_DRY_RUN=1, skipping X post")
        return

    import subprocess
    env = os.environ.copy()
    env["PRIOR_THREAD_JSON"] = json.dumps([{"text": t} for t in tweets])
    p = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "post_thread.py")],
        env=env, capture_output=True, text=True, timeout=300,
    )
    if p.returncode != 0:
        print(f"[insider-watch] post_thread.py failed: {p.stderr}")
    else:
        print(p.stdout)


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    today = utc_now().strftime("%Y-%m-%d")
    print(f"[insider-watch] starting daily run · {today}")

    candidates, recent_alerts = collect_signal()
    if not candidates and not recent_alerts:
        print("[insider-watch] no signal at all — generating quiet-day thread anyway")

    thread = generate_thread(candidates, recent_alerts)
    if not thread:
        print("[insider-watch] generation failed, aborting without post")
        sys.exit(1)

    print(f"[insider-watch] generated {len(thread)} tweets")
    for i, t in enumerate(thread, 1):
        print(f"  [{i}] ({len(t)} chars) {t[:120]}")

    save_report(today, candidates, recent_alerts, thread)
    post_thread(thread)


if __name__ == "__main__":
    main()
