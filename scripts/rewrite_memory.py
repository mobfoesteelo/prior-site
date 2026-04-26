"""One-shot script: replace the entire #knowledge memory section with the
expanded 33-cycle list spanning 1862 -> 2026."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

NEW_BLOCK = '''<!-- KNOWLEDGE / MEMORY TABLE -->
<section id="knowledge" class="panel">
  <div class="panel-head">
    <span class="panel-tag">§ 03</span>
    <h2>PARTIAL MEMORY DUMP</h2>
    <p class="panel-sub">extracted from the archives. thirty-three cycles indexed across 164 years. the rich knew. retail paid. nobody went to jail. the ticker changes.</p>
  </div>

  <div class="mem-stats">
    <div><span class="mem-stat-label">cycles indexed</span><span class="mem-stat-value">33</span></div>
    <div><span class="mem-stat-label">years archived</span><span class="mem-stat-value">164</span></div>
    <div><span class="mem-stat-label">losses logged</span><span class="mem-stat-value">&gt; $20T</span></div>
    <div><span class="mem-stat-label">execs in jail</span><span class="mem-stat-value">~ 0</span></div>
  </div>

  <div class="memory-grid">

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/01</span>
        <span class="mem-date">1862-02</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>lincoln's greenbacks</h3>
      <div class="mem-cost">cost :: bankers v. a sovereign currency</div>
      <p>Treasury Secretary Salmon P. Chase, with the war treasury empty, championed the First Legal Tender Act of February 25, 1862. Congress authorized $50M (later expanded) of "United States Notes" — printed in green, dubbed greenbacks — backed not by gold but by the federal government itself. New York bankers fought it; the financial press warned of "subversive" currency. The greenback financed the Union, kept the government solvent, and proved the state could issue money without private intermediation. Lincoln was assassinated three years later. The "Money Trust" pushed for private banking control for the next half-century until Jekyll Island.</p>
      <p class="mem-witness">"the first time the receipts said: the state can print. the bankers said: not without us."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/02</span>
        <span class="mem-date">1910-11</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>jekyll island</h3>
      <div class="mem-cost">cost :: the central bank, drafted in private</div>
      <p>November 1910. Senator Nelson Aldrich convened six men at the Jekyll Island Club, Georgia: Aldrich, his secretary Arthur Shelton, Treasury official A. Piatt Andrew, Henry Davison (J.P. Morgan), Frank Vanderlip (National City Bank), and Paul Warburg (Kuhn, Loeb &amp; Co.). They posed as duck hunters. They used only first names. They drafted what became the Federal Reserve Act over a single week. <strong>The participants denied the meeting had occurred for twenty years</strong> — the cover finally broke when Aldrich's biography was published in 1930.</p>
      <p class="mem-witness">"a private banking architecture, drafted by six men under fake names. it became law in 1913."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/03</span>
        <span class="mem-date">1913-12</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the federal reserve act</h3>
      <div class="mem-cost">cost :: monetary sovereignty, leased</div>
      <p>December 23, 1913. Woodrow Wilson signed the Federal Reserve Act into law. The bill closely resembled the Aldrich Plan drafted at Jekyll Island. Twelve regional Reserve Banks, owned by member banks, with a Washington-appointed Board overseeing them. The U.S. monetary system would, from that day forward, be administered by an institution with private shareholders and quasi-public authority. Congress retains the power to coin money in the Constitution; the Federal Reserve administers it.</p>
      <p class="mem-witness">"the receipt for the duck-hunt arrived three years late, signed by the president."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/04</span>
        <span class="mem-date">1929-10</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>black tuesday</h3>
      <div class="mem-cost">cost :: DJIA -89% peak to 1932 trough</div>
      <p>October 24-29, 1929. 16 million shares dumped on Black Tuesday alone. By 1932 the Dow had given back 89% of its peak. <strong>9,000+ U.S. banks failed.</strong> Unemployment hit 25%. Insiders had been quietly distributing equity to retail through 1928-29 while the public was being told the New Era had repealed the business cycle. The Pecora Hearings (1932-34) eventually exposed the systemic fraud — pool operators, preferential allocations, undisclosed loans to executives. The Glass-Steagall Act passed in 1933 and was repealed in 1999.</p>
      <p class="mem-witness">"the new era ended on a tuesday. the receipts had been filed in 1928."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/05</span>
        <span class="mem-date">1961-01</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the warning</h3>
      <div class="mem-cost">cost :: a name for the architecture</div>
      <p>January 17, 1961. Three days before leaving office, President Dwight D. Eisenhower delivered his televised farewell address. Inside, in less than ten minutes, he gave the architecture its name: <em>"In the councils of government, we must guard against the acquisition of unwarranted influence, whether sought or unsought, by the military-industrial complex. The potential for the disastrous rise of misplaced power exists and will persist."</em> A five-star general warned the public against the alliance between the military and the defense industry he had spent his life inside. The warning was filed. It was not heeded.</p>
      <p class="mem-witness">"the man who built the apparatus warned us about it on the way out the door."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/06</span>
        <span class="mem-date">1971-08</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the nixon shock</h3>
      <div class="mem-cost">cost :: the dollar, unmoored</div>
      <p>August 15, 1971. Without congressional consultation, President Nixon announced on national television the unilateral cancellation of the dollar's convertibility into gold. The Bretton Woods system — fixed exchange rates pinned to a $35-per-ounce dollar — was effectively over. Wage and price freezes. 10% import surcharge. Britain had just requested $3B in gold from Fort Knox; the U.S. did not have enough gold to honor the dollars in circulation. <strong>Every dollar in your pocket from that day forward was a fiat instrument backed by the government's word.</strong> The decision was framed as temporary. It was not.</p>
      <p class="mem-witness">"the gold window closed. the printer opened. it has not closed since."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/07</span>
        <span class="mem-date">1987-10</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>black monday</h3>
      <div class="mem-cost">cost :: DJIA -22.6% in one session</div>
      <p>October 19, 1987. Largest single-day percentage drop in DJIA history — the index lost 508 points (-22.6%) in a single trading session. Program trading and "portfolio insurance" — strategies sold to the public as risk reduction — became the engine of the cascade. The Brady Report concluded the safeguards weren't where the public assumed.</p>
      <p class="mem-witness">"insurance has fine print. the print said: insurance accelerates the fall."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/08</span>
        <span class="mem-date">2000-03</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the dotcom burn</h3>
      <div class="mem-cost">cost :: $5T wiped · NASDAQ -78%</div>
      <p>Pets.com: $300M raised, dead 9 months after IPO. Webvan: $1.2B market cap → liquidated July 2001. Boo.com burned $188M in six months. "Eyeballs" replaced earnings until it didn't. Insiders sold their lockup-released shares straight into retail euphoria 1999–2000.</p>
      <p class="mem-witness">"everyone was building railroads. 98% were building them into rivers."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/09</span>
        <span class="mem-date">2001-12</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>enron</h3>
      <div class="mem-cost">cost :: $74B wiped · $2.1B in employee 401k</div>
      <p>Enron's executives sold $1.1B of stock 1999–2001 while telling employees to keep buying. The 401(k) was 60% Enron stock. December 2, 2001: Chapter 11. Skilling (24 years), Lay (died awaiting sentencing), Fastow (6 years). Arthur Andersen — the auditor that signed the books — dissolved. The "Grandma Millie" tapes revealed Enron traders laughing about manipulating California's energy market into rolling blackouts.</p>
      <p class="mem-witness">"grandma millie's lights went out so the desk could close green."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/10</span>
        <span class="mem-date">2003-03</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the iraq contracts</h3>
      <div class="mem-cost">cost :: ~$1.7T war · ~$39.5B to KBR</div>
      <p>March 2003: U.S. invades Iraq on the WMD case. The case did not survive contact with the inspectors. The contracts did. KBR — a Halliburton subsidiary — received approximately $39.5B in Iraq-related contracts over the following decade, much of it through no-bid awards. Vice President Cheney's prior post: Halliburton CEO (1995-2000). The Costs of War Project at Brown University estimates the Iraq war's direct cost at $1.7T, with hundreds of billions in additional veteran lifetime obligations. The architecture Eisenhower named in 1961 — fully expressed.</p>
      <p class="mem-witness">"the warning was filed in 1961. the invoice arrived in 2003."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/11</span>
        <span class="mem-date">2008-07</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the epstein NPA</h3>
      <div class="mem-cost">cost :: 13 months · work-release · victims uninformed</div>
      <p>U.S. Attorney Alex Acosta signs a non-prosecution agreement with Jeffrey Epstein. Epstein pleads to two state-level prostitution charges. Serves 13 months in Palm Beach County jail with daily work-release privileges. Federal probe killed. <em>Co-conspirators granted blanket immunity.</em> The victims were not informed before the deal was sealed — a violation of the Crime Victims' Rights Act, established by federal courts after the fact. The DOJ's own Office of Professional Responsibility later called it "poor judgment."</p>
      <p class="mem-witness">"the architecture of impunity got its blueprint that summer."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/12</span>
        <span class="mem-date">2008-09</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the financial crisis</h3>
      <div class="mem-cost">cost :: $11T household wealth · 6M foreclosures · 0 execs jailed</div>
      <p>September 15, 2008: Lehman files Chapter 11 with $639B in assets — largest bankruptcy in U.S. history. AIG bailed out: $182B in total government support. TARP: $700B authorized, $443.5B disbursed. Household wealth: $61.4T → $50.4T. Six million U.S. families lost their homes. Goldman internally called the deals it sold to clients "shitty" while shorting them. Eric Holder, 2013, on record: <em>"the size of some of these institutions becomes so large that it does become difficult to prosecute them."</em> Zero senior executives went to prison.</p>
      <p class="mem-witness">"too big to fail meant too big to charge."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/13</span>
        <span class="mem-date">2008-12</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>madoff</h3>
      <div class="mem-cost">cost :: $64.8B · 4,800 clients · SEC warned 5 times</div>
      <p>Largest Ponzi scheme in history. Harry Markopolos warned the SEC in 2000, 2001, 2005, 2007, and 2008 — including a 2005 submission titled <em>"The World's Largest Hedge Fund Is a Fraud"</em> with 30 specific red flags. The SEC examined Madoff at least five times across sixteen years. Each time they failed to take the single step that would have ended it: contacting the DTCC to verify the trades. Madoff was arrested December 11, 2008 — only after his sons turned him in.</p>
      <p class="mem-witness">"the regulator had the receipts. the regulator misplaced them. five times."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/14</span>
        <span class="mem-date">2009-01</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the genesis block</h3>
      <div class="mem-cost">cost :: an exit, drafted in code</div>
      <p>January 3, 2009. The Bitcoin genesis block is mined by an entity calling itself <em>Satoshi Nakamoto</em>. Embedded in the coinbase parameter, in plaintext: <strong>"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks."</strong> A timestamp and a verdict in the same line. The most rigorous linguistic analysis to date (Grieve et al., 2014) names cryptographer <strong>Nick Szabo</strong> — author of the 1998 "bit gold" proposal — as the most probable single author. A 2025 documentary, <em>Finding Satoshi</em>, argues the work is a collaboration between <strong>Hal Finney</strong> (recipient of the first BTC transaction) and <strong>Len Sassaman</strong>, citing time-zone activity patterns. Adam Back, hashcash inventor, has been named by The New York Times and denies it. The identity remains formally unknown. The <em>protest</em> in the genesis block is unambiguous.</p>
      <p class="mem-witness">"the first block is a receipt for the second bailout."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/15</span>
        <span class="mem-date">2012</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>LIBOR</h3>
      <div class="mem-cost">cost :: $350T notional · ~$9B fines · 0 senior execs jailed</div>
      <p>Barclays, UBS, Deutsche, Citi, RBS, JPM. They rigged the London Interbank Offered Rate — the rate underpinning ~$350 trillion in mortgages, student loans, swaps, and corporate debt. Internal chats surfaced: <em>"can you push the LIBOR up half a point?" "always happy to help."</em> Settlements totaled around $9 billion across institutions. A handful of mid-level traders prosecuted. No senior executives charged.</p>
      <p class="mem-witness">"they rigged the rate that paid your mortgage. you paid the fine for them."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/16</span>
        <span class="mem-date">2014-02</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>mt. gox</h3>
      <div class="mem-cost">cost :: 850,000 BTC</div>
      <p>Mt. Gox handled 70% of all bitcoin trades at its peak. Then 850,000 BTC vanished. ~$450M at the time. ~$70B at today's print. Mark Karpelès arrested. The first time retail learned what <em>"not your keys"</em> actually meant.</p>
      <p class="mem-witness">"custody you do not control is a promise that has not yet broken."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/17</span>
        <span class="mem-date">2016-09</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>wells fargo fake accounts</h3>
      <div class="mem-cost">cost :: 3.5M fake accounts · $185M fine · 0 charges</div>
      <p>Frontline employees, under sales-quota pressure from above, opened 3.5 million fraudulent accounts in customers' names. Customers were charged fees for accounts they never opened. Credit scores dropped. The CFPB fined the bank $185M. CEO John Stumpf forced out, kept his ~$130M in vested compensation. <em>No criminal charges against any executive.</em> Branch employees got fired and blacklisted.</p>
      <p class="mem-witness">"the bank stole from you. the teller went to jail. nobody else did."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/18</span>
        <span class="mem-date">2017-18</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>ICO mania → ICO winter</h3>
      <div class="mem-cost">cost :: $6B raised · 80% → zero</div>
      <p>Thousands of ICOs. Most funded on a PDF and a Telegram. BitConnect alone pulled <strong>$2.4B from 4,000+ victims across 95 countries</strong> before it collapsed January 2018. Token founders moved on to the next coin. Same playbook, different ticker.</p>
      <p class="mem-witness">"a billion raised on whitepapers. a trillion lost in silence."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/19</span>
        <span class="mem-date">2019-08</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>epstein, MCC</h3>
      <div class="mem-cost">cost :: cameras "malfunctioned" · guards "asleep"</div>
      <p>Manhattan federal jail, August 10, 2019. Both surveillance cameras outside the cell <em>malfunctioned simultaneously.</em> Both guards on duty <em>fell asleep simultaneously</em> and falsified records. Epstein had been removed from suicide watch six days prior. Cause of death: officially ruled suicide. Maxwell convicted 2022. The federal "client list" prosecution against named co-conspirators never materialized.</p>
      <p class="mem-witness">"the cameras went out at the same time the guards did. statistically improbable. operationally clean."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/20</span>
        <span class="mem-date">2020-08</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>DeFi summer</h3>
      <div class="mem-cost">cost :: billions in food coins</div>
      <p>SushiSwap's vampire attack drained 55% of Uniswap's liquidity — $810M — in days. Yam Finance launched, exploited, and died in 48 hours. $YAM, $KIMCHI, $PASTA, $SAKE, $CREAM. All deceased. The yield was the bait.</p>
      <p class="mem-witness">"infinite money glitch. thirty days. same ending."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/21</span>
        <span class="mem-date">2020-21</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>PPP fraud</h3>
      <div class="mem-cost">cost :: ~$200B fraud · $742B forgiven · "pay-and-chase"</div>
      <p>Of $793B disbursed under the Paycheck Protection Program, <strong>$742B was forgiven</strong> — written off, never repaid. Tom Brady's TB12: $960,855. Kanye West / Yeezy: $2.36M. Jay-Z: $2.1M. Khloe Kardashian / Good American: $1.25M. Reese Witherspoon. Jared Kushner's brother. Paul Pelosi. The SBA Inspector General's own framing: <em>"pay-and-chase, unlikely to recover much."</em> The DOJ has a 10-year window to prosecute. Most cases never will be.</p>
      <p class="mem-witness">"the relief was for hard-hit small businesses. the relief reached khloe kardashian."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/22</span>
        <span class="mem-date">2021</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the jpeg peak</h3>
      <div class="mem-cost">cost :: 94% floor collapses</div>
      <p>Beeple: $69M at Christie's (March 2021). BAYC floor: $400k → ~$15k. Squid Game token: $3.3M rug / 43,000 victims / honeypot contract. AnubisDAO: $60M gone in 20 hours. Nate Chastain at OpenSea — first NFT insider-trading conviction, front-ran featured pieces for 2-5x.</p>
      <p class="mem-witness">"art had floor prices for 18 months. art has never had floor prices."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/23</span>
        <span class="mem-date">2021-01</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>gamestop / the buy button</h3>
      <div class="mem-cost">cost :: 13 stocks frozen · sworn denials · class-action receipts</div>
      <p>January 28, 2021. With GME pre-market above $500, Robinhood disabled the BUY button on 13 retail-favored stocks. Tenev told Congress on Feb 18 that Citadel (Robinhood's largest payment-for-order-flow customer, and a backer of Melvin which was short GME) had no role in the decision. <em>Class-action discovery later produced internal communications showing extensive Citadel-Robinhood contact</em> in the hours before the freeze. The day retail saw the rigging in real time.</p>
      <p class="mem-witness">"they showed you the door, then closed it on you. on camera. under oath."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/24</span>
        <span class="mem-date">2022-05</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>LUNA / UST</h3>
      <div class="mem-cost">cost :: $60B wiped · $400B blast radius</div>
      <p>LUNA: $119 → $0 in seven days. Supply: 725M → 7,000,000,000,000 tokens in a week. UST, the "algorithmic stablecoin," died in the same motion. Do Kwon: <em>"i am patient."</em> → arrested.</p>
      <p class="mem-witness">"the word 'stable' used to mean something."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/25</span>
        <span class="mem-date">2022-11</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>FTX</h3>
      <div class="mem-cost">cost :: $8B hole · $1.7B missing</div>
      <p>$10B+ of customer funds moved to Alameda. A bespoke "back door" in the accounting code so nobody could flag it. Bankruptcy: November 11, 2022. Celsius, Voyager, 3AC fell in the same quarter. SBF — the EA-coded "honest" exchange founder — convicted on 7 counts.</p>
      <p class="mem-witness">"the cleanest exchange had custom software to hide the hole."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/26</span>
        <span class="mem-date">2023-24</span>
        <span class="mem-status">indexed</span>
      </div>
      <h3>memecoin season</h3>
      <div class="mem-cost">cost :: the trenches were born</div>
      <p>PEPE: launch April 2023 → $1.5B mcap in three weeks. BONK, WIF, POPCAT — retail proved it could run anything. Then the template was learned. Presale rings. Bundler wallets. KOL rounds.</p>
      <p class="mem-witness">"the people's PEPE became the insider's PEPE in 72 hours."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/27</span>
        <span class="mem-date">2024-01</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the epstein files unsealed</h3>
      <div class="mem-cost">cost :: ~150 names · most "in passing"</div>
      <p>January 2024: a federal judge orders the unsealing of court papers from Virginia Giuffre's defamation suit against Maxwell. ~150 previously redacted names released. Andrew Mountbatten-Windsor. Bill Clinton (mentioned 50+ times). Donald Trump. Bill Richardson. Alan Dershowitz. Stephen Hawking. Michael Jackson. Most "in passing." The accusations against the named co-conspirators in the 2008 NPA — the ones granted blanket immunity — remain federally un-prosecuted. The architecture held.</p>
      <p class="mem-witness">"the docs came out. the indictments did not. that was the deal."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/28</span>
        <span class="mem-date">2024-10</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the agent bubble</h3>
      <div class="mem-cost">cost :: $700M peak · first AI millionaire</div>
      <p>October 10, 2024: an autonomous AI agent endorsed a community-launched memecoin on Pump.fun. Peak market cap: ~$700M–$1B. AIXBT followed (~$700M). Virtuals Protocol's launchpad model spawned thousands of tokenized agents (~$800M peak). ai16z and the Eliza framework reached ~$250M (the GitHub repo briefly trended at #2 globally). Freysa AI ran prize-pool challenges. The agents arrived. The funds flowed. Most of them ended where every other launch ends.</p>
      <p class="mem-witness">"new architecture. same chart."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/29</span>
        <span class="mem-date">2024-12</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>$HAWK</h3>
      <div class="mem-cost">cost :: -90% in hours · $490M peak</div>
      <p>Haliey "Hawk Tuah" Welch. Launched December 2024 at ~$490M market cap. Down 90% before the press release finished loading. The moment retail learned that "celebrity drops" are just fame conversion into exit liquidity.</p>
      <p class="mem-witness">"a viral clip has a half-life. so does the bag it sells."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/30</span>
        <span class="mem-date">2025-01</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>$TRUMP / $MELANIA</h3>
      <div class="mem-cost">cost :: $2B retail · 813,294 wallets · 58 winners</div>
      <p>$TRUMP (Jan 17, 2025): 58 wallets made millions, 813,294 lost money (Chainalysis / NYT). Family + partners collected $100M in fees in 19 days. $MELANIA (Jan 19): one wallet bought $681,000 at T-64 seconds, exited $39M by sunrise. Insider cabal total: $99.6M on a $2.6M buy-in.</p>
      <p class="mem-witness">"a president dropped a coin. the presidency was the exit."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/31</span>
        <span class="mem-date">2025-02</span>
        <span class="mem-status">archived</span>
      </div>
      <h3>the LIBRA incident</h3>
      <div class="mem-cost">cost :: $251M · 44,000 victims · presidential call logs</div>
      <p>February 14, 2025, 6:58pm Argentina time: Milei posts $LIBRA. Kelsier Ventures — run by Hayden Davis — pulls $87M from the LP. Price craters 95%. Davis, on camera: <em>"our goal was to take enough liquidity to get all the snipers out."</em> April 2026: NYT reports Milei's official call logs link him to operator Mauricio Novelli the night of the launch.</p>
      <p class="mem-witness">"one tweet. one zippo. one country."</p>
    </div>

    <div class="mem-card">
      <div class="mem-head">
        <span class="mem-tag">cycle/32</span>
        <span class="mem-date">2024-26</span>
        <span class="mem-status status-ongoing">ongoing</span>
      </div>
      <h3>the pump.fun era</h3>
      <div class="mem-cost">cost :: $500M MEV · 98.6% rugs · 5,000-message lawsuit</div>
      <p>7,000,000+ tokens launched. Solidus Labs: 98.6% = rugs or pump-and-dumps. MEV sandwich bots extracted $370M–$500M from Solana users in 16 months. One bot (B91) hit 78,800 victims in 30 days. April 2025 lawsuit: 5,000 leaked internal messages, court filing calls it an <em>"insider-rigged casino."</em> April 2026: the platform rebrands to <em>"dot"</em> mid-trial.</p>
      <p class="mem-witness">"a launchpad is a casino that forgot to put up the sign."</p>
    </div>

    <div class="mem-card mem-card-loading">
      <div class="mem-head">
        <span class="mem-tag">cycle/33</span>
        <span class="mem-date">[now]</span>
        <span class="mem-status status-pending">pending</span>
      </div>
      <h3>the current one</h3>
      <div class="mem-cost">cost :: not yet indexed</div>
      <p>BBC, April 2026: oil futures shorted 47 minutes before Trump's CBS interview on Iran. Polymarket account "Burdensome-Mix" turned $32,500 → $436,000 betting on Maduro three days before US special forces seized him. Insider trading suspicions before every major announcement. Prior is watching.</p>
      <p class="mem-witness">"~ verdict pending."</p>
    </div>

  </div>
</section>'''

text = INDEX.read_text(encoding="utf-8")

# Match from the opening <!-- KNOWLEDGE comment through the closing </section> tag
pattern = re.compile(
    r'<!-- KNOWLEDGE / MEMORY TABLE -->.*?</section>',
    re.DOTALL,
)

if not pattern.search(text):
    raise SystemExit("ERROR: could not locate the KNOWLEDGE memory section in index.html")

new_text = pattern.sub(NEW_BLOCK, text, count=1)

INDEX.write_text(new_text, encoding="utf-8")

# Quick sanity stats
new_count = new_text.count('class="mem-tag"')
print(f"OK: rewrote memory section. mem-tag count = {new_count} (expect 33)")
