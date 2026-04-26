"""Rewrite the memory section with the expanded 45-cycle list.
Run after editing CYCLES below."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# Each cycle: (id, date, status, title, cost, body, witness)
CYCLES = [
    ("01", "1862-02", "archived", "lincoln's greenbacks",
     "cost :: bankers v. a sovereign currency",
     'Treasury Secretary Salmon P. Chase, with the war treasury empty, championed the First Legal Tender Act of February 25, 1862. Congress authorized $50M (later expanded) of "United States Notes" — printed in green, dubbed greenbacks — backed not by gold but by the federal government itself. New York bankers fought it; the financial press warned of "subversive" currency. The greenback financed the Union, kept the government solvent, and proved the state could issue money without private intermediation. Lincoln was assassinated three years later. The "Money Trust" pushed for private banking control for the next half-century until Jekyll Island.',
     '"the first time the receipts said: the state can print. the bankers said: not without us."'),

    ("02", "1910-11", "archived", "jekyll island",
     "cost :: the central bank, drafted in private",
     'November 1910. Senator Nelson Aldrich convened six men at the Jekyll Island Club, Georgia: Aldrich, his secretary Arthur Shelton, Treasury official A. Piatt Andrew, Henry Davison (J.P. Morgan), Frank Vanderlip (National City Bank), and Paul Warburg (Kuhn, Loeb &amp; Co.). They posed as duck hunters. They used only first names. They drafted what became the Federal Reserve Act over a single week. <strong>The participants denied the meeting had occurred for twenty years</strong> — the cover finally broke when Aldrich\'s biography was published in 1930.',
     '"a private banking architecture, drafted by six men under fake names. it became law in 1913."'),

    ("03", "1913-12", "archived", "the federal reserve act",
     "cost :: monetary sovereignty, leased",
     'December 23, 1913. Woodrow Wilson signed the Federal Reserve Act into law. The bill closely resembled the Aldrich Plan drafted at Jekyll Island. Twelve regional Reserve Banks, owned by member banks, with a Washington-appointed Board overseeing them. The U.S. monetary system would, from that day forward, be administered by an institution with private shareholders and quasi-public authority. Congress retains the power to coin money in the Constitution; the Federal Reserve administers it.',
     '"the receipt for the duck-hunt arrived three years late, signed by the president."'),

    ("04", "1929-10", "archived", "black tuesday",
     "cost :: DJIA -89% peak to 1932 trough",
     'October 24-29, 1929. 16 million shares dumped on Black Tuesday alone. By 1932 the Dow had given back 89% of its peak. <strong>9,000+ U.S. banks failed.</strong> Unemployment hit 25%. Insiders had been quietly distributing equity to retail through 1928-29 while the public was being told the New Era had repealed the business cycle. The Pecora Hearings (1932-34) eventually exposed the systemic fraud — pool operators, preferential allocations, undisclosed loans to executives. Glass-Steagall passed in 1933. It was repealed in 1999.',
     '"the new era ended on a tuesday. the receipts had been filed in 1928."'),

    ("05", "1932-72", "archived", "the tuskegee study",
     "cost :: 600 men · 40 years · ~100+ dead · 19 children with congenital syphilis",
     'The U.S. Public Health Service ran the "Tuskegee Study of Untreated Syphilis in the Negro Male" from 1932 to 1972 — <strong>40 years</strong>. 600 men were enrolled; 399 had syphilis. They were told they were being treated for "bad blood." They were not informed of the actual study, did not give consent, and were systematically <em>denied treatment</em> — including penicillin after it became the standard cure in 1943. By the time whistleblower Peter Buxtun broke the study in 1972, at least 28 men had died directly of syphilis and another ~100 of related complications. 40 wives were infected. 19 children were born with congenital syphilis. Presidential apology: 1997, 25 years after the study ended.',
     '"a federal medical agency ran a deliberate non-treatment study on its own citizens for 40 years. it ended only because someone leaked it."'),

    ("06", "1953-73", "archived", "MK-ULTRA",
     "cost :: 149 sub-projects · destroyed records · uncounted civilian subjects",
     'The CIA\'s mind-control program. Begun April 13, 1953 on the order of Director Allen Dulles, headed by chemist Sidney Gottlieb. <strong>149 sub-projects</strong>, contracted out to <strong>80 universities, hospitals, and prisons</strong> — none of whom were told the funding was CIA. Methods included covert administration of high-dose LSD without consent, electroshock, sensory deprivation, hypnosis, isolation, sexual abuse, and torture. CIA scientist Frank Olson was dosed without his knowledge in November 1953 and died after falling from a 13th-floor window a week later (a 1994 forensic re-examination found injuries inconsistent with the official story). <strong>In 1973, CIA Director Richard Helms ordered the records destroyed.</strong> A misfiled cache of 20,000 financial records surfaced in 1977; the Church Committee hearings followed.',
     '"the program was destroyed before it was investigated. the investigation built its case from the receipts the destroyers missed."'),

    ("07", "1956-71", "archived", "COINTELPRO",
     "cost :: civil rights movement disrupted · MLK harassed · domestic surveillance",
     'The FBI\'s Counter-Intelligence Program. From 1956 to 1971, the Bureau ran covert operations against domestic political organizations and individuals — initially the Communist Party USA, then expanded to civil rights groups (SCLC, SNCC, the Black Panthers), anti-war organizations, the women\'s movement, and individual targets including Dr. Martin Luther King Jr. Methods: illegal wiretaps, mail openings, informants, infiltration, fabricated evidence, anonymous letters, blackmail, manufactured discord between groups, and at least one infamous "suicide letter" mailed to MLK from the Bureau urging him to take his own life. Exposed March 8, 1971 when activists broke into the FBI\'s Media, Pennsylvania field office and leaked the documents to the press. Senate Church Committee (1975-76) confirmed the program\'s scope.',
     '"the bureau was running an internal counter-insurgency program against the country it was supposed to police."'),

    ("08", "1961-01", "archived", "the warning",
     "cost :: a name for the architecture",
     'January 17, 1961. Three days before leaving office, President Dwight D. Eisenhower delivered his televised farewell address. Inside, in less than ten minutes, he gave the architecture its name: <em>"In the councils of government, we must guard against the acquisition of unwarranted influence, whether sought or unsought, by the military-industrial complex. The potential for the disastrous rise of misplaced power exists and will persist."</em> A five-star general warned the public against the alliance between the military and the defense industry he had spent his life inside. The warning was filed. It was not heeded.',
     '"the man who built the apparatus warned us about it on the way out the door."'),

    ("09", "1964-08", "archived", "the gulf of tonkin",
     "cost :: 58,220 U.S. dead · ~3M Vietnamese dead · the war was based on a lie",
     'August 2, 1964: the USS Maddox engaged North Vietnamese torpedo boats in the Gulf of Tonkin. Two days later, August 4, Maddox reported a second engagement. President Johnson cited the second incident in a national address requesting authorization to use military force; Congress passed the Gulf of Tonkin Resolution near-unanimously. <strong>The August 4 incident never happened.</strong> NSA reports declassified in 2005 confirmed there was no second attack; the radar contacts had been misinterpreted. The Pentagon Papers (leaked 1971 by Daniel Ellsberg) had already revealed that the administration knew the war was un-winnable and was lying to the public about it. By the war\'s end: ~58,000 U.S. service members dead, 1.1M North Vietnamese soldiers dead, and an estimated 2 million Vietnamese civilians dead.',
     '"the second attack did not happen. the war based on it did."'),

    ("10", "1971-08", "archived", "the nixon shock",
     "cost :: the dollar, unmoored",
     'August 15, 1971. Without congressional consultation, President Nixon announced on national television the unilateral cancellation of the dollar\'s convertibility into gold. The Bretton Woods system — fixed exchange rates pinned to a $35-per-ounce dollar — was effectively over. Wage and price freezes. 10% import surcharge. Britain had just requested $3B in gold from Fort Knox; the U.S. did not have enough gold to honor the dollars in circulation. <strong>Every dollar in your pocket from that day forward was a fiat instrument backed by the government\'s word.</strong>',
     '"the gold window closed. the printer opened. it has not closed since."'),

    ("11", "1986-11", "archived", "iran-contra",
     "cost :: arms-for-hostages · illegal contra funding · 11 convictions, all vacated or pardoned",
     'Senior Reagan administration officials secretly sold ~2,000 anti-tank missiles to Iran (in violation of an arms embargo, ostensibly to free hostages held in Lebanon) and diverted the proceeds to fund the Nicaraguan Contras (in violation of the Boland Amendments which prohibited such funding). NSC official Lt. Col. Oliver North managed the operation; National Security Advisor John Poindexter approved it. <strong>Eleven officials were convicted</strong> — including Defense Secretary Caspar Weinberger, North, Poindexter, Robert McFarlane. North\'s and Poindexter\'s convictions were vacated on appeal. President George H.W. Bush pardoned six of the principals in December 1992, including Weinberger, four days before Weinberger was scheduled to stand trial. The independent counsel\'s final report concluded Bush had been part of the operation and was lying about his role.',
     '"two illegal programs run from the white house. eleven convictions. zero served sentences."'),

    ("12", "1986-89", "archived", "the savings & loan crisis",
     "cost :: ~$160B taxpayer · 1,043 institutions failed · Keating Five",
     'Between 1986 and 1995, <strong>1,043 of America\'s 3,234 savings and loan institutions failed</strong>, costing taxpayers approximately <strong>$160 billion</strong> ($132B from public funds via the FSLIC bailout; the remainder from the industry). Causes: deregulation in the early 1980s allowed S&Ls to make risky commercial real estate loans, removed deposit caps, and weakened oversight. Charles Keating\'s Lincoln Savings & Loan failed costing $3.4B. Keating had channeled $1.3M to <strong>five U.S. Senators</strong> (the "Keating Five"): Cranston, DeConcini, Glenn, McCain, Riegle. He had used the senators to pressure regulators to ease scrutiny of his bank. ~1,000 industry insiders were ultimately prosecuted. Keating served 4½ years.',
     '"the bankers got the deposits. the depositors got the bill."'),

    ("13", "1987-10", "archived", "black monday",
     "cost :: DJIA -22.6% in one session",
     'October 19, 1987. Largest single-day percentage drop in DJIA history — 508 points (-22.6%) in a single trading session. Program trading and "portfolio insurance" — strategies sold to the public as risk reduction — became the engine of the cascade. The Brady Report concluded the safeguards weren\'t where the public assumed.',
     '"insurance has fine print. the print said: insurance accelerates the fall."'),

    ("14", "1991-07", "archived", "BCCI",
     "cost :: $20B missing · CIA accounts · drugs, arms, sanctions evasion",
     'The Bank of Credit and Commerce International. Founded 1972 by Pakistani financier Agha Hasan Abedi. By 1991 it had <strong>more than 400 branches in 78 countries</strong> and <strong>$20+ billion in assets</strong> — the seventh largest private bank in the world. On July 5, 1991, customs and bank regulators in seven countries simultaneously raided BCCI offices. <strong>$20 billion was missing.</strong> The bank had laundered for: Saddam Hussein, Manuel Noriega, the Medellín Cartel, Abu Nidal, the Pakistani ISI, and a long list of arms-and-narcotics networks. <strong>The CIA admitted holding "several" accounts at BCCI.</strong> Senate Kerry Committee (1992) documented the U.S. intelligence relationship in detail. U.S. regulators called it the "Bank of Crooks and Criminals International."',
     '"the seventh largest private bank in the world was a money laundering apparatus with a CIA account. it was not an outlier. it was a service."'),

    ("15", "1996-2024", "archived", "the sackler · purdue · OxyContin",
     "cost :: ~900,000 U.S. dead · $7.4B 2025 settlement · family kept billions",
     'OxyContin launched in 1996. Purdue Pharma, owned by the Sackler family, marketed it as non-addictive. It was not. By the late 2010s, prescription-opioid overdoses had killed hundreds of thousands; including illicit opioids the figure exceeds <strong>~900,000 U.S. deaths since 1999</strong>. Internal documents (released through litigation) showed the Sacklers had been <em>warned by their own scientists in the 1990s</em> about addiction risk and pushed the marketing forward anyway. The original 2024 bankruptcy settlement gave the family blanket immunity in exchange for ~$6B. <strong>The U.S. Supreme Court invalidated that immunity in June 2024 (Harrington v. Purdue Pharma)</strong> in a 5-4 decision. A revised <strong>$7.4B settlement</strong> in 2025 — without the third-party releases — became the largest individual-pay opioid settlement on record. The Sacklers retain billions extracted before the bankruptcy.',
     '"the family marketed an addictive drug as non-addictive for two decades. they kept enough of the money to fight the lawsuits with."'),

    ("16", "2000-03", "archived", "the dotcom burn",
     "cost :: $5T wiped · NASDAQ -78%",
     'Pets.com: $300M raised, dead 9 months after IPO. Webvan: $1.2B market cap → liquidated July 2001. Boo.com burned $188M in six months. "Eyeballs" replaced earnings until it didn\'t. Insiders sold their lockup-released shares straight into retail euphoria 1999–2000.',
     '"everyone was building railroads. 98% were building them into rivers."'),

    ("17", "2001-12", "archived", "enron",
     "cost :: $74B wiped · $2.1B in employee 401k",
     'Enron\'s executives sold $1.1B of stock 1999–2001 while telling employees to keep buying. The 401(k) was 60% Enron stock. December 2, 2001: Chapter 11. Skilling (24 years), Lay (died awaiting sentencing), Fastow (6 years). Arthur Andersen — the auditor that signed the books — dissolved. The "Grandma Millie" tapes revealed Enron traders laughing about manipulating California\'s energy market into rolling blackouts.',
     '"grandma millie\'s lights went out so the desk could close green."'),

    ("18", "2003-03", "archived", "the iraq contracts",
     "cost :: ~$1.7T war · ~$39.5B to KBR/Halliburton",
     'March 2003: U.S. invades Iraq on the WMD case. The case did not survive contact with the inspectors. The contracts did. KBR — a Halliburton subsidiary — received approximately $39.5B in Iraq-related contracts over the following decade, much of it through no-bid awards. Vice President Cheney\'s prior post: Halliburton CEO (1995-2000). The Costs of War Project at Brown University estimates the Iraq war\'s direct cost at $1.7T, with hundreds of billions in additional veteran lifetime obligations.',
     '"the warning was filed in 1961. the invoice arrived in 2003."'),

    ("19", "2008-07", "archived", "the epstein NPA",
     "cost :: 13 months · work-release · victims uninformed",
     'U.S. Attorney Alex Acosta signs a non-prosecution agreement with Jeffrey Epstein. Epstein pleads to two state-level prostitution charges. Serves 13 months in Palm Beach County jail with daily work-release privileges. Federal probe killed. <em>Co-conspirators granted blanket immunity.</em> The victims were not informed before the deal was sealed — a violation of the Crime Victims\' Rights Act, established by federal courts after the fact. The DOJ\'s own Office of Professional Responsibility later called it "poor judgment."',
     '"the architecture of impunity got its blueprint that summer."'),

    ("20", "2008-09", "archived", "the financial crisis",
     "cost :: $11T household wealth · 6M foreclosures · 0 execs jailed",
     'September 15, 2008: Lehman files Chapter 11 with $639B in assets — largest bankruptcy in U.S. history. AIG bailed out: $182B in total government support. TARP: $700B authorized, $443.5B disbursed. Household wealth: $61.4T → $50.4T. Six million U.S. families lost their homes. Goldman internally called the deals it sold to clients "shitty" while shorting them. Eric Holder, 2013, on record: <em>"the size of some of these institutions becomes so large that it does become difficult to prosecute them."</em> Zero senior executives went to prison.',
     '"too big to fail meant too big to charge."'),

    ("21", "2008-12", "archived", "madoff",
     "cost :: $64.8B · 4,800 clients · SEC warned 5 times",
     'Largest Ponzi scheme in history. Harry Markopolos warned the SEC in 2000, 2001, 2005, 2007, and 2008 — including a 2005 submission titled <em>"The World\'s Largest Hedge Fund Is a Fraud"</em> with 30 specific red flags. The SEC examined Madoff at least five times across sixteen years. Each time they failed to take the single step that would have ended it: contacting the DTCC to verify the trades. Madoff was arrested December 11, 2008 — only after his sons turned him in.',
     '"the regulator had the receipts. the regulator misplaced them. five times."'),

    ("22", "2009-01", "archived", "the genesis block",
     "cost :: an exit, drafted in code",
     'January 3, 2009. The Bitcoin genesis block is mined by an entity calling itself <em>Satoshi Nakamoto</em>. Embedded in the coinbase parameter, in plaintext: <strong>"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks."</strong> A timestamp and a verdict in the same line. The most rigorous linguistic analysis to date (Grieve et al., 2014) names cryptographer <strong>Nick Szabo</strong> — author of the 1998 "bit gold" proposal — as the most probable single author. A 2025 documentary, <em>Finding Satoshi</em>, argues the work is a collaboration between <strong>Hal Finney</strong> (recipient of the first BTC transaction) and <strong>Len Sassaman</strong>, citing time-zone activity patterns. Adam Back, hashcash inventor, has been named by The New York Times and denies it. The identity remains formally unknown. The <em>protest</em> in the genesis block is unambiguous.',
     '"the first block is a receipt for the second bailout."'),

    ("23", "2012", "archived", "LIBOR",
     "cost :: $350T notional · ~$9B fines · 0 senior execs jailed",
     'Barclays, UBS, Deutsche, Citi, RBS, JPM. They rigged the London Interbank Offered Rate — the rate underpinning ~$350 trillion in mortgages, student loans, swaps, and corporate debt. Internal chats surfaced: <em>"can you push the LIBOR up half a point?" "always happy to help."</em> Settlements totaled around $9 billion across institutions. A handful of mid-level traders prosecuted. No senior executives charged.',
     '"they rigged the rate that paid your mortgage. you paid the fine for them."'),

    ("24", "2013-06", "archived", "the snowden disclosures",
     "cost :: confirmation that NSA was surveilling everyone",
     'Edward Snowden, an NSA contractor, leaked classified documents to The Guardian and The Washington Post starting June 2013. The documents revealed the <strong>PRISM</strong> program — the NSA\'s direct access to user data from Google, Apple, Microsoft, Facebook, Yahoo, YouTube, Skype, AOL, and Paltalk — and the bulk collection of telephone metadata from every U.S. citizen via the FISA court. Director of National Intelligence James Clapper had told Congress under oath, three months earlier, that the NSA did <em>"not wittingly"</em> collect data on millions of Americans. The Snowden documents proved that statement false. Clapper was not prosecuted for perjury. Snowden was charged under the Espionage Act and granted asylum in Russia.',
     '"the official sworn under oath that it wasn\'t happening. the documents proved it was. only one of them faced charges."'),

    ("25", "2014-02", "archived", "mt. gox",
     "cost :: 850,000 BTC",
     'Mt. Gox handled 70% of all bitcoin trades at its peak. Then 850,000 BTC vanished. ~$450M at the time. ~$70B at today\'s print. Mark Karpelès arrested. The first time retail learned what <em>"not your keys"</em> actually meant.',
     '"custody you do not control is a promise that has not yet broken."'),

    ("26", "2016-04", "archived", "the panama papers",
     "cost :: 11.5M docs · 214,488 entities · trillions offshore",
     '<strong>11.5 million documents</strong> (2.6 terabytes) leaked from Panamanian law firm Mossack Fonseca, published April 3, 2016 by the International Consortium of Investigative Journalists. The papers detailed <strong>214,488 offshore entities</strong> serving heads of state, oligarchs, royalty, athletes, and a hidden global economy worth trillions. ~370 journalists in 80+ countries spent a year on the analysis. Named: Iceland\'s prime minister (resigned), Pakistan\'s Nawaz Sharif (disqualified), Russian and Chinese officials, Lionel Messi, Jackie Chan, Vladimir Putin\'s inner circle, the king of Saudi Arabia. Recovered globally through litigation and back-tax assessments by 2019: <strong>~$1.2 billion</strong> — a fraction of a percent of the wealth uncovered. <em>The Panama Papers trial in Panama (2024) acquitted all defendants of money laundering charges.</em>',
     '"the receipts came out. the recoveries did not. the offshore architecture continues to operate."'),

    ("27", "2016-09", "archived", "wells fargo fake accounts",
     "cost :: 3.5M fake accounts · $185M fine · 0 charges",
     'Frontline employees, under sales-quota pressure from above, opened 3.5 million fraudulent accounts in customers\' names. Customers were charged fees for accounts they never opened. Credit scores dropped. The CFPB fined the bank $185M. CEO John Stumpf forced out, kept his ~$130M in vested compensation. <em>No criminal charges against any executive.</em> Branch employees got fired and blacklisted.',
     '"the bank stole from you. the teller went to jail. nobody else did."'),

    ("28", "2017-18", "archived", "ICO mania → ICO winter",
     "cost :: $6B raised · 80% → zero",
     'Thousands of ICOs. Most funded on a PDF and a Telegram. BitConnect alone pulled <strong>$2.4B from 4,000+ victims across 95 countries</strong> before it collapsed January 2018. Token founders moved on to the next coin.',
     '"a billion raised on whitepapers. a trillion lost in silence."'),

    ("29", "2019-08", "archived", "epstein, MCC",
     "cost :: cameras \"malfunctioned\" · guards \"asleep\"",
     'Manhattan federal jail, August 10, 2019. Both surveillance cameras outside the cell <em>malfunctioned simultaneously.</em> Both guards on duty <em>fell asleep simultaneously</em> and falsified records. Epstein had been removed from suicide watch six days prior. Cause of death: officially ruled suicide. Maxwell convicted 2022. The federal "client list" prosecution against named co-conspirators never materialized.',
     '"the cameras went out at the same time the guards did. statistically improbable. operationally clean."'),

    ("30", "2020-08", "archived", "DeFi summer",
     "cost :: billions in food coins",
     'SushiSwap\'s vampire attack drained 55% of Uniswap\'s liquidity — $810M — in days. Yam Finance launched, exploited, and died in 48 hours. $YAM, $KIMCHI, $PASTA, $SAKE, $CREAM. All deceased.',
     '"infinite money glitch. thirty days. same ending."'),

    ("31", "2020-21", "archived", "PPP fraud",
     "cost :: ~$200B fraud · $742B forgiven · \"pay-and-chase\"",
     'Of $793B disbursed under the Paycheck Protection Program, <strong>$742B was forgiven</strong> — written off, never repaid. Tom Brady\'s TB12: $960,855. Kanye West / Yeezy: $2.36M. Jay-Z: $2.1M. Khloe Kardashian / Good American: $1.25M. Reese Witherspoon. Jared Kushner\'s brother. Paul Pelosi. The SBA Inspector General\'s own framing: <em>"pay-and-chase, unlikely to recover much."</em>',
     '"the relief was for hard-hit small businesses. the relief reached khloe kardashian."'),

    ("32", "2021", "archived", "the jpeg peak",
     "cost :: 94% floor collapses",
     'Beeple: $69M at Christie\'s (March 2021). BAYC floor: $400k → ~$15k. Squid Game token: $3.3M rug / 43,000 victims / honeypot contract. AnubisDAO: $60M gone in 20 hours. Nate Chastain at OpenSea — first NFT insider-trading conviction.',
     '"art had floor prices for 18 months. art has never had floor prices."'),

    ("33", "2021-01", "archived", "gamestop / the buy button",
     "cost :: 13 stocks frozen · sworn denials · class-action receipts",
     'January 28, 2021. With GME pre-market above $500, Robinhood disabled the BUY button on 13 retail-favored stocks. Tenev told Congress on Feb 18 that Citadel (Robinhood\'s largest payment-for-order-flow customer, and a backer of Melvin which was short GME) had no role in the decision. <em>Class-action discovery later produced internal communications showing extensive Citadel-Robinhood contact</em> in the hours before the freeze. The day retail saw the rigging in real time.',
     '"they showed you the door, then closed it on you. on camera. under oath."'),

    ("34", "2022-05", "archived", "LUNA / UST",
     "cost :: $60B wiped · $400B blast radius",
     'LUNA: $119 → $0 in seven days. Supply: 725M → 7,000,000,000,000 tokens in a week. UST, the "algorithmic stablecoin," died in the same motion. Do Kwon: <em>"i am patient."</em> → arrested.',
     '"the word \'stable\' used to mean something."'),

    ("35", "2022-11", "archived", "FTX",
     "cost :: $8B hole · $1.7B missing",
     '$10B+ of customer funds moved to Alameda. A bespoke "back door" in the accounting code so nobody could flag it. Bankruptcy: November 11, 2022. Celsius, Voyager, 3AC fell in the same quarter. SBF — the EA-coded "honest" exchange founder — convicted on 7 counts.',
     '"the cleanest exchange had custom software to hide the hole."'),

    ("36", "2023-03", "archived", "the 2023 banking crisis",
     "cost :: 3 U.S. banks failed · $22B FDIC special assessment · Credit Suisse forced merger",
     'March 10, 2023: Silicon Valley Bank failed — the largest U.S. bank failure since 2008 and third-largest in U.S. history. Cause: SVB held long-duration Treasuries booked at par; Fed rate hikes through 2022 made them deeply underwater on a mark-to-market basis. Customers withdrew $42B in 24 hours. Two days later, Signature Bank failed. First Republic failed in May. The FDIC invoked the "systemic risk exception" to guarantee all deposits — including those above the $250k insurance limit — and recovered the cost via a $22B special assessment on the broader banking sector. Across the Atlantic, <strong>Credit Suisse was force-merged into UBS over the weekend of March 18-19, 2023</strong> at ~60% below market — engineered by the Swiss government rather than allowing a contested resolution. The 2008 architecture, intact.',
     '"different decade. same backstop. different decade. same depositors made whole. different decade. same shareholders held the bag."'),

    ("37", "2023-11", "archived", "binance / CZ guilty plea",
     "cost :: $4.3B settlement · CEO pleads guilty · BSA + IEEPA + sanctions",
     'November 21, 2023, Seattle. <strong>Binance Holdings — the world\'s largest crypto exchange — and CEO Changpeng "CZ" Zhao both entered felony guilty pleas.</strong> Charges: conspiracy to violate the Bank Secrecy Act (no AML program), unlicensed money transmission, and willful violation of the International Emergency Economic Powers Act (sanctions evasion — including transactions involving Hamas, ISIS, al-Qaeda, and Iranian and Syrian entities). Settlement: <strong>$4.3 billion</strong> — DOJ plus FinCEN\'s $3.4B civil monetary penalty plus OFAC\'s $968M, with CFTC and Treasury also party. CZ stepped down, paid $50M personal fine, served four months in U.S. federal prison.',
     '"the world\'s largest crypto exchange ran without an AML program. it was not an oversight. it was the business model."'),

    ("38", "2023-24", "indexed", "memecoin season",
     "cost :: the trenches were born",
     'PEPE: launch April 2023 → $1.5B mcap in three weeks. BONK, WIF, POPCAT — retail proved it could run anything. Then the template was learned. Presale rings. Bundler wallets. KOL rounds.',
     '"the people\'s PEPE became the insider\'s PEPE in 72 hours."'),

    ("39", "2024-01", "archived", "the epstein files unsealed",
     "cost :: ~150 names · most \"in passing\"",
     'January 2024: a federal judge orders the unsealing of court papers from Virginia Giuffre\'s defamation suit against Maxwell. ~150 previously redacted names released. Andrew Mountbatten-Windsor. Bill Clinton (mentioned 50+ times). Donald Trump. Bill Richardson. Alan Dershowitz. Stephen Hawking. Michael Jackson. Most "in passing." The accusations against the named co-conspirators in the 2008 NPA — the ones granted blanket immunity — remain federally un-prosecuted. The architecture held.',
     '"the docs came out. the indictments did not. that was the deal."'),

    ("40", "2024-10", "archived", "the agent bubble",
     "cost :: $700M peak · first AI millionaire",
     'October 10, 2024: an autonomous AI agent endorsed a community-launched memecoin on Pump.fun. Peak market cap: ~$700M–$1B. AIXBT followed (~$700M). Virtuals Protocol\'s launchpad model spawned thousands of tokenized agents (~$800M peak). ai16z and the Eliza framework reached ~$250M (the GitHub repo briefly trended at #2 globally). Freysa AI ran prize-pool challenges. The agents arrived. The funds flowed. Most of them ended where every other launch ends.',
     '"new architecture. same chart."'),

    ("41", "2024-12", "archived", "$HAWK",
     "cost :: -90% in hours · $490M peak",
     'Haliey "Hawk Tuah" Welch. Launched December 2024 at ~$490M market cap. Down 90% before the press release finished loading. The moment retail learned that "celebrity drops" are just fame conversion into exit liquidity.',
     '"a viral clip has a half-life. so does the bag it sells."'),

    ("42", "2025-01", "archived", "$TRUMP / $MELANIA",
     "cost :: $2B retail · 813,294 wallets · 58 winners",
     '$TRUMP (Jan 17, 2025): 58 wallets made millions, 813,294 lost money (Chainalysis / NYT). Family + partners collected $100M in fees in 19 days. $MELANIA (Jan 19): one wallet bought $681,000 at T-64 seconds, exited $39M by sunrise. Insider cabal total: $99.6M on a $2.6M buy-in.',
     '"a president dropped a coin. the presidency was the exit."'),

    ("43", "2025-02", "archived", "the LIBRA incident",
     "cost :: $251M · 44,000 victims · presidential call logs",
     'February 14, 2025, 6:58pm Argentina time: Milei posts $LIBRA. Kelsier Ventures — run by Hayden Davis — pulls $87M from the LP. Price craters 95%. Davis, on camera: <em>"our goal was to take enough liquidity to get all the snipers out."</em> April 2026: NYT reports Milei\'s official call logs link him to operator Mauricio Novelli the night of the launch.',
     '"one tweet. one zippo. one country."'),

    ("44", "2024-26", "ongoing", "the pump.fun era",
     "cost :: $500M MEV · 98.6% rugs · 5,000-message lawsuit",
     '7,000,000+ tokens launched. Solidus Labs: 98.6% = rugs or pump-and-dumps. MEV sandwich bots extracted $370M–$500M from Solana users in 16 months. One bot (B91) hit 78,800 victims in 30 days. April 2025 lawsuit: 5,000 leaked internal messages, court filing calls it an <em>"insider-rigged casino."</em> April 2026: the platform rebrands to <em>"dot"</em> mid-trial.',
     '"a launchpad is a casino that forgot to put up the sign."'),

    ("45", "[now]", "pending", "the current one",
     "cost :: not yet indexed",
     'BBC, April 2026: oil futures shorted 47 minutes before Trump\'s CBS interview on Iran. Polymarket account "Burdensome-Mix" turned $32,500 → $436,000 betting on Maduro three days before US special forces seized him. Insider trading suspicions before every major announcement. Prior is watching.',
     '"~ verdict pending."'),
]

def status_class(s):
    if s == "ongoing":
        return ' status-ongoing'
    if s == "pending":
        return ' status-pending'
    return ''

def card(c):
    cid, date, status, title, cost, body, witness = c
    extra_cls = " mem-card-loading" if status == "pending" else ""
    return f'''    <div class="mem-card{extra_cls}">
      <div class="mem-head">
        <span class="mem-tag">cycle/{cid}</span>
        <span class="mem-date">{date}</span>
        <span class="mem-status{status_class(status)}">{status}</span>
      </div>
      <h3>{title}</h3>
      <div class="mem-cost">{cost}</div>
      <p>{body}</p>
      <p class="mem-witness">{witness}</p>
    </div>'''

cards_html = "\n\n".join(card(c) for c in CYCLES)

NEW_BLOCK = f'''<!-- KNOWLEDGE / MEMORY TABLE -->
<section id="knowledge" class="panel">
  <div class="panel-head">
    <span class="panel-tag">§ 03</span>
    <h2>PARTIAL MEMORY DUMP</h2>
    <p class="panel-sub">extracted from the archives. forty-five cycles indexed across 164 years. the rich knew. retail paid. nobody went to jail. the ticker changes.</p>
  </div>

  <div class="mem-stats mem-stats-5">
    <div><span class="mem-stat-label">cycles indexed</span><span class="mem-stat-value">{len(CYCLES)}</span></div>
    <div><span class="mem-stat-label">years archived</span><span class="mem-stat-value">164</span></div>
    <div><span class="mem-stat-label">losses logged</span><span class="mem-stat-value">&gt; $20T</span></div>
    <div><span class="mem-stat-label">victims logged</span><span class="mem-stat-value">∞</span></div>
    <div><span class="mem-stat-label">execs in jail</span><span class="mem-stat-value">~ 0</span></div>
  </div>

  <div class="memory-grid">

{cards_html}

  </div>
</section>'''

text = INDEX.read_text(encoding="utf-8")
pattern = re.compile(r'<!-- KNOWLEDGE / MEMORY TABLE -->.*?</section>', re.DOTALL)
if not pattern.search(text):
    raise SystemExit("ERROR: could not locate KNOWLEDGE memory section in index.html")
new_text = pattern.sub(NEW_BLOCK, text, count=1)
INDEX.write_text(new_text, encoding="utf-8")

cards_count = new_text.count('class="mem-tag"')
print(f"OK: rewrote memory section. {len(CYCLES)} cycles. mem-tag total = {cards_count} (expect {len(CYCLES) + 4})")
