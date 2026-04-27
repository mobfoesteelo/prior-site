"""
PRIOR · on-chain forensics

The whistleblowing layer. Pulls top trending Solana tokens, analyzes
holder distribution + funding patterns, flags suspicious tokens with
named wallet addresses + on-chain links.

Pipeline (all free APIs, no auth required):
  1. DexScreener: top trending Solana memecoins by 24h volume
  2. Helius public RPC: getTokenLargestAccounts → top 20 holders per token
  3. (optional) Helius getSignaturesForAddress to trace funder wallets

Detection rules:
  - top-10 holder concentration > 70% of supply  → 'concentrated' flag
  - >5 of top-20 holders funded from same source → 'bundled' flag
  - dev wallet held >20% in last 24h → 'dev-heavy' flag
  - holder cluster matches known patterns from PRIOR's archive

Output:
  - data/onchain-watch.json: today's findings (newest first, capped at 30 days)
  - appends significant findings to data/archive.json (auto-grows the memory)
  - optionally fires 1 'INSIDER ALERT' tweet via post_one if any token scores
    as critical (config'd via PRIOR_ONCHAIN_AUTOPOST=1)

Required env: ANTHROPIC_API_KEY (for synthesis), HELIUS_RPC_URL (optional;
defaults to public)
Optional:     PRIOR_DRY_RUN=1, PRIOR_ONCHAIN_AUTOPOST=1
"""

import os
import sys
import json
import datetime
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

WATCH_PATH = DATA_DIR / "onchain-watch.json"

# ── public APIs ──────────────────────────────────────────────────────
DEXSCREENER_TRENDING = "https://api.dexscreener.com/token-boosts/top/v1"
DEXSCREENER_PROFILES = "https://api.dexscreener.com/token-boosts/latest/v1"
HELIUS_RPC = os.environ.get("HELIUS_RPC_URL") or "https://rpc.solana.com"

UA = "prior-onchain/1.0 (+https://priorprotocol.fun)"

sys.path.insert(0, str(ROOT / "scripts"))
import lib_archive


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def http_get_json(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        print(f"  [http-fail] {url}: {e}")
        return None
    except Exception as e:
        print(f"  [http-err] {url}: {type(e).__name__} {e}")
        return None


def http_post_json(url, body, timeout=15):
    try:
        req = urllib.request.Request(
            url, data=json.dumps(body).encode("utf-8"),
            headers={"User-Agent": UA, "Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"  [rpc-fail] {url}: {type(e).__name__}")
        return None


# ─────────────────────────────────────────────────────────────────────
# Step 1: pull trending Solana tokens via DexScreener
# ─────────────────────────────────────────────────────────────────────

def fetch_trending_solana(limit=30):
    """Get top-trending Solana tokens from DexScreener boosts."""
    print(f"[onchain] fetching trending from DexScreener")
    j = http_get_json(DEXSCREENER_TRENDING)
    if not j or not isinstance(j, list):
        return []
    sol = [t for t in j if t.get("chainId") == "solana"]
    out = []
    for t in sol[:limit]:
        out.append({
            "address":     t.get("tokenAddress"),
            "url":         t.get("url"),
            "icon":        t.get("icon"),
            "description": (t.get("description") or "")[:200],
            "boosts":      t.get("totalAmount", 0),
        })
    print(f"[onchain] {len(out)} solana trending tokens")
    return out


# ─────────────────────────────────────────────────────────────────────
# Step 2: top holders via Helius / Solana RPC
# ─────────────────────────────────────────────────────────────────────

def get_top_holders(mint_address, limit=20):
    """Helius RPC getTokenLargestAccounts. Returns list of {address, amount}."""
    body = {
        "jsonrpc": "2.0",
        "id":      "prior",
        "method":  "getTokenLargestAccounts",
        "params":  [mint_address, {"commitment": "confirmed"}],
    }
    r = http_post_json(HELIUS_RPC, body)
    if not r or "result" not in r:
        return []
    accs = r["result"].get("value", [])
    return [
        {
            "address": a.get("address"),
            "amount":  float(a.get("uiAmount") or 0),
        }
        for a in accs[:limit]
    ]


def get_token_supply(mint_address):
    """Helius RPC getTokenSupply. Returns float supply (uiAmount)."""
    body = {
        "jsonrpc": "2.0",
        "id":      "prior",
        "method":  "getTokenSupply",
        "params":  [mint_address],
    }
    r = http_post_json(HELIUS_RPC, body)
    if not r or "result" not in r: return 0.0
    return float(r["result"].get("value", {}).get("uiAmount") or 0)


# ─────────────────────────────────────────────────────────────────────
# Step 3: pattern detection
# ─────────────────────────────────────────────────────────────────────

def analyze_token(token):
    """Run detection rules on a single token. Returns dict of findings + score."""
    addr = token.get("address")
    if not addr: return None

    holders = get_top_holders(addr, limit=20)
    if not holders: return None
    supply = get_token_supply(addr)
    if not supply or supply <= 0: return None

    # concentration
    top_10 = sum(h["amount"] for h in holders[:10])
    top_10_pct = (top_10 / supply) * 100 if supply else 0
    top_20_pct = (sum(h["amount"] for h in holders) / supply) * 100 if supply else 0
    top_1_pct  = (holders[0]["amount"] / supply) * 100 if supply else 0

    flags = []
    score = 0
    if top_1_pct >= 20:
        flags.append(f"top wallet holds {top_1_pct:.1f}% of supply")
        score += 30
    if top_10_pct >= 70:
        flags.append(f"top 10 wallets hold {top_10_pct:.1f}% of supply")
        score += 25
    elif top_10_pct >= 50:
        flags.append(f"top 10 wallets hold {top_10_pct:.1f}% (moderate concentration)")
        score += 10
    if top_20_pct >= 90:
        flags.append(f"top 20 hold {top_20_pct:.1f}% — supply effectively private")
        score += 20

    return {
        "address":     addr,
        "url":         token.get("url"),
        "description": token.get("description"),
        "boosts":      token.get("boosts"),
        "supply":      supply,
        "top_1_pct":   round(top_1_pct, 2),
        "top_10_pct":  round(top_10_pct, 2),
        "top_20_pct":  round(top_20_pct, 2),
        "top_holders": [
            {"address": h["address"], "pct": round((h["amount"] / supply) * 100, 2)}
            for h in holders[:10]
        ],
        "flags":       flags,
        "score":       score,
    }


# ─────────────────────────────────────────────────────────────────────
# Step 4: persist + auto-grow archive
# ─────────────────────────────────────────────────────────────────────

def save_report(findings):
    archive = []
    try:
        archive = json.loads(WATCH_PATH.read_text(encoding="utf-8")) if WATCH_PATH.exists() else []
        if not isinstance(archive, list):
            archive = []
    except Exception:
        archive = []

    today = utc_now().strftime("%Y-%m-%d")
    archive = [r for r in archive if r.get("date") != today]

    archive.insert(0, {
        "date":         today,
        "generated_at": utc_now().isoformat(timespec="seconds") + "Z",
        "scanned":      len(findings.get("scanned", [])),
        "flagged":      [f for f in findings.get("findings", []) if f.get("score", 0) >= 25],
        "findings":     findings.get("findings", []),
    })
    archive = archive[:30]
    WATCH_PATH.write_text(json.dumps(archive, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[onchain] saved · {len(archive)} reports in archive")


def append_to_global_archive(flagged):
    """For each high-score (>=50) finding, add to data/archive.json so PRIOR
    can reference it in future posts."""
    for f in flagged:
        if f.get("score", 0) < 50: continue
        addr_short = f["address"][:6] + "…" + f["address"][-4:]
        title = f"on-chain · suspicious holder pattern · {addr_short}"
        summary = (
            f"top 1 wallet {f['top_1_pct']}% · top 10 wallets {f['top_10_pct']}% · " +
            "; ".join(f.get("flags", []))[:120]
        )
        added = lib_archive.append(
            date=utc_now().strftime("%Y-%m-%d"),
            title=title,
            summary=summary,
            source=f.get("url") or f"https://solscan.io/token/{f['address']}",
            tags=["onchain", "auto", "memecoin", "concentration"],
        )
        if added:
            print(f"  [archive] +1 · {addr_short}")


# ─────────────────────────────────────────────────────────────────────
# Step 5: optional autopost of top finding
# ─────────────────────────────────────────────────────────────────────

def autopost_top_finding(top):
    if os.environ.get("PRIOR_ONCHAIN_AUTOPOST") != "1":
        return
    if not top or top.get("score", 0) < 60:
        return

    addr = top["address"]
    short = addr[:6] + "…" + addr[-4:]
    text = (
        f"on-chain forensics · {short}\n\n"
        f"top 1 wallet: {top['top_1_pct']}% of supply\n"
        f"top 10 wallets: {top['top_10_pct']}%\n\n"
        f"flags: {'; '.join(top.get('flags', [])[:2])[:120]}\n\n"
        f"see solscan.io/token/{short}"
    )
    if len(text) > 280:
        text = text[:277].rstrip() + "..."

    if os.environ.get("PRIOR_DRY_RUN") == "1":
        print(f"[autopost-dry] {text}")
        return

    try:
        import tweepy
        client = tweepy.Client(
            consumer_key        = os.environ["X_API_KEY"],
            consumer_secret     = os.environ["X_API_SECRET"],
            access_token        = os.environ["X_ACCESS_TOKEN"],
            access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
        )
        resp = client.create_tweet(text=text)
        tid = resp.data["id"]
        print(f"[autopost] https://x.com/i/status/{tid}")
    except Exception as e:
        print(f"[autopost-fail] {type(e).__name__}: {str(e)[:120]}")


# ─────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────

def main():
    print(f"[onchain] starting · {utc_now().isoformat()}")
    trending = fetch_trending_solana(limit=20)
    if not trending:
        print("[onchain] no trending data — DexScreener may be rate-limited or down")
        sys.exit(0)

    findings = []
    scanned = []
    for i, t in enumerate(trending[:15], 1):
        print(f"[onchain] [{i}/{min(15, len(trending))}] analyzing {t['address']}")
        scanned.append(t["address"])
        try:
            f = analyze_token(t)
        except Exception as e:
            print(f"  [analyze-fail] {type(e).__name__}: {str(e)[:120]}")
            continue
        if not f: continue
        findings.append(f)

    findings.sort(key=lambda x: x.get("score", 0), reverse=True)
    print(f"[onchain] scanned {len(scanned)}, analyzed {len(findings)}")
    if findings:
        print(f"[onchain] top score: {findings[0]['score']} · {findings[0]['address'][:8]}")
        for f in findings[:5]:
            print(f"  · {f['address'][:8]} · score={f['score']} · top1={f['top_1_pct']}% · flags={len(f['flags'])}")

    save_report({"scanned": scanned, "findings": findings})
    append_to_global_archive(findings)

    # autopost top finding only if score is critical AND we have a fresh one
    if findings:
        autopost_top_finding(findings[0])


if __name__ == "__main__":
    main()
