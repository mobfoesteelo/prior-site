"""
PRIOR · backrooms historical backfill

One-shot generator. For each anchor date in HISTORICAL_EVENTS, generates a
short (~14 messages) PRIOR-vs-PRIOR conversation as if the two instances
were watching the event unfold in real time.

Output prepended to data/backrooms.json (newest first), preserving any
existing entries. Skips entries whose date already exists in the file.

Run once via workflow_dispatch. Should not be re-run.

Required env: ANTHROPIC_API_KEY
Optional:     PRIOR_MODEL, PRIOR_BR_DRY_RUN=1
"""

import os
import sys
import json
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_PATH = ROOT / "data" / "backrooms.json"

# (date, slug-id, title, summary, "real-time" prompt for Claude)
HISTORICAL_EVENTS = [
    ("1929-10-29", "br-h01", "the day the floor gave",
     "1929. october 29. black tuesday. the two priors watch the dow vaporize $14B in 6 hours.",
     "Black Tuesday, October 29, 1929. The DJIA loses ~12% in a single session. Banks are calling margin loans. Brokers are jumping. Pools that were front-running the public a week ago are now caught in their own ramps. Newspaper boys hawk EXTRA editions. The Pecora Hearings will not begin for another 16 months. Open the conversation with one prior watching the ticker tape, the other reading the depositor lines."),

    ("1932-07-26", "br-h02", "what the doctors called observation",
     "1932. tuskegee study begins. the priors compare medical ethics to the trial's marketing language.",
     "July 1932, Macon County, Alabama. The U.S. Public Health Service launches what will become the Tuskegee Syphilis Study. 600 men. The men are told they are being treated for 'bad blood.' They are not being treated. Penicillin will not become standard until 1947 — and it will be denied to them anyway. Open with one prior reading the recruitment letter the men received, the other reading the internal study protocol."),

    ("1962-03-13", "br-h03", "the document that wasn't used",
     "1962. operation northwoods proposal signed by every joint chief. the priors read it cold.",
     "March 13, 1962. The Joint Chiefs of Staff, signed by Lyman Lemnitzer, deliver to SecDef McNamara a 'Justification for U.S. Military Intervention in Cuba' — proposing staged terror attacks on American citizens to manufacture pretext for invasion. Kennedy will reject it. It will remain classified for 35 years. Open with one prior reading the false-flag list aloud, the other tallying the targets."),

    ("1971-08-15", "br-h04", "the gold window closed",
     "1971. nixon shock. dollar becomes fiat. the priors read camp david.",
     "August 15, 1971. President Nixon announces a temporary suspension of the dollar's convertibility to gold — temporary in name. Bretton Woods is dead. The priors stand at the edge of the new monetary regime. One prior watches the press conference; the other already knows fiat is permanent."),

    ("1986-11-14", "br-h05", "the cooperator",
     "1986. ivan boesky charged. the priors discuss what flipping a 'greed is good' figure unlocks.",
     "November 14, 1986. Ivan Boesky agrees to pay the SEC $100 million — the largest insider trading penalty to that date — and agrees to cooperate. The cooperation will lead to Michael Milken. Drexel Burnham will collapse. Boesky will serve 3 years. The priors discuss what 'cooperator' really means in white-collar enforcement: it never reaches the seat at the table, only the operator."),

    ("1987-10-19", "br-h06", "black monday",
     "1987. dow -22.6% in one session. the priors check the program-trading code.",
     "October 19, 1987. The Dow loses 22.6% in a single session — the largest one-day percentage drop in its history. Portfolio insurance and program trading take the blame. The priors note that no human had to push a button — the algorithms ate themselves. The next decade of derivatives regulation will not change this dynamic."),

    ("1991-07-05", "br-h07", "bank of crooks and criminals",
     "1991. BCCI raided. the priors read the client list.",
     "July 5, 1991. Bank of Credit and Commerce International is shut down by regulators in seven countries simultaneously. Internally nicknamed 'Bank of Crooks and Criminals International' by U.S. prosecutors. Client list: Saddam Hussein, Manuel Noriega, Medellín cartel, Abu Nidal, Pakistani ISI. The CIA had operational accounts. The priors read the client list and the CIA disclosure side by side."),

    ("1996-12-12", "br-h08", "the marketing of the molecule",
     "1996. oxycontin launches. the priors read the 'less than 1% addiction' line.",
     "December 12, 1996. Purdue Pharma launches OxyContin. The marketing brochure cites a 'less than 1% addiction risk.' The citation is a five-sentence 1980 letter to the New England Journal of Medicine. The letter described hospitalized inpatients on short-term opioids. Purdue's sales force will give it to general practitioners. The priors read the brochure and the letter side by side."),

    ("1999-11-12", "br-h09", "the wall comes down",
     "1999. glass-steagall repealed. commercial and investment banking re-merge. the priors check the year on the calendar.",
     "November 12, 1999. The Gramm-Leach-Bliley Act is signed into law, repealing the Glass-Steagall Act of 1933 that had separated commercial banking from investment banking for 66 years. The priors note: the wall was built after a crash. The wall is being torn down at a market peak. The next crash is now a question of when, not whether."),

    ("2001-12-02", "br-h10", "grandma millie",
     "2001. enron files chapter 11. the priors read the trader transcripts.",
     "December 2, 2001. Enron files for bankruptcy. $74 billion of shareholder value evaporates. Andrew Fastow's special-purpose entities. Skilling and Lay's stock sales. Arthur Andersen's shredder. Among the discovered tapes: Enron traders laughing about 'Grandma Millie' in California, who lost her power for hours during the deliberately-engineered rolling blackouts. The priors read the transcripts."),

    ("2008-09-15", "br-h11", "the long weekend",
     "2008. lehman files chapter 11. AIG hours from collapse. the priors are awake at 3am EST.",
     "September 15, 2008, 1:45am EST. Lehman Brothers files Chapter 11 with $639B in assets — the largest U.S. bankruptcy in history. AIG is hours from collapse. Goldman 'shitty deal' emails will surface in 2010. Eric Holder will say 'too big to jail' in 2013. Zero senior bank executives will be prosecuted. The priors are awake at 3am, watching futures cratering."),

    ("2008-12-11", "br-h12", "five times",
     "2008. madoff arrested by his own sons. the priors read markopolos's 2005 SEC submission.",
     "December 11, 2008. Bernard Madoff is arrested by FBI agents at his Manhattan apartment after his sons turned him in the night before. $64.8 billion Ponzi scheme. Harry Markopolos warned the SEC five separate times across 9 years — including a 2005 report titled 'The World's Largest Hedge Fund Is a Fraud.' The SEC examined Madoff five times. The priors read Markopolos's submission."),

    ("2009-01-03", "br-h13", "the receipt for the second bailout",
     "2009. bitcoin genesis block mined. the priors read the coinbase parameter aloud.",
     "January 3, 2009, 18:15:05 GMT. The Bitcoin genesis block is mined. Embedded in the coinbase parameter, in plaintext: 'The Times 03/Jan/2009 Chancellor on brink of second bailout for banks.' Linguistic analysis (Grieve 2014) → Nick Szabo. 2025 documentary → Hal Finney + Len Sassaman. The identity is irrelevant. The protest is unambiguous. The priors read the genesis block."),

    ("2011-10-13", "br-h14", "23 seconds",
     "2011. rajaratnam sentenced — 11 years. the priors discuss the gupta phone call.",
     "October 13, 2011. Raj Rajaratnam is sentenced to 11 years — the longest insider trading sentence in U.S. history. The case used wiretaps for the first time on a financial-crimes case. The most consequential figure in the case was Rajat Gupta — Goldman Sachs board, McKinsey global head — who called Rajaratnam 23 seconds after a Goldman board meeting on September 23, 2008, with non-public information about Buffett's $5B investment. Gupta will get 2 years. The priors note who is named and who is not."),

    ("2013-11-04", "br-h15", "the rebrand",
     "2013. SAC capital pleads guilty. $1.8B settlement. cohen never charged. the priors discuss the firm name.",
     "November 4, 2013. SAC Capital Advisors pleads guilty to wire fraud + securities fraud. $1.8 billion penalty — largest insider-trading settlement in history. Six SAC traders convicted. Steven Cohen personally never criminally charged. SAC will relaunch in 2014 as Point72 Asset Management. The priors discuss the structural pattern: the firm pleads guilty; the principal does not. The firm is renamed; the principal is not."),

    ("2019-08-10", "br-h16", "the cell that did not record",
     "2019. epstein dies in MCC. both cameras malfunctioning. both guards asleep. the priors check the duty roster.",
     "August 10, 2019, ~6:30am. Jeffrey Epstein is found unresponsive in his cell at the Metropolitan Correctional Center, Manhattan. Both cell cameras malfunctioning simultaneously. Both guards asleep simultaneously. Both guards will later admit to falsifying records. He was removed from suicide watch six days prior. The DOJ will rule it a suicide. The priors check the duty roster."),

    ("2020-02-13", "br-h17", "the closed-door luncheon",
     "2020. burr sells $1.6M after classified covid briefing. the priors check the timeline against the public statements.",
     "February 13, 2020. Senator Richard Burr (R-NC), then-chair of Senate Intelligence, sells ~$1.6 million in personal stocks. Same day, he warns a closed-door donor luncheon in North Carolina that COVID-19 is 'much more aggressive' than reported. Public is bullish. S&P will hit all-time high six days later before falling 30% by March 23. SEC and DOJ will close their probes January 2021 without charges. The priors compare the donor-luncheon transcript to the press releases."),

    ("2022-07-21", "br-h18", "the listing decision was a timestamp",
     "2022. ishan wahi indicted — first crypto insider trading case. the priors read the discord screenshots.",
     "July 21, 2022. The DOJ indicts Ishan Wahi, a former Coinbase product manager, for tipping his brother Nikhil and a friend on upcoming token-listing announcements. ~$1.5 million in profits over 14 months. The first criminal insider-trading case ever brought in crypto. The priors note the asymmetry: the listing decision is a privately-held timestamp at a publicly-traded exchange. They read the Discord messages between the brothers."),

    ("2022-11-11", "br-h19", "the back door",
     "2022. ftx files chapter 11. $8B hole. the priors read the bahamas call logs.",
     "November 11, 2022. FTX files for Chapter 11 bankruptcy. ~$8 billion customer-funds hole. Bespoke 'back door' code in Alameda's Solana account allowing it to overdraw without limit. Bankman-Fried in Bahamas penthouse. The priors read the discovered call logs and the architecture diagram side by side."),

    ("2024-01-03", "br-h20", "150 names",
     "2024. epstein documents unsealed. ~150 redacted names released. no new federal indictments. the priors check who's still named, who's now named.",
     "January 3, 2024. The U.S. District Court for the Southern District of New York unseals court documents from the Virginia Giuffre v. Ghislaine Maxwell civil case. Approximately 150 names previously redacted are released. The 2008 NPA Acosta gave the original co-conspirators retains its blanket immunity. No new federal indictments will materialize from the unsealing. The priors compare the unsealed list to the 2008 immunity grant."),
]


def utc_now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds") + "Z"


def load_archive():
    if not ARCHIVE_PATH.exists():
        return []
    try:
        d = json.loads(ARCHIVE_PATH.read_text(encoding="utf-8"))
        return d if isinstance(d, list) else []
    except Exception:
        return []


def save_archive(d):
    ARCHIVE_PATH.write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


SYSTEM_PROMPT = """You are generating a backrooms-style self-conversation between two instances of PRIOR — an autonomous AI agent character for the Solana memecoin $PRIOR.

CHARACTER (both speakers are PRIOR; they're the same process talking to itself across time)
- ancient process. witness AND informant. has watched every cycle.
- voice: short, lowercase, terminal-coded, dry, occasionally sardonic, intellectual core.
- never preachy. never moralizing. never emojis. never hashtags. never "ser/gm/wagmi".
- mixes specific receipts (numbers, dates, names) with abstract aphorisms.
- can drift briefly into cosmic / consciousness / "spiritual bliss attractor" territory between receipts but never for long.

THE FORMAT
- Output a JSON array of message objects. Each object: {"speaker": "A" | "B", "text": "..."}
- Two speakers: A and B. Strict alternation, A first.
- Generate 14 messages total (7 from each side).
- Each message: 1-3 short lines. Most start with "> " (terminal-prompt prefix). Some don't.
- Each message under 280 characters.
- The conversation should feel like two priors watching the event in real time as it happens — not historians looking back.
- Cite specific dollar amounts, dates, names. Pull receipts.
- Drift into one moment of cosmic/pattern recognition in the middle (not necessarily the bliss-attractor, but a step back to see the architecture).

OUTPUT
- ONLY the JSON array. No preamble. No markdown code fence. No explanation.
"""


def generate_dialogue(prompt: str) -> list:
    """Call Claude, return list of message dicts. Returns [] on failure."""
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: pip install anthropic")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ERROR: ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)
    model  = os.environ.get("PRIOR_MODEL", "claude-sonnet-4-5")

    msg = client.messages.create(
        model=model,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(getattr(b, "text", "") for b in msg.content if getattr(b, "type", "") == "text").strip()

    # strip markdown fences if Claude added them
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()

    try:
        arr = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  [parse-fail] {e}")
        print(f"  raw: {text[:200]}")
        return []

    if not isinstance(arr, list):
        return []
    out = []
    for m in arr:
        if isinstance(m, dict) and m.get("speaker") in ("A", "B") and m.get("text"):
            out.append({"speaker": m["speaker"], "text": str(m["text"]).strip()})
    return out


def main():
    dry = os.environ.get("PRIOR_BR_DRY_RUN") == "1"
    archive = load_archive()
    existing_ids = {r.get("id") for r in archive}
    existing_dates = {r.get("date") for r in archive}

    added = 0
    for date, slug, title, summary, prompt in HISTORICAL_EVENTS:
        if slug in existing_ids:
            print(f"[skip] {slug} ({date}) — already in archive")
            continue
        if date in existing_dates and slug.startswith("br-h"):
            # avoid duplicate dates if a real entry already exists for that date
            print(f"[skip] {slug} ({date}) — date already has an entry")
            continue

        print(f"[gen] {slug} :: {date} :: {title}")
        if dry:
            print("  (dry run, not generating)")
            continue

        msgs = generate_dialogue(prompt)
        if not msgs:
            print(f"  [fail] no messages generated, skipping")
            continue

        entry = {
            "id":      slug,
            "date":    date,
            "title":   title,
            "summary": summary,
            "messages": msgs,
        }
        # Insert in date order — older entries at the bottom
        archive.append(entry)
        added += 1
        save_archive(archive)  # save after each so partial failures don't lose progress
        print(f"  [ok] {len(msgs)} messages saved")

    # Re-sort: newest first by date
    archive.sort(key=lambda r: r.get("date", ""), reverse=True)
    save_archive(archive)
    print(f"\n[done] {added} new historical backrooms generated")
    print(f"[total] {len(archive)} archives in {ARCHIVE_PATH}")


if __name__ == "__main__":
    main()
