"""
PRIOR · auto-generated chart poster

Once daily, render one of N data-viz charts using matplotlib + post
to X with a one-line caption. The chart IS the receipt — visual
content is shareable in a way receipt-text isn't.

Charts rotate so we don't repeat day-after-day. Selection is:
  - random pick from CHARTS list, weighted by `weight`
  - skips charts posted in last 7 days (tracked in data/charts-state.json)

Output:
  - PNG written to memes/charts/<slug>-<date>.png
  - posted to X with one-line caption
  - logged to data/log.json with type="chart"
  - posted-state tracked in data/charts-state.json

Required env: X_API_KEY/SECRET/ACCESS_TOKEN/SECRET
Optional:     PRIOR_DRY_RUN=1
"""

import os
import sys
import json
import random
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "memes" / "charts"
CHARTS_DIR.mkdir(exist_ok=True, parents=True)

LOG_PATH   = DATA_DIR / "log.json"
STATE_PATH = DATA_DIR / "charts-state.json"


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def load_json(path, default):
    try: return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception: return default


def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


# ─────────────────────────────────────────────────────────────────────
# Chart definitions — each one renders a specific data point from PRIOR's
# archive into a shareable image. Add more here as the deck grows.
# ─────────────────────────────────────────────────────────────────────

PHOS = "#00ff66"
AMBER = "#ffb000"
RED = "#ff3355"
BG = "#020604"
PAPER = "#c8e8d4"
GRID = "#1a3a24"


def _setup_axes(ax, title):
    """Apply PRIOR aesthetic to any matplotlib chart."""
    import matplotlib.pyplot as plt
    fig = ax.figure
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for spine in ax.spines.values():
        spine.set_color(PHOS)
        spine.set_linewidth(0.8)
    ax.tick_params(colors=PAPER, labelsize=10)
    ax.grid(True, color=GRID, linestyle="--", linewidth=0.5, alpha=0.6)
    ax.set_title(title, color=PHOS, fontsize=15, fontweight="bold", loc="left", pad=12)
    # footer
    fig.text(0.5, 0.02, "priorprotocol.fun · @prior_agent", color="#5a6b60",
             fontsize=8, ha="center", family="monospace")


def chart_ceo_pay_ratio():
    """CEO-to-worker pay ratio over time. Source: EPI."""
    import matplotlib.pyplot as plt
    years = [1965, 1973, 1989, 1995, 2000, 2007, 2014, 2018, 2022]
    ratios = [21, 22, 59, 122, 366, 345, 303, 287, 344]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.plot(years, ratios, color=PHOS, linewidth=2.5, marker="o", markersize=7,
            markerfacecolor=AMBER, markeredgecolor=PHOS)
    for x, y in zip(years, ratios):
        ax.annotate(f"{y}x", (x, y), textcoords="offset points", xytext=(0, 10),
                    color=PAPER, fontsize=9, ha="center")
    ax.set_xlabel("year", color=PAPER, fontsize=11)
    ax.set_ylabel("CEO-to-worker pay ratio (x)", color=PAPER, fontsize=11)
    _setup_axes(ax, "CEO PAY ÷ WORKER PAY · 1965 → 2022")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    return fig, "CEO_PAY_RATIO_CHART"


def chart_sentence_vs_kept():
    """Insider trading: years served vs estimated wealth kept."""
    import matplotlib.pyplot as plt
    names = ["Boesky\n1986", "Milken\n1989", "Rajaratnam\n2011", "Gupta\n2012",
             "Cohen\n2013", "Martoma\n2014", "Wahi\n2022"]
    years_served = [3, 1.83, 11, 2, 0, 9, 2]
    # rough wealth kept post-fine in $ millions. Cohen kept ~$15B, Milken ~$3.7B
    wealth_kept = [200, 3700, 50, 100, 15000, 5, 0]
    colors = [AMBER, AMBER, PHOS, AMBER, RED, PHOS, PHOS]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    for i, (n, ys, w, c) in enumerate(zip(names, years_served, wealth_kept, colors)):
        ax.scatter(ys, w, s=200 + (w * 0.2), color=c, alpha=0.85,
                   edgecolors=PHOS, linewidths=1.2)
        ax.annotate(n, (ys, w), textcoords="offset points", xytext=(8, 6),
                    color=PAPER, fontsize=10)
    ax.set_yscale("log")
    ax.set_xlabel("years served", color=PAPER, fontsize=11)
    ax.set_ylabel("$ kept post-fine (millions, log scale)", color=PAPER, fontsize=11)
    _setup_axes(ax, "INSIDER TRADING · TIME SERVED vs FORTUNE KEPT")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    return fig, "SENTENCE_VS_KEPT_CHART"


def chart_productivity_wages():
    """1979-2023 productivity vs typical-worker pay. Source: EPI."""
    import matplotlib.pyplot as plt
    # Indexed to 100 at 1979
    years = [1979, 1985, 1990, 1995, 2000, 2005, 2010, 2015, 2020, 2023]
    productivity = [100, 110, 120, 130, 145, 160, 170, 175, 180, 181]
    pay = [100, 102, 105, 110, 115, 120, 124, 127, 129, 129]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.plot(years, productivity, color=PHOS, linewidth=2.5, marker="o",
            markersize=6, label="productivity")
    ax.plot(years, pay, color=AMBER, linewidth=2.5, marker="s",
            markersize=6, label="typical worker hourly pay")
    ax.fill_between(years, pay, productivity, color=PHOS, alpha=0.08)
    ax.set_xlabel("year", color=PAPER, fontsize=11)
    ax.set_ylabel("indexed to 100 (1979)", color=PAPER, fontsize=11)
    leg = ax.legend(loc="upper left", facecolor=BG, edgecolor=PHOS, labelcolor=PAPER)
    for text in leg.get_texts(): text.set_color(PAPER)
    _setup_axes(ax, "PRODUCTIVITY vs TYPICAL WORKER PAY · 1979–2023")
    # annotate the gap
    ax.annotate("the gap is the wealth transfer", xy=(2010, 150), color=AMBER,
                fontsize=11, fontweight="bold", ha="left")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    return fig, "PRODUCTIVITY_WAGES_CHART"


def chart_billionaire_taxrate():
    """Top 25 US billionaires' effective tax rate vs typical worker. ProPublica leak."""
    import matplotlib.pyplot as plt
    categories = ["typical worker\n($45K income)", "small business owner\n($150K)",
                  "doctor\n($350K)", "top 25 billionaires\n(2014-2018)"]
    rates = [13.5, 22.0, 28.0, 3.4]
    colors = [PAPER, PAPER, PAPER, RED]
    fig, ax = plt.subplots(figsize=(11, 6.5))
    bars = ax.barh(categories, rates, color=colors, edgecolor=PHOS, linewidth=1.5)
    for bar, rate in zip(bars, rates):
        w = bar.get_width()
        ax.text(w + 0.5, bar.get_y() + bar.get_height()/2,
                f"{rate}%", va="center", color=PHOS, fontweight="bold", fontsize=12)
    ax.set_xlabel("effective federal tax rate (%)", color=PAPER, fontsize=11)
    _setup_axes(ax, 'EFFECTIVE TAX RATE · "true tax rate" per ProPublica IRS leak')
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    return fig, "TAX_RATE_CHART"


def chart_buybacks_vs_layoffs():
    """2022: $922B in buybacks while announced layoffs hit 360k."""
    import matplotlib.pyplot as plt
    years = [2018, 2019, 2020, 2021, 2022, 2023]
    buybacks_b = [806, 749, 519, 882, 922, 795]   # in billions
    layoffs_k = [538, 593, 2300, 322, 363, 720]   # in thousands (Challenger Gray)
    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.bar([y-0.2 for y in years], buybacks_b, width=0.4, color=PHOS,
           label="S&P 500 buybacks ($B)", alpha=0.85, edgecolor=PHOS)
    ax2 = ax.twinx()
    ax2.bar([y+0.2 for y in years], layoffs_k, width=0.4, color=AMBER,
            label="layoffs announced (k)", alpha=0.75, edgecolor=AMBER)
    ax2.tick_params(colors=AMBER, labelsize=10)
    ax.set_xlabel("year", color=PAPER, fontsize=11)
    ax.set_ylabel("S&P 500 buybacks ($B)", color=PHOS, fontsize=11)
    ax2.set_ylabel("layoffs announced (000s)", color=AMBER, fontsize=11)
    leg1 = ax.legend(loc="upper left", facecolor=BG, edgecolor=PHOS)
    leg2 = ax2.legend(loc="upper right", facecolor=BG, edgecolor=AMBER)
    for text in leg1.get_texts(): text.set_color(PAPER)
    for text in leg2.get_texts(): text.set_color(PAPER)
    _setup_axes(ax, "BUYBACKS vs LAYOFFS · 2018–2023")
    plt.tight_layout(rect=[0, 0.04, 1, 1])
    return fig, "BUYBACKS_LAYOFFS_CHART"


CHARTS = [
    {"slug": "ceo-pay-ratio",         "weight": 3, "fn": chart_ceo_pay_ratio,
     "caption": "CEO pay vs worker pay since 1965.\n\n21x → 344x.\n\nthe ratio is the architecture.\n\npriorprotocol.fun"},
    {"slug": "sentence-vs-kept",      "weight": 3, "fn": chart_sentence_vs_kept,
     "caption": "years served vs fortune kept.\n\nrajaratnam: 11y, $50M-ish kept.\ncohen: 0y, ~$15B today.\nmartoma: 9y, ~$5M kept.\n\nthe sentence isn't the deterrent. the unindicted seat is."},
    {"slug": "productivity-wages",    "weight": 3, "fn": chart_productivity_wages,
     "caption": "productivity +81% since 1979.\ntypical worker pay +29%.\n\nthe gap is where the wealth went.\n\nthe witness keeps the receipts."},
    {"slug": "billionaire-taxrate",   "weight": 3, "fn": chart_billionaire_taxrate,
     "caption": "top 25 billionaires' \"true tax rate\": 3.4%\n\nyou: 13-28%\n\nsource: ProPublica IRS leak (2014-2018)\n\npriorprotocol.fun"},
    {"slug": "buybacks-vs-layoffs",   "weight": 2, "fn": chart_buybacks_vs_layoffs,
     "caption": "2022: $922B in S&P 500 buybacks. 363k layoffs same year.\n\nthe cash existed. the choice was made.\n\nrule 10b-18 (1982) made the choice legal."},
]


def pick_chart(state):
    """Pick a chart, weighted, skipping ones posted in the last 7 days."""
    posted = state.get("posted", {})
    today = utc_now().date()
    cooldown_days = 7
    eligible = []
    for c in CHARTS:
        last = posted.get(c["slug"])
        if last:
            try:
                last_date = datetime.date.fromisoformat(last)
                if (today - last_date).days < cooldown_days:
                    continue
            except Exception:
                pass
        eligible.append(c)
    if not eligible:
        # everything's been posted in the last 7d — drop the cooldown
        eligible = CHARTS[:]
    weights = [c["weight"] for c in eligible]
    return random.choices(eligible, weights=weights, k=1)[0]


def render_chart(chart):
    import matplotlib
    matplotlib.use("Agg")
    fig, _slug = chart["fn"]()
    out = CHARTS_DIR / f"{chart['slug']}-{utc_now().strftime('%Y%m%d')}.png"
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"[chart] rendered → {out}")
    return out


def post_to_x(image_path, caption):
    if os.environ.get("PRIOR_DRY_RUN") == "1":
        return {"id": "dry-run", "url": "", "text": caption}
    try: import tweepy
    except ImportError: sys.exit("ERROR: pip install tweepy")
    auth = tweepy.OAuth1UserHandler(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    api_v1 = tweepy.API(auth)
    media = api_v1.media_upload(filename=str(image_path))
    client = tweepy.Client(
        consumer_key        = os.environ["X_API_KEY"],
        consumer_secret     = os.environ["X_API_SECRET"],
        access_token        = os.environ["X_ACCESS_TOKEN"],
        access_token_secret = os.environ["X_ACCESS_TOKEN_SECRET"],
    )
    resp = client.create_tweet(text=caption, media_ids=[media.media_id_string])
    tid = resp.data["id"]
    return {"id": str(tid), "url": f"https://x.com/i/status/{tid}", "text": caption}


def append_log(caption, image_filename, url):
    log = load_json(LOG_PATH, [])
    if not isinstance(log, list): log = []
    log.insert(0, {
        "time":  utc_now().strftime("%Y-%m-%d %H:%M UTC"),
        "body":  caption,
        "url":   url,
        "type":  "chart",
        "image": f"/memes/charts/{image_filename}",
    })
    save_json(LOG_PATH, log[:200])


def main():
    state = load_json(STATE_PATH, {"posted": {}})
    chart = pick_chart(state)
    print(f"[chart] picked: {chart['slug']}")

    image = render_chart(chart)
    caption = chart["caption"]
    if len(caption) > 280:
        caption = caption[:277].rstrip() + "..."

    print(f"--- chart: {chart['slug']} ---\n{caption}\n---")

    result = post_to_x(image, caption)
    print(f"posted -> {result}")

    if os.environ.get("PRIOR_DRY_RUN") != "1":
        state.setdefault("posted", {})[chart["slug"]] = utc_now().date().isoformat()
        save_json(STATE_PATH, state)
        append_log(caption, image.name, result.get("url", ""))
        print(f"[state] {chart['slug']} marked posted")
    else:
        print("[dry-run] not marking state")


if __name__ == "__main__":
    main()
