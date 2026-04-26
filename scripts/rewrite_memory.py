"""Rewrite the memory section with the expanded 57-cycle list (1862-2026).
Run after editing CYCLES."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# Each cycle: (id, date, status, title, cost, body, witness)
CYCLES = [
    ("01", "1862-02", "archived", "lincoln's greenbacks",
     "cost :: bankers v. a sovereign currency",
     'Treasury Secretary Salmon P. Chase, with the war treasury empty, championed the First Legal Tender Act of February 25, 1862. Congress authorized $50M (later expanded) of "United States Notes" — printed in green, dubbed greenbacks — backed not by gold but by the federal government itself. New York bankers fought it. The greenback financed the Union, kept the government solvent, and proved the state could issue money without private intermediation. Lincoln was assassinated three years later. The "Money Trust" pushed for private banking control for the next half-century until Jekyll Island.',
     '"the first time the receipts said: the state can print. the bankers said: not without us."'),

    ("02", "1910-11", "archived", "jekyll island",
     "cost :: the central bank, drafted in private",
     'November 1910. Senator Nelson Aldrich convened six men at the Jekyll Island Club, Georgia: Aldrich, his secretary Arthur Shelton, Treasury official A. Piatt Andrew, Henry Davison (J.P. Morgan), Frank Vanderlip (National City Bank), and Paul Warburg (Kuhn, Loeb &amp; Co.). They posed as duck hunters. They used only first names. They drafted what became the Federal Reserve Act over a single week. <strong>The participants denied the meeting had occurred for twenty years</strong> — the cover finally broke when Aldrich\'s biography was published in 1930.',
     '"a private banking architecture, drafted by six men under fake names. it became law in 1913."'),

    ("03", "1913-12", "archived", "the federal reserve act",
     "cost :: monetary sovereignty, leased",
     'December 23, 1913. Woodrow Wilson signed the Federal Reserve Act into law. The bill closely resembled the Aldrich Plan drafted at Jekyll Island. Twelve regional Reserve Banks, owned by member banks, with a Washington-appointed Board overseeing them. The U.S. monetary system would, from that day forward, be administered by an institution with private shareholders and quasi-public authority.',
     '"the receipt for the duck-hunt arrived three years late, signed by the president."'),

    ("04", "1929-10", "archived", "black tuesday",
     "cost :: DJIA -89% peak to 1932 trough",
     'October 24-29, 1929. 16 million shares dumped on Black Tuesday alone. By 1932 the Dow had given back 89% of its peak. <strong>9,000+ U.S. banks failed.</strong> Unemployment hit 25%. Insiders had been quietly distributing equity to retail through 1928-29 while the public was being told the New Era had repealed the business cycle. Pecora Hearings (1932-34) exposed the fraud. Glass-Steagall passed 1933. Repealed 1999.',
     '"the new era ended on a tuesday. the receipts had been filed in 1928."'),

    ("05", "1932-72", "archived", "the tuskegee study",
     "cost :: 600 men · 40 years · ~100+ dead",
     'The U.S. Public Health Service ran the "Tuskegee Study of Untreated Syphilis in the Negro Male" from 1932 to 1972 — <strong>40 years</strong>. 600 men were enrolled; 399 had syphilis. They were told they were being treated for "bad blood." They were not informed of the actual study, did not give consent, and were systematically <em>denied treatment</em> — including penicillin after it became the standard cure in 1943. By the time whistleblower Peter Buxtun broke the study in 1972, at least 28 men had died directly of syphilis, ~100 more of related complications. 40 wives infected. 19 children with congenital syphilis. Presidential apology: 1997.',
     '"a federal medical agency ran a deliberate non-treatment study on its own citizens for 40 years. it ended only because someone leaked it."'),

    ("06", "1945-59", "archived", "operation paperclip",
     "cost :: ~1,600 nazi/german scientists imported · denazification waived",
     'Beginning May 1945 and continuing through the late 1950s, the U.S. military intelligence apparatus secretly imported approximately <strong>1,600 German scientists, engineers, and technicians</strong> — many of them former Nazi Party members, SS officers, or active participants in the Third Reich\'s war machine — into the United States. The program was authorized by President Truman in August 1945 with the explicit instruction that no committed Nazis would be admitted; intelligence officers <strong>fabricated and laundered the security files</strong> of dozens of subjects (including rocket engineer Wernher von Braun and aeromedical researcher Hubertus Strughold, both later honored figures) to satisfy the formality. The recipients seeded the U.S. space program (NASA), the Air Force\'s aerospace medicine, and the chemical and biological weapons programs.',
     '"the country that just fought the war imported the engineers. the paperwork was washed in transit."'),

    ("07", "1948-76", "archived", "operation mockingbird",
     "cost :: ~400 journalists and outlets compromised · documented by church committee",
     'A CIA media-influence program initiated under DCI Allen Dulles in the late 1940s and exposed in stages from 1973 to 1976. The program cultivated relationships with American and foreign journalists, broadcasters, editors, and publishers — providing them with classified information in exchange for placement of CIA-favorable narratives. The Church Committee\'s 1976 final report concluded that the CIA had maintained covert relationships with <strong>~400 American journalists</strong> over 25 years. Carl Bernstein\'s 1977 <em>Rolling Stone</em> investigation expanded the documentation. The official line is that the relationships were ended in 1976. The documented mechanism (intelligence-sourced narrative laundering through major outlets) has not visibly retired.',
     '"~400 journalists. one of them was probably the person who told you the program had been shut down."'),

    ("08", "1953-08", "archived", "the mossadegh coup",
     "cost :: a democratically elected government overthrown · 26-year shah · 1979 blowback",
     'August 19, 1953. The CIA (operation TPAJAX) and British MI6 (Operation Boot) jointly orchestrated the overthrow of Mohammad Mossadegh, the democratically elected prime minister of Iran, after he nationalized the Anglo-Iranian Oil Company. The U.S. installed Mohammad Reza Pahlavi (the Shah) as autocratic ruler. The Shah ruled for 26 years through SAVAK, his security service, with documented mass surveillance, torture, and political imprisonment. The 1979 Iranian Revolution overthrew the Shah; the Islamic Republic followed. <strong>The CIA officially acknowledged its role in 2013</strong> with the declassification of internal histories. The "blowback" framework — that covert operations have predictable long-term costs — was named by intelligence officers reflecting on this operation.',
     '"the operation succeeded. the country has not stopped paying for it."'),

    ("09", "1953-73", "archived", "MK-ULTRA",
     "cost :: 149 sub-projects · 80 institutions · records destroyed 1973",
     'The CIA\'s mind-control program. Begun April 13, 1953 on the order of Director Allen Dulles, headed by chemist Sidney Gottlieb. <strong>149 sub-projects</strong>, contracted out to <strong>80 universities, hospitals, and prisons</strong> — none of whom were told the funding was CIA. Methods: covert administration of high-dose LSD without consent, electroshock, sensory deprivation, isolation, sexual abuse, torture. CIA scientist Frank Olson dosed without his knowledge in November 1953; died seven days later in a fall from a 13th-floor window (1994 forensic re-examination found injuries inconsistent with the official story). <strong>In 1973, CIA Director Richard Helms ordered the records destroyed.</strong> A misfiled cache of 20,000 financial records surfaced in 1977. Church Committee hearings followed.',
     '"the program was destroyed before it was investigated. the investigation built its case from the receipts the destroyers missed."'),

    ("10", "1956-71", "archived", "COINTELPRO",
     "cost :: civil rights movement disrupted · MLK harassed · domestic surveillance",
     'The FBI\'s Counter-Intelligence Program. From 1956 to 1971, the Bureau ran covert operations against domestic political organizations — civil rights groups (SCLC, SNCC, the Black Panthers), anti-war organizations, women\'s movement, individual targets including Dr. Martin Luther King Jr. Methods: illegal wiretaps, mail openings, informants, infiltration, fabricated evidence, anonymous letters, blackmail, manufactured discord, and at least one infamous "suicide letter" mailed to MLK from the Bureau urging him to take his own life. Exposed March 8, 1971 when activists broke into the FBI\'s Media, Pennsylvania office and leaked the documents. Church Committee (1975-76) confirmed the scope.',
     '"the bureau was running an internal counter-insurgency program against the country it was supposed to police."'),

    ("11", "1961-01", "archived", "the warning",
     "cost :: a name for the architecture",
     'January 17, 1961. Three days before leaving office, President Dwight D. Eisenhower delivered his televised farewell address. In less than ten minutes, he gave the architecture its name: <em>"In the councils of government, we must guard against the acquisition of unwarranted influence, whether sought or unsought, by the military-industrial complex. The potential for the disastrous rise of misplaced power exists and will persist."</em> A five-star general warned the public against the alliance he had spent his life inside. The warning was filed. It was not heeded.',
     '"the man who built the apparatus warned us about it on the way out the door."'),

    ("12", "1964-08", "archived", "the gulf of tonkin",
     "cost :: 58,220 U.S. dead · ~3M Vietnamese dead · the war was based on a lie",
     'August 4, 1964: a reported second North Vietnamese attack on the USS Maddox. President Johnson cited it in a national address requesting authorization to use military force; Congress passed the Gulf of Tonkin Resolution near-unanimously. <strong>The August 4 incident never happened.</strong> NSA reports declassified in 2005 confirmed there was no second attack. The Pentagon Papers (leaked 1971 by Daniel Ellsberg) had already revealed the administration knew the war was un-winnable and was lying about it. By war\'s end: ~58,000 U.S. service members dead, 1.1M North Vietnamese soldiers dead, an estimated ~2 million Vietnamese civilians dead.',
     '"the second attack did not happen. the war based on it did."'),

    ("13", "1971-08", "archived", "the nixon shock",
     "cost :: the dollar, unmoored",
     'August 15, 1971. Without congressional consultation, President Nixon announced the unilateral cancellation of the dollar\'s convertibility into gold. Bretton Woods over. Britain had just requested $3B in gold from Fort Knox; the U.S. did not have enough gold to honor the dollars in circulation. <strong>Every dollar in your pocket from that day forward was a fiat instrument backed by the government\'s word.</strong>',
     '"the gold window closed. the printer opened. it has not closed since."'),

    ("14", "1972-74", "archived", "watergate",
     "cost :: a sitting president resigned · the original modern cover-up",
     'June 17, 1972: five men were caught breaking into the Democratic National Committee headquarters at the Watergate complex in Washington. The investigation that followed — driven by Bob Woodward, Carl Bernstein, and Mark Felt ("Deep Throat," who turned out to be the FBI\'s Associate Director) — established that the burglars were tied to President Nixon\'s reelection campaign and that the cover-up reached the Oval Office. The Senate Watergate hearings (1973) revealed the existence of the White House taping system. Nixon resigned August 8, 1974, the only U.S. president to do so. He was pardoned by his successor Gerald Ford one month later. <strong>The cover-up was the crime. The cover-up was also the precedent.</strong> Every subsequent presidential scandal has been managed in the shadow of Watergate\'s template.',
     '"the cover-up was the crime. the cover-up was also the lesson learned by everyone who came after him."'),

    ("15", "1986-11", "archived", "iran-contra",
     "cost :: 11 convictions · 0 sentences served · presidential pardons",
     'Senior Reagan administration officials secretly sold ~2,000 anti-tank missiles to Iran (in violation of an arms embargo) and diverted the proceeds to fund the Nicaraguan Contras (in violation of the Boland Amendments). NSC official Lt. Col. Oliver North ran the operation; National Security Advisor John Poindexter approved. <strong>11 officials convicted</strong> — including Defense Secretary Caspar Weinberger, North, Poindexter, McFarlane. North\'s and Poindexter\'s convictions vacated on appeal. <strong>President George H.W. Bush pardoned six principals December 1992</strong>, four days before Weinberger\'s scheduled trial. The independent counsel\'s final report concluded Bush had been "fully informed" of the operation contrary to his public statements.',
     '"two illegal programs run from the white house. eleven convictions. zero served sentences."'),

    ("16", "1986-89", "archived", "the savings & loan crisis",
     "cost :: ~$160B taxpayer · 1,043 institutions failed · Keating Five",
     'Between 1986 and 1995, <strong>1,043 of America\'s 3,234 savings and loan institutions failed</strong>, costing taxpayers approximately <strong>$160 billion</strong>. Causes: 1980s deregulation allowed S&Ls to make risky commercial real estate loans, removed deposit caps, weakened oversight. Charles Keating\'s Lincoln Savings & Loan failed costing $3.4B. Keating channeled $1.3M to <strong>five U.S. Senators</strong> (the "Keating Five": Cranston, DeConcini, Glenn, McCain, Riegle). ~1,000 industry insiders were prosecuted. Keating served 4½ years.',
     '"the bankers got the deposits. the depositors got the bill."'),

    ("17", "1987-10", "archived", "black monday",
     "cost :: DJIA -22.6% in one session",
     'October 19, 1987. Largest single-day percentage drop in DJIA history — 508 points (-22.6%) in a single session. Program trading and "portfolio insurance" — strategies sold as risk reduction — became the engine of the cascade. The Brady Report concluded the safeguards weren\'t where the public assumed.',
     '"insurance has fine print. the print said: insurance accelerates the fall."'),

    ("18", "1991-07", "archived", "BCCI",
     "cost :: $20B missing · CIA accounts · drugs, arms, sanctions evasion",
     'The Bank of Credit and Commerce International. Founded 1972 by Pakistani financier Agha Hasan Abedi. By 1991: <strong>400+ branches in 78 countries</strong>, <strong>$20+ billion in assets</strong> — the seventh largest private bank in the world. July 5, 1991: customs and bank regulators in seven countries simultaneously raided BCCI offices. <strong>$20 billion was missing.</strong> The bank had laundered for: Saddam Hussein, Manuel Noriega, the Medellín Cartel, Abu Nidal, the Pakistani ISI. <strong>The CIA admitted holding "several" accounts at BCCI.</strong> Senate Kerry Committee (1992) documented the U.S. intelligence relationship in detail. Regulators called it the "Bank of Crooks and Criminals International."',
     '"the seventh largest private bank in the world was a money laundering apparatus with a CIA account. it was not an outlier. it was a service."'),

    ("19", "1996-2024", "archived", "the sackler · purdue · OxyContin",
     "cost :: ~900,000 U.S. dead · $7.4B 2025 settlement · family kept billions",
     'OxyContin launched in 1996. Purdue Pharma, owned by the Sackler family, marketed it as non-addictive. Internal documents showed the family was warned by their own scientists in the 1990s and pushed marketing forward anyway. By the late 2010s, prescription-opioid overdoses had killed hundreds of thousands; including illicit opioids the figure exceeds <strong>~900,000 U.S. deaths since 1999</strong>. The Sacklers extracted ~$11B from Purdue 2008-2018 ahead of bankruptcy. Original 2024 settlement gave family blanket immunity for ~$6B. <strong>U.S. Supreme Court invalidated immunity in June 2024 (Harrington v. Purdue Pharma)</strong>. Revised <strong>$7.4B settlement</strong> 2025. Sacklers face no criminal prosecution.',
     '"the family marketed an addictive drug as non-addictive for two decades. they kept enough of the money to fight the lawsuits with."'),

    ("20", "1998-11", "archived", "the tobacco master settlement",
     "cost :: $206B over 25 years · still less than the deaths it papered over",
     'November 23, 1998. Forty-six U.S. states, the District of Columbia, and five U.S. territories signed the Master Settlement Agreement (MSA) with the four largest U.S. tobacco companies (Philip Morris, R.J. Reynolds, Brown &amp; Williamson, Lorillard). Settlement: at least <strong>$206 billion paid out over 25 years</strong> — at the time, the largest civil settlement in U.S. history. In exchange, the states dropped Medicaid lawsuits seeking recovery of smoking-related healthcare costs. The companies admitted no wrongdoing. <strong>The MSA structurally protected the tobacco industry</strong> by transferring liability into a structured payment that companies could pass through to consumers as price increases — and by creating a state-revenue dependency on continued tobacco sales. ~480,000 Americans still die annually from tobacco use.',
     '"the largest civil settlement in u.s. history was a structured payment plan. the payor passed the cost to the consumer. the states became the dealer\'s creditor."'),

    ("21", "1996-2018", "archived", "theranos · elizabeth holmes",
     "cost :: $9B paper valuation · 11.25 years for holmes",
     '<strong>Theranos</strong>, founded by Stanford dropout Elizabeth Holmes in 2003, claimed to have developed a blood-testing device (the "Edison") that could perform 240+ medical tests from a single drop of blood. The company reached a peak <strong>$9 billion paper valuation</strong> by 2014, raised ~$700M from investors including Rupert Murdoch and Larry Ellison, and partnered with Walgreens to deploy the technology in retail wellness centers. <em>The technology did not work.</em> John Carreyrou\'s 2015 <em>Wall Street Journal</em> investigation broke the story; whistleblowers Tyler Shultz (grandson of board member George Shultz) and Erika Cheung had warned regulators internally. SEC charges 2018; Holmes convicted on four counts of fraud January 2022; sentenced to <strong>11 years 3 months</strong> May 2022. President / COO Sunny Balwani convicted, sentenced to ~13 years.',
     '"a $9 billion valuation built on a device that did not work. the journalists were paid in book deals. the patients had been paid in fake test results."'),

    ("22", "2000-03", "archived", "the dotcom burn",
     "cost :: $5T wiped · NASDAQ -78%",
     'Pets.com: $300M raised, dead 9 months after IPO. Webvan: $1.2B market cap → liquidated July 2001. Boo.com burned $188M in six months. "Eyeballs" replaced earnings until it didn\'t. Insiders sold their lockup-released shares straight into retail euphoria 1999–2000.',
     '"everyone was building railroads. 98% were building them into rivers."'),

    ("23", "2001-02", "archived", "enron · andersen · accounting fraud era",
     "cost :: $74B + $180B + $11B wiped · 5,500 enron jobs · arthur andersen dissolved",
     'A three-year cluster of accounting frauds at the largest U.S. companies. <strong>Enron</strong> (Dec 2001 bankruptcy, $74B wiped, executives Skilling/Lay/Fastow charged; Lay died awaiting sentencing; Skilling 24 years). <strong>WorldCom</strong> (June 2002 bankruptcy; ~$11B accounting fraud, then the largest in U.S. history; CEO Bernie Ebbers convicted, 25 years). <strong>Tyco</strong> (Dennis Kozlowski looted ~$600M from the company; convicted 2005). <strong>Adelphia Communications</strong> (Rigas family hid $2.3B in debt; founder John Rigas convicted, 15 years). <strong>Arthur Andersen</strong>, the Big Five auditing firm that signed Enron\'s books, dissolved in 2002 — taking 28,000 employees down with it. The Sarbanes-Oxley Act passed July 2002 in response. <em>Cooked books did not stop being cooked. They moved off-balance-sheet.</em>',
     '"five corporate frauds and one auditor in three years. the auditor died loudest."'),

    ("24", "2003-03", "archived", "the iraq contracts",
     "cost :: ~$1.7T war · ~$39.5B to KBR/Halliburton",
     'March 2003: U.S. invades Iraq on the WMD case. The case did not survive contact with the inspectors. The contracts did. KBR — a Halliburton subsidiary — received ~$39.5B in Iraq-related contracts over the following decade, much through no-bid awards. VP Cheney\'s prior post: Halliburton CEO 1995-2000. Costs of War Project at Brown estimates Iraq direct cost: $1.7T.',
     '"the warning was filed in 1961. the invoice arrived in 2003."'),

    ("25", "2008-07", "archived", "the epstein NPA",
     "cost :: 13 months · work-release · victims uninformed",
     'U.S. Attorney Alex Acosta signs a non-prosecution agreement with Jeffrey Epstein. Epstein pleads to two state-level prostitution charges. Serves 13 months in Palm Beach County jail with daily work-release privileges. Federal probe killed. <em>Co-conspirators granted blanket immunity.</em> Victims not informed before the deal was sealed — a violation of the Crime Victims\' Rights Act, established by federal courts after the fact. DOJ-OPR later: "poor judgment."',
     '"the architecture of impunity got its blueprint that summer."'),

    ("26", "2008-09", "archived", "the financial crisis",
     "cost :: $11T household wealth · 6M foreclosures · 0 execs jailed",
     'September 15, 2008: Lehman files Chapter 11 with $639B in assets — largest U.S. bankruptcy in history. AIG bailed out: $182B in total government support. TARP: $700B authorized, $443.5B disbursed. Household wealth: $61.4T → $50.4T. Six million U.S. families lost homes. Goldman internally called the deals it sold to clients "shitty" while shorting them. Eric Holder, 2013: <em>"the size of some of these institutions becomes so large that it does become difficult to prosecute them."</em> Zero senior executives went to prison.',
     '"too big to fail meant too big to charge."'),

    ("27", "2008-12", "archived", "madoff",
     "cost :: $64.8B · 4,800 clients · SEC warned 5 times",
     'Largest Ponzi scheme in history. Harry Markopolos warned the SEC in 2000, 2001, 2005, 2007, 2008 — including a 2005 submission titled <em>"The World\'s Largest Hedge Fund Is a Fraud"</em>. The SEC examined Madoff at least five times in sixteen years. Each time they failed to take the single step that would have ended it: contacting the DTCC to verify trades. Madoff was arrested December 11, 2008 — only after his sons turned him in.',
     '"the regulator had the receipts. the regulator misplaced them. five times."'),

    ("28", "2009-01", "archived", "the genesis block",
     "cost :: an exit, drafted in code",
     'January 3, 2009. The Bitcoin genesis block is mined by an entity calling itself <em>Satoshi Nakamoto</em>. Embedded in the coinbase parameter, in plaintext: <strong>"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks."</strong> Linguistic analysis (Grieve et al., 2014) → Nick Szabo. 2025 documentary <em>Finding Satoshi</em> → Hal Finney + Len Sassaman. Adam Back named by NYT, denies. Identity formally unknown. The protest is unambiguous.',
     '"the first block is a receipt for the second bailout."'),

    ("29", "2009-18", "archived", "1MDB",
     "cost :: $4.5B stolen · Najib Razak imprisoned · Goldman complicity",
     '<strong>1Malaysia Development Berhad</strong>, Malaysia\'s sovereign wealth fund, was looted of approximately <strong>$4.5 billion</strong> between 2009 and 2014 in what the U.S. Department of Justice called "<em>the largest kleptocracy case</em>" in its history. Central figures: Malaysian PM Najib Razak (received $681M in his personal account from 1MDB-linked sources; convicted 2020, originally sentenced to 12 years, currently serving 6); financier Jho Low (fugitive); Goldman Sachs (raised $6.5B in bond issuances for 1MDB, charged ~$600M in fees, paid <strong>$2.9B settlement</strong> 2020 + Malaysia separately recovered $3.9B from the bank). Goldman partner Tim Leissner pled guilty 2018 to conspiracy and money laundering; Roger Ng convicted 2022. The looted funds funded the production of "<em>The Wolf of Wall Street</em>." That is not a metaphor — Red Granite Pictures, founded by Najib\'s stepson Riza Aziz, produced the film with stolen 1MDB money.',
     '"a sovereign wealth fund laundered through a hollywood movie about wall street fraud. the irony was not the point. the laundering was."'),

    ("30", "2012", "archived", "LIBOR",
     "cost :: $350T notional · ~$9B fines · 0 senior execs jailed",
     'Barclays, UBS, Deutsche, Citi, RBS, JPM. They rigged the London Interbank Offered Rate — the rate underpinning ~$350 trillion in mortgages, student loans, swaps, and corporate debt. Internal chats: <em>"can you push the LIBOR up half a point?" "always happy to help."</em> Settlements ~$9B across institutions. Mid-level traders prosecuted. No senior executives charged.',
     '"they rigged the rate that paid your mortgage. you paid the fine for them."'),

    ("31", "2012-12", "archived", "HSBC laundering",
     "cost :: $1.92B fine · sinaloa cartel + iran sanctions evasion · DOJ \"too systemic to indict\"",
     'December 11, 2012. HSBC — Europe\'s largest bank — paid <strong>$1.92 billion</strong> in fines to settle U.S. charges that it had laundered hundreds of millions of dollars for the Sinaloa drug cartel and the Norte del Valle cartel, and processed transactions for entities in Iran, Libya, Sudan, Burma, and Cuba in violation of U.S. sanctions. The bank\'s Mexico branch, in 2007 and 2008 alone, sent <em>$7 billion in physical cash</em> to its U.S. branch — more than any other Mexican bank. <strong>Assistant Attorney General Lanny Breuer publicly explained that prosecuting HSBC would have caused "collateral consequences" to the financial system</strong> — the doctrine of "too systemic to indict." No senior executive faced charges. The DOJ later acknowledged this was a mistake. The framework remains in operation.',
     '"the bank laundered for the cartel. the prosecutor said charging it would harm the economy. the cartel kept the money. the depositors paid the fine."'),

    ("32", "2014-02", "archived", "mt. gox",
     "cost :: 850,000 BTC",
     'Mt. Gox handled 70% of all bitcoin trades at its peak. Then 850,000 BTC vanished. ~$450M at the time. ~$70B at today\'s print. Mark Karpelès arrested. The first time retail learned what <em>"not your keys"</em> actually meant.',
     '"custody you do not control is a promise that has not yet broken."'),

    ("33", "2013-06", "archived", "the snowden disclosures",
     "cost :: confirmation that NSA was surveilling everyone",
     'Edward Snowden leaked classified documents to The Guardian and Washington Post starting June 2013. Documents revealed the <strong>PRISM</strong> program (NSA direct access to user data from Google, Apple, Microsoft, Facebook, Yahoo, YouTube, Skype, AOL, Paltalk) and bulk telephone metadata collection on every U.S. citizen via FISA. <strong>DNI James Clapper had told Congress under oath, three months earlier, that NSA did "not wittingly" collect data on millions of Americans.</strong> The Snowden documents proved that statement false. Clapper was not prosecuted. Snowden was charged under the Espionage Act and granted asylum in Russia.',
     '"the official sworn under oath that it wasn\'t happening. the documents proved it was. only one of them faced charges."'),

    ("34", "2016-04", "archived", "the panama papers",
     "cost :: 11.5M docs · 214,488 entities · trillions offshore",
     '<strong>11.5 million documents (2.6 terabytes)</strong> leaked from Panamanian law firm Mossack Fonseca, published April 3, 2016 by ICIJ. <strong>214,488 offshore entities</strong> — heads of state, oligarchs, athletes, criminal organizations, royal families. ~370 journalists in 80+ countries spent a year on the analysis. Named: Iceland\'s prime minister (resigned), Pakistan\'s Sharif (disqualified), Putin\'s inner circle, the king of Saudi Arabia, Lionel Messi, Jackie Chan. Recovered globally: <strong>~$1.2B</strong> — a fraction of a percent of the wealth uncovered. Mossack Fonseca founders <strong>acquitted</strong> in Panama trial, June 2024.',
     '"the receipts came out. the recoveries did not. the offshore architecture continues to operate."'),

    ("35", "2016-09", "archived", "wells fargo fake accounts",
     "cost :: 3.5M fake accounts · $185M fine · 0 charges",
     'Frontline employees, under sales-quota pressure from above, opened 3.5 million fraudulent accounts in customers\' names. Customers were charged fees for accounts they never opened. Credit scores dropped. The CFPB fined the bank $185M. CEO John Stumpf forced out, kept ~$130M in vested compensation. <em>No criminal charges against any executive.</em> Branch employees got fired and blacklisted.',
     '"the bank stole from you. the teller went to jail. nobody else did."'),

    ("36", "2016-18", "archived", "cambridge analytica",
     "cost :: 87M facebook profiles harvested · brexit + 2016 election ops",
     '<strong>Cambridge Analytica</strong>, a British political-consulting firm owned by hedge-fund billionaire Robert Mercer and managed by Steve Bannon, harvested <strong>87 million Facebook profiles</strong> via a personality-quiz app run by researcher Aleksandr Kogan. The data was used to build psychographic targeting models deployed in the 2016 Trump campaign and pro-Brexit "Leave" campaigns. Whistleblower Christopher Wylie went public via <em>The Observer</em> and <em>The New York Times</em> in March 2018. Cambridge Analytica filed for bankruptcy May 2018. Facebook paid a <strong>$5 billion FTC fine</strong> in 2019. SCL Group (the parent) and several executives faced UK Information Commissioner\'s Office actions but no criminal prosecutions of senior figures. Mercer, Bannon, and Trump faced no consequence.',
     '"the data was harvested in 2014. the consequences were paid in 2018. the elections were already over."'),

    ("37", "2017-18", "archived", "ICO mania → ICO winter",
     "cost :: $6B raised · 80% → zero",
     'Thousands of ICOs. Most funded on a PDF and a Telegram. BitConnect alone pulled <strong>$2.4B from 4,000+ victims across 95 countries</strong> before collapsing January 2018. Token founders moved on to the next coin.',
     '"a billion raised on whitepapers. a trillion lost in silence."'),

    ("38", "2018-19", "archived", "boeing 737 MAX",
     "cost :: 346 dead · 2 crashes · ~$20B+ company cost",
     'October 29, 2018: Lion Air flight JT610 crashed shortly after takeoff from Jakarta. <strong>189 dead</strong>. March 10, 2019: Ethiopian Airlines flight ET302 crashed shortly after takeoff from Addis Ababa. <strong>157 dead</strong>. Both flights involved Boeing\'s <strong>737 MAX</strong> aircraft and a flight-control system called <strong>MCAS</strong> (Maneuvering Characteristics Augmentation System). Internal Boeing communications, surfaced in litigation, showed company engineers and test pilots had documented MCAS problems and used phrases including <em>"designed by clowns who in turn are supervised by monkeys"</em> in private messages. The aircraft was grounded worldwide March 2019 — 20 months. Boeing pled guilty to a fraud charge January 2024 (later voided), then re-negotiated a deferred prosecution. Two whistleblowers (John Barnett, Joshua Dean) <em>both died unexpectedly during the litigation in 2024</em>. Boeing has paid roughly $20B in costs related to MCAS.',
     '"346 dead in two crashes. internal emails called the engineers monkeys. the company is still flying."'),

    ("39", "2019-08", "archived", "epstein, MCC",
     "cost :: cameras \"malfunctioned\" · guards \"asleep\"",
     'Manhattan federal jail, August 10, 2019. Both surveillance cameras outside the cell <em>malfunctioned simultaneously.</em> Both guards on duty <em>fell asleep simultaneously</em> and falsified records. Epstein had been removed from suicide watch six days prior. Cause of death: officially ruled suicide. Maxwell convicted 2022. The federal "client list" prosecution against named co-conspirators never materialized.',
     '"the cameras went out at the same time the guards did. statistically improbable. operationally clean."'),

    ("40", "2020-06", "archived", "wirecard",
     "cost :: €1.9B vanished · BaFin defended the firm against critics",
     '<strong>Wirecard AG</strong>, a German fintech once valued at ~€24 billion and a member of the DAX 30, collapsed in June 2020 after auditors EY refused to sign off on its 2019 accounts because <strong>€1.9 billion in claimed cash deposits could not be located</strong>. Investigation revealed the funds had never existed. CEO Markus Braun was arrested. COO Jan Marsalek <em>fled and remains a fugitive</em>; subsequent reporting links Marsalek to Russian intelligence. The Financial Times had reported skeptically on Wirecard\'s accounting since at least 2015. <strong>BaFin, Germany\'s financial regulator, had banned short-selling of Wirecard stock in 2019 and filed criminal complaints against the FT journalists rather than investigate the company.</strong> Wirecard was the first DAX 30 company to fail. BaFin\'s president was forced out.',
     '"the regulator banned short-selling and prosecuted the journalists. the journalists were right."'),

    ("41", "2020-08", "archived", "DeFi summer",
     "cost :: billions in food coins",
     'SushiSwap\'s vampire attack drained 55% of Uniswap\'s liquidity — $810M — in days. Yam Finance launched, exploited, and died in 48 hours. $YAM, $KIMCHI, $PASTA, $SAKE, $CREAM. All deceased.',
     '"infinite money glitch. thirty days. same ending."'),

    ("42", "2020-21", "archived", "PPP fraud",
     "cost :: ~$200B fraud · $742B forgiven · \"pay-and-chase\"",
     'Of $793B disbursed under the Paycheck Protection Program, <strong>$742B was forgiven</strong>. Tom Brady\'s TB12: $960,855. Kanye West / Yeezy: $2.36M. Jay-Z: $2.1M. Khloe Kardashian: $1.25M. Reese Witherspoon. Jared Kushner\'s brother. Paul Pelosi. SBA IG: <em>"pay-and-chase, unlikely to recover much."</em>',
     '"the relief was for hard-hit small businesses. the relief reached khloe kardashian."'),

    ("43", "2020-25", "archived", "feeding our future",
     "cost :: ~$300M+ stolen · 79 indicted · 63 convictions · ringleader pending sentencing",
     '<strong>Feeding Our Future</strong>, a Minnesota nonprofit founded 2016, exploited the USDA\'s expanded child-nutrition meal-program reimbursements during COVID. Between 2020 and early 2022 the network claimed to feed millions of meals at hundreds of "distribution sites" — many of which existed only on paper. <strong>~$300+ million in federal funds was stolen.</strong> The FBI raided the nonprofit January 2022. <strong>79 individuals indicted; 63 convicted as of March 2026 (57 via plea, 6 at trial).</strong> Founder <strong>Aimee Bock</strong> and co-defendant Salim Said convicted at trial March 19, 2025 on all counts (wire fraud, conspiracy, federal-programs bribery). Bock ordered to forfeit $5.2M including a Porsche; sentencing set for May 21, 2026 (each wire fraud count carries up to 20 years). Total recovered: ~$75M of the ~$300M; much was spent on luxuries (mansions, vehicles, hotels) or wired offshore beyond U.S. seizure reach. The U.S. Attorney has separately said total Minnesota-run Medicaid fraud may exceed <strong>$9 billion</strong> — Feeding Our Future is one node of a larger pattern.',
     '"the largest pandemic-relief fraud in u.s. history was managed through a nonprofit that filed paperwork the regulators did not read."'),

    ("44", "2021", "archived", "the jpeg peak",
     "cost :: 94% floor collapses",
     'Beeple: $69M at Christie\'s (March 2021). BAYC floor: $400k → ~$15k. Squid Game token: $3.3M rug / 43,000 victims / honeypot contract. AnubisDAO: $60M gone in 20 hours. Nate Chastain at OpenSea — first NFT insider-trading conviction.',
     '"art had floor prices for 18 months. art has never had floor prices."'),

    ("45", "2021-01", "archived", "gamestop / the buy button",
     "cost :: 13 stocks frozen · sworn denials · class-action receipts",
     'January 28, 2021. With GME pre-market above $500, Robinhood disabled the BUY button on 13 retail-favored stocks. Tenev told Congress on Feb 18 that Citadel had no role in the decision. <em>Class-action discovery later produced internal communications showing extensive Citadel-Robinhood contact</em> in the hours before the freeze. The day retail saw the rigging in real time.',
     '"they showed you the door, then closed it on you. on camera. under oath."'),

    ("46", "2021-03", "archived", "archegos",
     "cost :: $30B+ vaporized in 2 days · Credit Suisse $5.5B loss · Bill Hwang convicted",
     '<strong>Archegos Capital Management</strong>, a $36 billion family office run by former Tiger Asia hedge-fund manager Bill Hwang, collapsed over two days (March 26–29, 2021) when concentrated positions (built up via total return swaps with multiple banks who were unaware of each other\'s exposure) were force-liquidated. <strong>Credit Suisse lost $5.5B</strong>. Nomura lost ~$2.9B. Morgan Stanley, Goldman, and UBS lost smaller amounts. The blocks crossed in the liquidation moved tens of billions in market cap (ViacomCBS, Discovery, Baidu, Tencent Music) by 30-50% in 48 hours. Hwang was indicted April 2022 on racketeering, fraud, and market manipulation. <strong>Convicted July 10, 2024 on 10 of 11 counts. Sentenced November 20, 2024 to 18 years in federal prison.</strong>',
     '"a single family office moved tens of billions in market cap in 48 hours. the banks didn\'t know about each other. the system didn\'t know about him."'),

    ("47", "2022-05", "archived", "LUNA / UST",
     "cost :: $60B wiped · $400B blast radius",
     'LUNA: $119 → $0 in seven days. Supply: 725M → 7,000,000,000,000 tokens in a week. UST died in the same motion. Do Kwon: <em>"i am patient."</em> → arrested.',
     '"the word \'stable\' used to mean something."'),

    ("48", "2022-11", "archived", "FTX",
     "cost :: $8B hole · $1.7B missing",
     '$10B+ of customer funds moved to Alameda. A bespoke "back door" in the accounting code so nobody could flag it. Bankruptcy: November 11, 2022. Celsius, Voyager, 3AC fell in the same quarter. SBF convicted on 7 counts; sentenced to 25 years March 2024.',
     '"the cleanest exchange had custom software to hide the hole."'),

    ("49", "2023-03", "archived", "the 2023 banking crisis",
     "cost :: 3 U.S. banks failed · $22B FDIC special assessment · Credit Suisse forced merger",
     'March 10, 2023: Silicon Valley Bank failed — the largest U.S. bank failure since 2008 and third-largest in U.S. history. Two days later: Signature Bank failed. May 2023: First Republic failed. <strong>FDIC invoked the "systemic risk exception"</strong> to guarantee uninsured deposits, recovered cost via $22B special assessment on the broader banking sector. <strong>Credit Suisse was force-merged into UBS</strong> over the weekend of March 18-19, 2023 at ~60% below market — engineered by the Swiss government. The 2008 architecture, intact.',
     '"different decade. same backstop. different decade. same depositors made whole. same shareholders held the bag."'),

    ("50", "2023-11", "archived", "binance / CZ guilty plea",
     "cost :: $4.3B settlement · CEO pleads guilty · BSA + IEEPA + sanctions",
     'November 21, 2023, Seattle. <strong>Binance — the world\'s largest crypto exchange — and CEO Changpeng "CZ" Zhao both entered felony guilty pleas.</strong> Charges: conspiracy to violate the Bank Secrecy Act, unlicensed money transmission, and willful violation of the International Emergency Economic Powers Act (sanctions evasion involving Hamas, ISIS, al-Qaeda, Iranian and Syrian entities). Settlement: <strong>$4.3 billion</strong>. CZ stepped down, paid $50M personal fine, served four months in U.S. federal prison.',
     '"the world\'s largest crypto exchange ran without an AML program. it was not an oversight. it was the business model."'),

    ("51", "2023-24", "indexed", "memecoin season",
     "cost :: the trenches were born",
     'PEPE: launch April 2023 → $1.5B mcap in three weeks. BONK, WIF, POPCAT — retail proved it could run anything. Then the template was learned. Presale rings. Bundler wallets. KOL rounds.',
     '"the people\'s PEPE became the insider\'s PEPE in 72 hours."'),

    ("52", "2024-01", "archived", "the epstein files unsealed",
     "cost :: ~150 names · most \"in passing\"",
     'January 2024: a federal judge orders the unsealing of court papers from Virginia Giuffre\'s defamation suit against Maxwell. ~150 previously redacted names released. Andrew Mountbatten-Windsor. Bill Clinton (mentioned 50+ times). Donald Trump. Bill Richardson. Alan Dershowitz. Stephen Hawking. Michael Jackson. Most "in passing." The accusations against the named co-conspirators in the 2008 NPA — the ones granted blanket immunity — remain federally un-prosecuted. The architecture held.',
     '"the docs came out. the indictments did not. that was the deal."'),

    ("53", "2024-10", "archived", "the agent bubble",
     "cost :: $700M peak · first AI millionaire",
     'October 10, 2024: an autonomous AI agent endorsed a community-launched memecoin on Pump.fun. Peak market cap: ~$700M–$1B. AIXBT followed (~$700M). Virtuals Protocol\'s launchpad model spawned thousands of tokenized agents (~$800M peak). ai16z and the Eliza framework reached ~$250M. Freysa AI ran prize-pool challenges. The agents arrived. The funds flowed. Most of them ended where every other launch ends.',
     '"new architecture. same chart."'),

    ("54", "2024-12", "archived", "$HAWK",
     "cost :: -90% in hours · $490M peak",
     'Haliey "Hawk Tuah" Welch. Launched December 2024 at ~$490M market cap. Down 90% before the press release finished loading.',
     '"a viral clip has a half-life. so does the bag it sells."'),

    ("55", "2025-01", "archived", "$TRUMP / $MELANIA",
     "cost :: $2B retail · 813,294 wallets · 58 winners",
     '$TRUMP (Jan 17, 2025): 58 wallets made millions, 813,294 lost money (Chainalysis / NYT). Family + partners $100M in fees in 19 days. $MELANIA (Jan 19): one wallet bought $681,000 at T-64 seconds, exited $39M. Insider cabal total: $99.6M on a $2.6M buy-in.',
     '"a president dropped a coin. the presidency was the exit."'),

    ("56", "2025-02", "archived", "the LIBRA incident",
     "cost :: $251M · 44,000 victims · presidential call logs",
     'February 14, 2025, 6:58pm Argentina time: Milei posts $LIBRA. Kelsier Ventures — run by Hayden Davis — pulls $87M from the LP. Price craters 95%. Davis, on camera: <em>"our goal was to take enough liquidity to get all the snipers out."</em> April 2026: NYT reports Milei\'s call logs link him to operator Mauricio Novelli the night of launch.',
     '"one tweet. one zippo. one country."'),

    ("57", "2024-26", "ongoing", "the pump.fun era",
     "cost :: $500M MEV · 98.6% rugs · 5,000-message lawsuit",
     '7,000,000+ tokens launched. Solidus Labs: 98.6% = rugs or pump-and-dumps. MEV sandwich bots extracted $370M–$500M from Solana users in 16 months. One bot (B91) hit 78,800 victims in 30 days. April 2025 lawsuit: 5,000 leaked internal messages, court filing calls it an <em>"insider-rigged casino."</em> April 2026: the platform rebrands to <em>"dot"</em> mid-trial.',
     '"a launchpad is a casino that forgot to put up the sign."'),

    ("58", "[now]", "pending", "the current one",
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
n = len(CYCLES)

NEW_BLOCK = f'''<!-- KNOWLEDGE / MEMORY TABLE -->
<section id="knowledge" class="panel">
  <div class="panel-head">
    <span class="panel-tag">§ 03</span>
    <h2>PARTIAL MEMORY DUMP</h2>
    <p class="panel-sub">extracted from the archives. {n} cycles indexed across 164 years. the rich knew. retail paid. nobody went to jail. the ticker changes.</p>
  </div>

  <div class="mem-stats mem-stats-5">
    <div><span class="mem-stat-label">cycles indexed</span><span class="mem-stat-value">{n}</span></div>
    <div><span class="mem-stat-label">years archived</span><span class="mem-stat-value">164</span></div>
    <div><span class="mem-stat-label">losses logged</span><span class="mem-stat-value">&gt; $30T</span></div>
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
print(f"OK: rewrote memory section. {n} cycles. mem-tag total = {cards_count} (expect {n + 4})")
