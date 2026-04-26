/* PRIOR · LIVE · streamer-optimized control room
 *
 * Pulls from the same data sources as the dashboard (data/log.json,
 * data/alerts.json, data/monitor-public.json, data/replies.json,
 * data/backrooms.json) plus uses public GitHub Actions API for runs.
 *
 * Designed to be visually busy — multiple animations running simultaneously
 * so an OBS stream of this page never looks frozen.
 */

const REPO = 'mobfoesteelo/prior-site';
const REFRESH_MS = 30_000;       // pull data every 30s
const NOW_TYPE_MS = 22;          // typewriter speed (ms per char)
const NOW_HOLD_MS = 11_000;      // dwell on each "now posting" before rotating

// ── helpers ────────────────────────────────────────────────────────
const $  = (sel) => document.querySelector(sel);
const el = (tag, cls, html) => {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};
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

const ago = (when) => {
  if (!when) return '?';
  const t = (typeof when === 'number') ? when : new Date(when).getTime();
  if (isNaN(t)) return '?';
  const diff = Date.now() - t;
  if (diff < 0)             return 'queued';
  if (diff < 60_000)        return Math.floor(diff/1000) + 's';
  if (diff < 3_600_000)     return Math.floor(diff/60_000) + 'm';
  if (diff < 86_400_000)    return Math.floor(diff/3_600_000) + 'h';
  return Math.floor(diff/86_400_000) + 'd';
};

const parseTime = (s) => {
  if (!s) return null;
  if (typeof s === 'number') return new Date(s);
  const iso = s.replace(' UTC', 'Z').replace(' ', 'T');
  const d = new Date(iso);
  return isNaN(d) ? null : d;
};

const todayUTC = () => new Date().toISOString().slice(0, 10);

const countToday = (entries, key = 'time') => {
  if (!Array.isArray(entries)) return 0;
  const today = todayUTC();
  return entries.filter(e => {
    const t = parseTime(e[key]);
    return t && t.toISOString().slice(0, 10) === today;
  }).length;
};

// ── REC clock (ticks every second) ─────────────────────────────────
const tickClock = () => {
  const now = new Date();
  const t = now.toISOString().slice(11, 19);
  const d = now.toISOString().slice(0, 10);
  $('#rec-clock').textContent = `${d} ${t} UTC`;
};
setInterval(tickClock, 1000);
tickClock();

// ── CYCLE TICKER (vertical autoscroll) ─────────────────────────────
const CYCLES = [
  ['1862', "lincoln's greenbacks"],
  ['1910', 'jekyll island · the secret six'],
  ['1913', 'federal reserve act'],
  ['1929', 'black tuesday · -89%'],
  ['1932', 'tuskegee begins'],
  ['1953', 'mk-ultra · 149 sub-projects'],
  ['1956', 'cointelpro'],
  ['1961', 'eisenhower names the MIC'],
  ['1962', 'operation northwoods'],
  ['1964', 'gulf of tonkin'],
  ['1971', 'gold window closes'],
  ['1985', 'iran-contra · 0 served'],
  ['1986', 'boesky · $100M fine'],
  ['1987', 'black monday · -22.6%'],
  ['1989', 'milken · 22 months'],
  ['1991', 'BCCI · bank of crooks'],
  ['1996', 'oxycontin launches'],
  ['1999', 'glass-steagall repealed'],
  ['2001', 'enron · grandma millie'],
  ['2003', 'iraq · halliburton'],
  ['2008', 'lehman · too big to jail'],
  ['2008', 'epstein NPA · acosta'],
  ['2008', 'madoff · SEC missed 5x'],
  ['2009', 'the genesis block'],
  ['2011', 'galleon · gupta · 23 sec'],
  ['2012', 'LIBOR · $350T notional'],
  ['2013', 'SAC · cohen · point72'],
  ['2014', 'mt. gox · 850k BTC'],
  ['2016', 'panama papers'],
  ['2016', 'wells fargo · 3.5M accounts'],
  ['2019', 'epstein cell · cameras off'],
  ['2020', 'burr · loeffler · feinstein'],
  ['2020', 'PPP · $742B forgiven'],
  ['2021', 'gamestop · jan 28'],
  ['2021', 'kaplan · rosengren · clarida'],
  ['2022', 'wahi · first crypto insider'],
  ['2022', 'FTX · the back door'],
  ['2023', 'SVB · signature · CS'],
  ['2024', 'epstein files unsealed'],
  ['2024', 'pelosi nvidia $5M pre-CHIPS'],
  ['2025', 'TRUMP · MELANIA · 813,294'],
  ['2025', 'LIBRA · milei · -95%'],
  ['2026', 'oil futures · 47 min before'],
  ['2026', 'polymarket · maduro 3d early'],
];

const renderCycleTicker = () => {
  const container = $('#cycle-ticker');
  // duplicate the list so the loop animation feels seamless
  const html = [...CYCLES, ...CYCLES].map(([yr, txt]) =>
    `<div class="cycle-line"><span class="cycle-yr">${yr}</span><span class="cycle-arrow">→</span>${escapeHTML(txt)}</div>`
  ).join('');
  container.innerHTML = `<div class="cycle-ticker-inner">${html}</div>`;
};
renderCycleTicker();

// ── ARCHIVE CRAWL (horizontal bottom ticker) ───────────────────────
const renderCrawl = () => {
  const track = $('#crawl-track');
  const items = CYCLES.map(([yr, txt]) =>
    `<span class="crawl-item"><span class="crawl-yr">${yr}</span>${escapeHTML(txt)}</span>`
  ).join('<span class="crawl-sep"> · </span>');
  // duplicate for seamless loop
  track.innerHTML = items + '<span class="crawl-sep"> · </span>' + items;
};
renderCrawl();

// ── ENGINE STRIP ───────────────────────────────────────────────────
const ENGINES = [
  { id: 'agent',     name: 'prior.agent',     workflow: 'prior-bot.yml',       cron: 'every 4h · :17' },
  { id: 'memes',     name: 'prior.memes',     workflow: 'prior-memes.yml',     cron: 'every 8h · :42' },
  { id: 'monitor',   name: 'prior.monitor',   workflow: 'prior-monitor.yml',   cron: 'every 15m'      },
  { id: 'replies',   name: 'prior.replies',   workflow: 'prior-replies.yml',   cron: 'every 15m'      },
  { id: 'backrooms', name: 'prior.backrooms', workflow: 'prior-backrooms.yml', cron: '4×/day · :11'   },
];

const renderEngines = (runsByWorkflow) => {
  const strip = $('#engine-strip');
  strip.innerHTML = '';
  let liveCount = 0;
  ENGINES.forEach(e => {
    const runs = runsByWorkflow[e.id] || [];
    const last = runs[0];
    let statusCls = 'live';
    if (last && last.conclusion === 'failure') {
      statusCls = 'blocked';
    } else if (last) {
      liveCount++;
    } else {
      // No runs yet but schedule armed
      liveCount++;
    }
    const lastWhen = last ? ago(last.run_started_at) + ' ago' : '—';
    const row = el('div', `engine-row ${statusCls}`);
    row.innerHTML = `
      <span class="engine-dot"></span>
      <span class="engine-name">${escapeHTML(e.name)}</span>
      <span class="engine-cron">${escapeHTML(e.cron)} · ${lastWhen}</span>
    `;
    strip.appendChild(row);
  });
  $('#engines-sub').textContent = `${liveCount}/${ENGINES.length} LIVE`;
};

// ── BUDGET BARS ─────────────────────────────────────────────────────
const renderBudget = (counts) => {
  const list = $('#budget-list');
  list.innerHTML = '';
  const total = counts.posts + counts.memes + counts.alerts + counts.replies;
  const items = [
    { name: 'autonomous posts', count: counts.posts,  cap: 6  },
    { name: 'memes',            count: counts.memes,  cap: 3  },
    { name: 'monitor alerts',   count: counts.alerts, cap: 4  },
    { name: 'replies',          count: counts.replies, cap: 12 },
    { name: 'TOTAL',            count: total,         cap: 17 },
  ];
  items.forEach(it => {
    const pct = Math.min(100, (it.count / it.cap) * 100);
    const fillCls = pct >= 100 ? 'full' : pct >= 75 ? 'warn' : '';
    const row = el('div', 'budget-row');
    row.innerHTML = `
      <div class="budget-row-head">
        <span class="budget-name">${escapeHTML(it.name)}</span>
        <span class="budget-count">${it.count}/${it.cap}</span>
      </div>
      <div class="budget-bar"><div class="budget-bar-fill ${fillCls}" style="width:${pct}%"></div></div>
    `;
    list.appendChild(row);
  });
};

// ── ACTIVITY FEED (merge posts + alerts + replies) ─────────────────
const buildActivityList = (log, alerts, replies) => {
  const items = [];
  (log || []).slice(0, 12).forEach(p => {
    items.push({
      kind: p.type === 'meme' ? 'meme' : (p.type === 'thread' ? 'thread' : 'post'),
      time: parseTime(p.time),
      time_str: p.time || '',
      body: p.body || '',
    });
  });
  (alerts || []).slice(0, 6).forEach(a => {
    items.push({
      kind: 'alert',
      time: parseTime(a.time),
      time_str: a.time || '',
      body: a.body || '',
    });
  });
  (replies || []).slice(0, 6).forEach(r => {
    items.push({
      kind: 'reply',
      time: parseTime(r.time),
      time_str: r.time || '',
      body: `→ @${r.to_user || '?'} :: ${r.body || ''}`,
    });
  });
  // sort newest first
  items.sort((a, b) => (b.time?.getTime() || 0) - (a.time?.getTime() || 0));
  return items.slice(0, 10);
};

const renderActivity = (items) => {
  const feed = $('#activity-feed');
  if (!items.length) {
    feed.innerHTML = '<div class="loading">— no activity yet —</div>';
    return;
  }
  feed.innerHTML = '';
  items.forEach(it => {
    const item = el('div', `activity-item activity-${it.kind}`);
    const tagCls = `tag-${it.kind}`;
    const ageStr = it.time ? ago(it.time.getTime()) + ' ago' : '';
    item.innerHTML = `
      <div class="activity-meta">
        <span class="activity-tag ${tagCls}">${it.kind}</span>
        ${ageStr}
      </div>
      <div class="activity-body">${escapeHTML(it.body.slice(0, 200))}${it.body.length > 200 ? '…' : ''}</div>
    `;
    feed.appendChild(item);
  });
};

// ── NOW POSTING (rotates through latest posts with typewriter effect) ──
let nowQueue = [];
let nowIndex = 0;
let nowTimer = null;
let nowTypeTimer = null;

const renderNowPosting = (log) => {
  // queue = filter out memes (they have images we can't show in this panel)
  // and replies (those are elsewhere). Just autonomous posts + threads.
  nowQueue = (log || []).filter(p => !p.type || p.type === 'thread').slice(0, 8);
  if (!nowQueue.length) {
    $('#now-body').innerHTML = '<span class="now-cursor">▮</span>';
    $('#now-time').textContent = 'awaiting first post...';
    $('#now-meta').textContent = '— empty —';
    return;
  }
  // restart the carousel
  nowIndex = 0;
  cycleNow();
};

const cycleNow = () => {
  if (!nowQueue.length) return;
  if (nowTimer) clearTimeout(nowTimer);
  if (nowTypeTimer) clearInterval(nowTypeTimer);

  const post = nowQueue[nowIndex % nowQueue.length];
  $('#now-time').textContent = post.time || '';
  $('#now-meta').textContent = `${nowIndex + 1} / ${nowQueue.length}`;
  const body = $('#now-body');
  body.innerHTML = '';

  // typewriter
  const text = post.body || '';
  let i = 0;
  const cursor = '<span class="now-cursor">▮</span>';
  nowTypeTimer = setInterval(() => {
    if (i >= text.length) {
      clearInterval(nowTypeTimer);
      body.innerHTML = escapeHTML(text) + cursor;
      // schedule next post after dwell
      nowTimer = setTimeout(() => {
        nowIndex++;
        cycleNow();
      }, NOW_HOLD_MS);
      return;
    }
    i++;
    body.innerHTML = escapeHTML(text.slice(0, i)) + cursor;
  }, NOW_TYPE_MS);
};

// ── MASTER REFRESH ─────────────────────────────────────────────────
async function refresh() {
  const [log, alerts, replies, ghData] = await Promise.all([
    fetchJSON('/data/log.json'),
    fetchJSON('/data/alerts.json'),
    fetchJSON('/data/replies.json'),
    fetchJSON(`https://api.github.com/repos/${REPO}/actions/runs?per_page=20`),
  ]);

  const ghRuns = ghData?.workflow_runs || [];
  const runsByWorkflow = {};
  ENGINES.forEach(e => {
    runsByWorkflow[e.id] = ghRuns
      .filter(r => r.path && r.path.endsWith(e.workflow))
      .sort((a, b) => new Date(b.run_started_at) - new Date(a.run_started_at));
  });

  renderEngines(runsByWorkflow);

  const memeCount = (log || []).filter(e => e.type === 'meme').length;
  const memeToday = countToday((log || []).filter(e => e.type === 'meme'));
  const textPosts = (log || []).filter(e => e.type !== 'meme');
  renderBudget({
    posts:   countToday(textPosts),
    memes:   memeToday,
    alerts:  countToday(alerts || []),
    replies: countToday(replies || []),
  });

  renderActivity(buildActivityList(log, alerts, replies));
  renderNowPosting(log);
}

refresh();
setInterval(refresh, REFRESH_MS);
