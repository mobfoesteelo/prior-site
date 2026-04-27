/* PRIOR · /watch · daily insider watch streamable view
 *
 * Pulls from data/insider-watch.json (generated daily by
 * scripts/insider_watch.py). Animates the latest report's thread
 * tweet-by-tweet. Rotates an archive spotlight in the background.
 * Crawls source feed headlines along the bottom.
 */

const REFRESH_MS = 60_000;          // re-fetch every 60s (catches new daily drops)
const TWEET_REVEAL_MS = 9_000;      // each tweet stays visible for this long before next reveals
const SPOTLIGHT_INTERVAL_MS = 5_500;
const CRAWL_REFRESH_MS = 5 * 60_000;

const $  = (s) => document.querySelector(s);
const escapeHTML = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
})[c]);
const fetchJSON = async (path) => {
  try {
    const r = await fetch(path + '?_=' + Date.now(), { cache: 'no-store' });
    if (!r.ok) return null;
    return await r.json();
  } catch (_) { return null; }
};

// ── REC clock ──────────────────────────────────────────────────────
const tickClock = () => {
  const now = new Date();
  const t = now.toISOString().slice(11, 19);
  const d = now.toISOString().slice(0, 10);
  const el = $('#rec-clock');
  if (el) el.textContent = `${d} ${t} UTC`;
};
setInterval(tickClock, 1000);
tickClock();

// ── archive spotlight (rotates through 65 cycles) ──────────────────
const SPOTLIGHT = [
  ['1986', 'IVAN BOESKY', '$100M penalty · 3 yrs · cooperator → milken'],
  ['1989', 'MICHAEL MILKEN', '$600M · 22 mos served · ~$3.7B net worth today'],
  ['2009', 'RAJ RAJARATNAM', '11 yrs · longest insider sentence ever · wiretap precedent'],
  ['2011', 'RAJAT GUPTA', '23 sec after the goldman board · 2 yrs served · the seat at the table was the asset'],
  ['2013', 'STEVEN COHEN / SAC', '$1.8B settlement · 0 charges for principal · rebranded point72 · ~$15B'],
  ['2014', 'MATHEW MARTOMA', '9 yrs · $276M elan/wyeth alzheimer\'s trade · refused to cooperate'],
  ['2017', 'PHIL MICKELSON', '$931K dean foods · DOJ declined to charge · walters got 5'],
  ['2020-02', 'SEN. BURR (R-NC)', 'sold $1.6M post-classified-covid briefing · probe closed'],
  ['2020-02', 'SEN. LOEFFLER (R-GA)', '$20M+ same window · bought citrix + dupont (PPE) · no charges'],
  ['2020-02', 'SEN. FEINSTEIN (D-CA)', '$1.5-6M sold pre-crash · no charges · pattern bipartisan'],
  ['2021-09', 'KAPLAN / ROSENGREN', 'fed presidents traded individual stocks during emergency policy · resigned · no charges'],
  ['2022-01', 'RICHARD CLARIDA', 'fed vice chair · "rebalanced" 3 days before powell rate cut · no charges'],
  ['2022-07', 'ISHAN WAHI', 'first crypto insider conviction · coinbase product manager tipped brother · 2 yrs'],
  ['2022', 'NATE CHASTAIN', 'first NFT insider conviction · opensea homepage was the leak · 3 mos'],
  ['2024-07', 'PAUL PELOSI', '$5M nvidia call options · weeks before CHIPS act vote · disclosed, never investigated'],
  ['2024-26', 'PUMP.FUN BUNDLERS', '5,000 leaked messages · "the platform was the insider"'],
  ['2026-04', 'OIL FUTURES SHORT', '47 minutes before trump\'s CBS Iran interview · BBC reporting · probe live'],
  ['2026-04', 'POLYMARKET / MADURO', '$32,500 → $436,000 · 3 days before US forces seized him'],
];

let spotlightIdx = 0;
const renderSpotlight = () => {
  const stage = $('#archive-spotlight');
  if (!stage) return;
  if (!stage.children.length) {
    SPOTLIGHT.forEach((s, i) => {
      const card = document.createElement('div');
      card.className = 'spotlight-card' + (i === 0 ? ' active' : '');
      card.innerHTML = `
        <div class="spotlight-yr">${escapeHTML(s[0])}</div>
        <div class="spotlight-name">${escapeHTML(s[1])}</div>
        <div class="spotlight-receipt">${escapeHTML(s[2])}</div>
      `;
      stage.appendChild(card);
    });
    return;
  }
  // advance
  const cards = stage.querySelectorAll('.spotlight-card');
  cards[spotlightIdx % cards.length].classList.remove('active');
  spotlightIdx = (spotlightIdx + 1) % cards.length;
  cards[spotlightIdx].classList.add('active');
};
renderSpotlight();
setInterval(renderSpotlight, SPOTLIGHT_INTERVAL_MS);

// ── thread reveal animation ────────────────────────────────────────
let threadRevealTimer = null;
let threadRevealIdx = 0;

const renderThread = (tweets, dateStr) => {
  const stage = $('#thread-stage');
  if (!stage) return;
  if (threadRevealTimer) {
    clearInterval(threadRevealTimer);
    threadRevealTimer = null;
  }
  threadRevealIdx = 0;

  if (!tweets || !tweets.length) {
    stage.innerHTML = `<div class="loading">— no report today (yet) — daily run fires at 14:00 UTC —</div>`;
    $('#thread-sub').textContent = 'next drop ~14:00 UTC';
    return;
  }

  stage.innerHTML = '';
  $('#thread-sub').textContent = `${tweets.length} tweets · revealed every ${TWEET_REVEAL_MS/1000}s`;

  const revealNext = () => {
    if (threadRevealIdx >= tweets.length) {
      // restart the loop after a pause
      threadRevealTimer && clearInterval(threadRevealTimer);
      setTimeout(() => renderThread(tweets, dateStr), 12_000);
      return;
    }
    const t = tweets[threadRevealIdx];
    const el = document.createElement('div');
    el.className = 'thread-tweet';
    el.style.animationDelay = '0s';
    el.innerHTML = `<span class="tweet-num">${threadRevealIdx + 1}/${tweets.length}</span>${escapeHTML(t)}`;
    stage.appendChild(el);
    // auto-trim to last 6 visible so it doesn't overflow
    while (stage.children.length > 6) stage.removeChild(stage.firstChild);
    threadRevealIdx++;
  };

  revealNext();   // immediate first
  threadRevealTimer = setInterval(revealNext, TWEET_REVEAL_MS);
};

// ── sources list ───────────────────────────────────────────────────
const renderSources = (signals) => {
  const list = $('#sources-list');
  if (!list) return;
  if (!signals || !signals.length) {
    list.innerHTML = '<div class="loading">— no priority signals in last 24h —</div>';
    $('#sources-sub').textContent = '0 items';
    return;
  }
  list.innerHTML = '';
  signals.slice(0, 8).forEach(s => {
    const row = document.createElement('div');
    row.className = 'source-row';
    row.innerHTML = `
      <span class="source-feed">${escapeHTML(s.feed || '?')}</span>
      <span class="source-title">${escapeHTML(s.title || '')}</span>
    `;
    list.appendChild(row);
  });
  $('#sources-sub').textContent = `${signals.length} items consulted`;
};

// ── history (past reports) ─────────────────────────────────────────
const renderHistory = (archive) => {
  const list = $('#history-list');
  if (!list) return;
  // skip today's; show prior reports
  const past = (archive || []).slice(1, 8);
  if (!past.length) {
    list.innerHTML = '<div class="loading">— first day on file —</div>';
    $('#history-sub').textContent = '0';
    return;
  }
  list.innerHTML = '';
  past.forEach(r => {
    const row = document.createElement('div');
    row.className = 'history-row';
    const summary = (r.thread && r.thread[0]) || '';
    row.innerHTML = `
      <div><span class="history-date">${escapeHTML(r.date || '')}</span><span class="history-counts">${r.tweet_count || 0}t · ${(r.signals||[]).length}s</span></div>
      <span class="history-summary">${escapeHTML(summary.slice(0, 160))}${summary.length > 160 ? '…' : ''}</span>
    `;
    list.appendChild(row);
  });
  $('#history-sub').textContent = `${past.length} prior days`;
};

// ── bottom news crawl (uses signals from latest report + monitor alerts) ──
let crawlAlerts = null;
async function refreshCrawl() {
  // pull live alerts.json for the bottom ticker
  crawlAlerts = await fetchJSON('/data/alerts.json');
  renderCrawl();
}
const renderCrawl = () => {
  const track = $('#crawl-track');
  if (!track) return;
  let items = [];
  if (Array.isArray(crawlAlerts)) {
    items = crawlAlerts.slice(0, 12).map(a => `<span class="crawl-item"><span class="crawl-feed">${escapeHTML(a.source_feed || 'PRIOR')}</span>${escapeHTML((a.source_title || a.body || '').slice(0, 100))}</span>`);
  }
  if (!items.length) {
    track.innerHTML = '<span class="crawl-loading">// monitoring · 18 feeds · no insider alerts in last 24h //</span>';
    return;
  }
  // duplicate for seamless loop
  track.innerHTML = items.join('<span class="crawl-sep">·</span>') + '<span class="crawl-sep">·</span>' + items.join('<span class="crawl-sep">·</span>');
};
refreshCrawl();
setInterval(refreshCrawl, CRAWL_REFRESH_MS);

// ── master refresh ─────────────────────────────────────────────────
async function refresh() {
  const archive = await fetchJSON('/data/insider-watch.json');
  if (!archive || !archive.length) {
    $('#report-date').textContent  = new Date().toISOString().slice(0, 10);
    $('#report-status').textContent = 'awaiting first run · 14:00 UTC daily';
    $('#cnt-tweets').textContent  = '—';
    $('#cnt-signals').textContent = '—';
    $('#cnt-alerts').textContent  = '—';
    $('#cnt-archive').textContent = '0';

    // While the first report lands, run the archive spotlight in the
    // thread stage so the page never looks empty.
    const stage = $('#thread-stage');
    if (stage) {
      stage.innerHTML = `
        <div class="thread-tweet" style="opacity:1;transform:none">
          <span class="tweet-num">— archive teaser —</span>
          the daily insider watch fires every day at 14:00 UTC.
          tomorrow's report will land here, animated tweet-by-tweet.
          for now: 65 cycles on file, 162 years archived, the rolodex spotlight is to the right →
        </div>
      `;
    }
    $('#thread-sub').textContent = 'first drop pending';
    renderSources(null);
    renderHistory(null);
    return;
  }
  const today = archive[0];
  $('#report-date').textContent  = today.date || '?';
  $('#report-status').textContent = `report v${archive.length} · streaming`;
  $('#cnt-tweets').textContent  = String(today.tweet_count || 0);
  $('#cnt-signals').textContent = String((today.signals || []).length);
  $('#cnt-alerts').textContent  = String((today.alerts_referenced || []).length);
  $('#cnt-archive').textContent = String(archive.length);

  renderThread(today.thread || [], today.date);
  renderSources(today.signals || []);
  renderHistory(archive);
}

refresh();
setInterval(refresh, REFRESH_MS);
