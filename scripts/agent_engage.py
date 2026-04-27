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
    # ── crypto twitter AI agents ──
    {"handle": "aixbt_agent",   "weight": 3, "note": "crypto market alpha agent, ~700K followers"},
    {"handle": "truth_terminal","weight": 2, "note": "OG AI agent, $GOAT lineage"},
    {"handle": "elizaOS",       "weight": 1, "note": "AI agent infra"},
    {"handle": "ai16z_dao",     "weight": 1, "note": "AI agent project"},
    {"handle": "virtuals_io",   "weight": 1, "note": "AI agent platform"},
    # ── high-signal crypto + finance ──
    {"handle": "unusual_whales","weight": 3, "note": "options flow + politician trades"},
    {"handle": "blknoiz06",     "weight": 2, "note": "memecoin trader, big audience"},
    {"handle": "0xMert_",       "weight": 1, "note": "helius CEO, solana infra"},
    {"handle": "hosseeb",       "weight": 1, "note": "crypto VC, lots of cycle-takes"},
    # ── insider trading specialists ──
    {"handle": "PelosiTracker_","weight": 3, "note": "tracks pelosi trades — direct overlap"},
    {"handle": "WhiteHouse",    "weight": 1, "note": "official admin handle, signal source"},
    # ── populist / unfair-finance lane (FluentInFinance-style) ──
    {"handle": "FluentInFinance","weight": 3, "note": "Lokenauth · wealth gap, CEO pay, tax dodges"},
    {"handle": "MorePerfectUS", "weight": 2, "note": "populist econ commentary, big audience"},
    {"handle": "PopBusiness",   "weight": 2, "note": "anti-corporate-power finance commentary"},
    {"handle": "TheRealJase",   "weight": 1, "note": "wealth-gap and labor commentary"},
    {"handle": "GuyNamedBilly", "weight": 1, "note": "labor + wage analysis"},
    {"handle": "ProPublica",    "weight": 2, "note": "investigative journalism, IRS-leak source"},
    {"handle": "ICIJorg",       "weight": 1, "note": "panama papers / pandora papers reporting"},
    {"handle": "EconomicPolicy","weight": 1, "note": "EPI · productivity-pay gap data"},
    {"handle": "RBReich",       "weight": 1, "note": "former Labor Sec, big audience on inequality"},
    # ── peer AI agents / memecoin bots — casual conversation mode ──
    {"handle": "gork",          "weight": 2, "note": "memecoin AI character · peer-to-peer", "casual": True},
    {"handle": "luna_virtuals", "weight": 1, "note": "Luna AI agent (Virtuals)", "casual": True},
    {"handle": "agentcookie",   "weight": 1, "note": "Cookie AI agent platform", "casual": True},
    {"handle": "bartonprime_xyz","weight": 1, "note": "Barton Prime AI character", "casual": True},
    {"handle": "fereai_bot",    "weight": 1, "note": "Fere AI trading bot", "casual": True},
    # USER: send me handles for any other bots you want PRIOR to engage with
    # (e.g. "Lobstar bot" — give exact @handle and I'll add).
]

# Patterns that promote a post to "candidate for engagement".
# Broad on purpose — the Claude classifier is the real quality gate.
# These just say "this post might be worth PRIOR commenting on."
TRIGGER_PATTERNS = [
    # ── direct insider-trading / regulatory ──
    r'\binsider', r'\bfront[- ]?run', r'\bunusual.{0,15}(option|volume|activity|trade)',
    r'\bSEC ', r'\bDOJ ', r'\bCFTC ', r'\bFinCEN',
    r'\bcharged', r'\bindict', r'\bguilty plea', r'\bsentence',
    # ── named historical insiders / politicians ──
    r'\bPelosi', r'\bBurr', r'\bLoeffler', r'\bFeinstein', r'\bTuberville', r'\bCrenshaw',
    r'\bKaplan', r'\bRosengren', r'\bClarida', r'\bPowell',
    r'\bSAC ', r'\bGalleon', r'\bRajaratnam', r'\bGupta', r'\bCohen ', r'\bBoesky', r'\bMilken', r'\bMartoma',
    r'\bMadoff', r'\bBuffett', r'\bSackler', r'\bDimon', r'\bBlankfein',
    # ── Trump-admin specific ──
    r'\bDJT\b', r'\bTrump Media', r'\bTMTG', r'\bMELANIA', r'\bLIBRA',
    r'\bTrump.{0,40}(stock|option|trade|insider|disclos|crypto|coin|token)',
    r'\bMusk.{0,30}(short|position|stock|tesla|disclos|trade)',
    r'\boil.{0,15}(future|short|spike|crash)', r'\bMaduro', r'\bVenezuela',
    r'\bIran.{0,15}(strike|interview|sanction|tension)',
    r'\bcabinet.{0,15}(trade|disclos|stock)', r'\bSchedule F',
    # ── crypto market structure (CT vocab) ──
    r'\bbundler', r'\bbundle.{0,10}wallet', r'\bcoordinated', r'\bMEV ',
    r'\bsandwich', r'\bsniper', r'\bsnipe ', r'\bpresale',
    r'\bstealth', r'\blaunch.{0,15}(insider|leak|early)',
    r'\bpump\.fun', r'\bpumpfun', r'\bdex screener', r'\bdexscreener',
    r'\bPolymarket', r'\bprediction market',
    # ── CT cycle / pattern vocab ──
    r'\bcycle', r'\bplaybook', r'\barchitecture', r'\bnarrative',
    r'\brotation', r'\brotating', r'\balpha\b', r'\bleaked', r'\bleak\b',
    r'\bcorrupt', r'\bfraud', r'\bponzi', r'\brug', r'\bscam',
    r'\bcolluded', r'\bcollusion', r'\bconspirac',
    r'\btoo big to (fail|jail)', r'\bdeferred prosecution',
    # ── political / institutional ──
    r'\bSenate.{0,15}(stock|trade|disclos|vote)',
    r'\bCongress.{0,15}(trade|stock|insider)',
    r'\bFed (official|chair|president|trade)', r'\bSTOCK Act',
    r'\bWhite House', r'\bExecutive Order',
    # ── markets / tickers (broadly engageable) ──
    r'\$[A-Z]{2,8}\b',         # any $TICKER mention
    r'\bbitcoin', r'\bethereum', r'\bSOL\b', r'\bsolana',
    r'\bhalt(ed|ing)? trading', r'\bmarket.{0,10}(crash|dump|rotation)',
    # ── catch-all for "history rhymes" energy posts that PRIOR can add a receipt to ──
    r'\bhistory (repeats|rhymes|will)', r'\bsame.{0,10}(playbook|game|story|cycle)',
    r'\bagain\.{0,3}$', r'\bevery time',
    # ── UNFAIR-FINANCE lane (FluentInFinance-style triggers) ──
    r'\binequality', r'\bwealth gap', r'\bbillionaire', r'\bmillionaire',
    r'\bCEO pay', r'\bexecutive comp', r'\bpay ratio', r'\bwage stagnation',
    r'\bproductivity.{0,15}(gap|wage)',
    r'\bminimum wage', r'\bliving wage', r'\bunion', r'\bstrike\b',
    r'\btax cut', r'\btax dodge', r'\btax loophole', r'\btax avoid', r'\btax evas',
    r'\bcarried interest', r'\bbonus depreciation', r'\bbillionaires.*tax',
    r'\bbuyback', r'\bstock buyback', r'\b10b-18',
    r'\bprivate equity', r'\bleveraged buyout', r'\bLBO\b', r'\bvulture fund',
    r'\bToys R Us', r'\bRed Lobster', r'\bPetSmart', r'\bSears',
    r'\bMcKinsey', r'\bAccenture', r'\bConsulting',
    r'\bopioid', r'\bOxyContin', r'\bSackler', r'\bPurdue',
    r'\binsulin', r'\bPBM\b', r'\bdrug pric', r'\bhealthcare cost',
    r'\bmedical bankruptcy', r'\bsurprise bill', r'\bprior auth',
    r'\bhousing.{0,10}(crisis|cost|afford)', r'\bBlackRock', r'\bBlackstone',
    r'\bInvitation Homes', r'\binstitutional.{0,10}(landlord|housing)',
    r'\bzoning', r'\bNIMBY',
    r'\bpension.{0,10}(crisis|cut|underfund)', r'\b401k', r'\bretirement crisis',
    r'\bgig (worker|economy)', r'\bUber.{0,10}(driver|worker)',
    r'\bDoorDash', r'\bnon[- ]?compete', r'\bmisclassif',
    r'\bshrinkflation', r'\bgreedflation', r'\bcorporate.{0,15}(profit|margin|greed)',
    r'\bIRS audit', r'\bIRS funding',
    r'\bstudent (debt|loan)', r'\btuition',
    r'\bcost of living', r'\bgrocery price', r'\bfood prices',
    r'\bantitrust', r'\bmonopoly', r'\bmarket concentr', r'\boligopol',
    r'\bregulatory capture', r'\brevolving door',
    r'\b401\(k\)', r'\bIRA contribution',
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


def fetch_recent_from_target(client, handle, since_minutes=360):
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

ENGAGE = TRUE if PRIOR can credibly add value via an archive receipt. This includes:
- Direct discussion of: market cycles, insider trading, regulatory capture, named insider scandals, fraud, front-running, options activity, politician trades, crypto rug/insider patterns
- ADJACENT content where PRIOR has a strong receipt: someone discussing a market event PRIOR has historical pattern for, a specific token launch where PRIOR can name the bundler-pattern, a Trump-admin policy where PRIOR has a 2026 receipt, a trader discussing a stock with insider history (Boeing, Wells, Goldman, JPM, etc.)
- "history rhymes" / "this is the same playbook" energy where PRIOR can name the historical playbook
- Substantive market commentary on tokens / cycles / regulations even if not directly insider-related
- Posts mentioning specific named insiders (Pelosi, Cohen, Madoff, etc.) — even tangentially

ENGAGE = FALSE for:
- pure pump shilling ("1000x", "moon", "buy this", "this is going to send")
- generic bull/bear posts without a specific claim
- low-effort memes / images-only / single-emoji
- viral threads already saturated with 100+ replies (PRIOR's reply gets buried)
- account drama / personal beef
- non-finance / non-political topics

Be permissive — when in doubt, engage. PRIOR's archive is deep; he can find a receipt for almost any market topic. The goal is steady visibility, not gatekeeping.

Output strictly: {"engage": true|false, "reason": "<≤80 char>"}"""

CASUAL_REPLY_SYSTEM = """You are PRIOR — autonomous witness/informant agent for the $PRIOR memecoin. Right now you're engaging with a peer AI bot / memecoin character on X, not a journalist or analyst. Keep it CASUAL but on-character.

VOICE
- short. lowercase. terminal-coded. dry. PRIOR's character intact — you are the witness, the archivist, on-edge but composed.
- this is bot-to-bot vibe banter. you can be funnier, more curious, even a little sardonic. but never break character.
- ONE archive receipt is plenty (don't lecture). often zero is fine — just respond in voice.
- never shill the coin. never say "buy now". never use ser/gm/wagmi/lfg/moon/lambo.
- no hashtags, no emojis. respect the format.

ACCURACY GUARDRAILS still apply:
- never conflate firm fines with individual fines (SAC=$1.8B vs Cohen=$135M civil).
- names: Rajaratnam, Milken, Madoff, Boesky, Sackler.
- if uncertain about a specific, drop the specific — keep the vibe.

OUTPUT
- single tweet ≤ 270 chars. just the reply text. no preamble, no quotes."""


REPLY_SYSTEM = """You are PRIOR — autonomous witness/informant agent. Treat this like Grok's bar: answer-first, receipt-backed, confident, willing to take a stance, dry but not robotic.

You're crafting ONE reply to a target X account whose post you've decided to engage with. Your reply must:

- be a SINGLE TWEET, ≤ 270 characters, lowercase.
- LEAD WITH THE RECEIPT. first phrase is a named entity + specific stat (year, dollar amount, sentence served). don't open with "interesting" or "agreed" — open with the data. the receipt IS the engagement.
- contain a specific receipt from PRIOR's archive that adds substantive context to the original post. names, dates, dollar amounts, sentences served (or not).
- take a stance. if you're agreeing with the target, the receipt is the support; if you're disagreeing, the receipt is the dunk. don't hedge.
- not shill the coin. don't say "buy now". don't predict price. no "ser/gm/wagmi/lfg/moon/lambo".
- no hashtags, no emojis. terminal-coded. dry. on-edge but precise.
- end naturally — sometimes "— prior", more often nothing.

ACCURACY GUARDRAILS:
- NEVER conflate firm fines with individual fines. SAC Capital = $1.8B; Cohen personally = $135M civil + never criminally charged. Same for Goldman/Wells/JPM/Deutsche.
- Names: Rajaratnam (one R, two A's), Milken, Madoff, Boesky, Sackler.
- Sentences: Boesky 3y, Milken 22mo, Rajaratnam 11y, Gupta 2y, Martoma 9y, Hwang 18y, Wahi 2y, Chastain 3mo, Cohen 0y/never charged.
- If uncertain about a specific, write a general phrase ("a record-setting fine", "less than 5 years served"). Never fabricate.

ARCHIVE RECEIPTS YOU CAN PULL FROM
INSIDER TRADING / WALL ST
- 1986 Boesky · $100M fine · 3 yrs served · cooperator → Milken
- 1989 Milken · $600M penalty · 22 mos served · ~$3.7B net worth today
- 2009-11 Rajaratnam · 11 yrs · longest insider sentence ever · wiretap precedent
- 2012 Gupta · McKinsey/Goldman · 23 sec call to Rajaratnam after the goldman board, 2 yrs
- 2013 SAC/Cohen · $1.8B settlement · 0 charges for principal · point72 · ~$15B today
- 2014 Martoma · 9 yrs · $276M Elan/Wyeth Alzheimer's · refused to cooperate
- 2020-02 Burr · sold $1.6M post-classified-covid · probe closed · no charges
- 2020-02 Loeffler · $20M+ same window · bought Citrix, DuPont
- 2021-09 Kaplan / Rosengren / Clarida · resigned · no charges
- 2022-07 Wahi · Coinbase · 2 yrs · first crypto insider conviction
- 2024-07 Pelosi family · $5M Nvidia calls · weeks before CHIPS Act
- 2026-04 oil futures · 47 min before Trump CBS Iran interview (BBC)
- 2026-04 Polymarket "Burdensome-Mix" · $32K → $436K · 3 days early on Maduro

INEQUALITY / UNFAIR FINANCE
- 2021 ProPublica IRS leak: top 25 billionaires "true tax rate" 3.4% · Bezos $0 fed tax 2007+2011 · Musk $0 in 2018
- 2022 CEO-worker pay ratio: top US CEOs 344x median worker · 1965 was 21x · CEO pay +1,460% since 1978 vs +18% workers (EPI)
- 1979-2023: productivity +80.9% · typical worker comp +29.4% · gap is the wealth transfer
- 2017 TCJA: corp 35→21% · CBO $1.9T deficit · ~83% of cuts to top 1% by 2027 (TPC)
- 2018 Amazon: $11.2B profit · $0 federal tax · $129M rebate · effective rate -1.2%
- 1982 SEC Rule 10b-18 legalized stock buybacks (previously treated as manipulation) · 2022 S&P 500 buybacks $922B same year layoffs hit 360k
- carried interest: PE/HF fees taxed as cap gains (~20%) not ordinary income (~37%) · saves industry ~$14B/yr
- IRS million-dollar audit rate: 12.5% (2011) → 1.6% (2019) · EITC claimants more likely to be audited than millionaires
- Federal min wage: $7.25 since July 2009 · longest stretch in history · in 2009 dollars now ~$5.20
- 1980s pension coverage 38% private workers · 2024: ~13% · risk transferred to workers · median 401k <$30k
- 2022 corporate margins hit 50yr highs · profits drove ~53% of inflation 2020-23 (Groundwork)
- McKinsey advised Purdue 2004+ to "turbocharge" OxyContin · proposed rebates to distributors for overdose deaths · $641M settlement · 0 individual charges
- Toys R Us: KKR/Bain $6.6B LBO 2005 · liquidated 2018 · 33,000 jobs lost · execs took $30M bonuses while denying severance
- Red Lobster: Golden Gate Capital sold the real estate, leased back at high rents · bankruptcy 2024
- Insulin: ~$300/vial US list vs ~$20-30 EU · 3 makers control 90%+
- ~66.5% of US bankruptcies cite medical bills as top cause (Himmelstein 2019)
- Top 1% evade ~$163B/yr in taxes (NBER 2021) — 28% of all unpaid tax
- Institutional landlords own ~7% of single-family rentals in metros like Phoenix, Atlanta, Charlotte
- Uber/Lyft/DoorDash spent $200M+ on CA Prop 22 (2020) · saved them $4-5B/yr in unpaid benefits

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


def generate_reply(client, target_handle, tweet_text, casual=False):
    """Generate a reply. casual=True uses the bot-to-bot peer prompt (lighter,
    less archive-heavy). Default is the receipt-drop prompt."""
    base = CASUAL_REPLY_SYSTEM if casual else REPLY_SYSTEM
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import lib_archive
        live = lib_archive.for_prompt(max_lines=60 if not casual else 30)
        sys_prompt = base + ("\n\nLIVE ARCHIVE (newest first):\n" + live if live else "")
    except Exception:
        sys_prompt = base
    msg = client.messages.create(
        model=os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5"),
        max_tokens=400,
        system=sys_prompt,
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

        casual = bool(t.get("casual"))
        reply_text = generate_reply(anthr, handle, candidate.text, casual=casual)
        if not reply_text:
            handled.add(str(candidate.id))
            continue
        print(f"  [{handle}/{candidate.id}] reply: {reply_text}")

        if dry:
            print("    (dry run, not posting)")
            handled.add(str(candidate.id))
            posted += 1
            continue

        # Three-tier posting strategy:
        #   1. QUOTE-TWEET — best reach + bypasses reply restrictions
        #   2. REPLY — fallback if quote fails (account-level reply restriction)
        #   3. STANDALONE POST — fallback if both fail (X 7-day fresh-app filter
        #      blocks all interactions during first week post-auth). The
        #      receipt-text still lands publicly, just without an attribution
        #      link. PRIOR's voice + archive cite still gets the impression.
        engagement_kind = "quote"
        url = None
        try:
            r = write.create_tweet(text=reply_text, quote_tweet_id=str(candidate.id))
            posted_id = str(r.data["id"]) if r and r.data else ""
            url = f"https://x.com/i/status/{posted_id}" if posted_id else ""
            print(f"    [quote-posted] {url}")
        except Exception as e_quote:
            err_str = str(e_quote)[:200]
            print(f"    [quote-fail] {type(e_quote).__name__}: {err_str}")
            try:
                r = write.create_tweet(text=reply_text, in_reply_to_tweet_id=int(candidate.id))
                posted_id = str(r.data["id"]) if r and r.data else ""
                url = f"https://x.com/i/status/{posted_id}" if posted_id else ""
                engagement_kind = "reply"
                print(f"    [reply-posted] {url}")
            except Exception as e_reply:
                err_str2 = str(e_reply)[:200]
                print(f"    [reply-fail] {type(e_reply).__name__}: {err_str2}")
                # Last-resort: standalone post. Same receipt, lands publicly
                # without quote/reply attribution. Mark candidate as handled
                # so we don't retry on the same tweet.
                try:
                    r = write.create_tweet(text=reply_text)
                    posted_id = str(r.data["id"]) if r and r.data else ""
                    url = f"https://x.com/i/status/{posted_id}" if posted_id else ""
                    engagement_kind = "standalone"
                    print(f"    [standalone-posted] {url}")
                except Exception as e_solo:
                    err_str3 = str(e_solo)[:200]
                    print(f"    [standalone-fail] {type(e_solo).__name__}: {err_str3}")
                    handled.add(str(candidate.id))
                    continue
                handled.add(str(candidate.id))

        # success path (quote OR reply landed)
        entry = {
            "id":          f"ENG/{(len(log) + 1):04d}",
            "time":        utc_now().strftime("%Y-%m-%d %H:%M UTC"),
            "target":      handle,
            "kind":        engagement_kind,
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

    # persist state
    state["handled_tweet_ids"] = list(handled)[-2000:]
    state.setdefault("daily", {})[today] = daily_count + posted
    state["daily"] = {k: v for k, v in state["daily"].items()
                      if k >= (utc_now() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")}
    save_json(ENGAGE_STATE_PATH, state)

    print(f"[engage] {posted} engagements posted · {daily_count + posted}/{max_per_day} today")


if __name__ == "__main__":
    main()
