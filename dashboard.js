/* PRIOR · ops dashboard
   pulls live data from data/*.json + GitHub Actions API
   auto-refreshes every 60s
*/

const REPO = 'mobfoesteelo/prior-site';
const REFRESH_MS = 60_000;

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
  if (!when) return 'never';
  const t = new Date(when).getTime();
  if (isNaN(t)) return 'unknown';
  const diff = Date.now() - t;
  if (diff < 0)               return 'in future';
  if (diff < 60_000)          return Math.floor(diff/1000) + 's ago';
  if (diff < 3_600_000)       return Math.floor(diff/60_000) + 'm ago';
  if (diff < 86_400_000)      return Math.floor(diff/3_600_000) + 'h ago';
  return Math.floor(diff/86_400_000) + 'd ago';
};

const parseTime = (s) => {
  // accepts "2026-04-26 13:00 UTC" or ISO
  if (!s) return null;
  if (typeof s === 'number') return new Date(s);
  const iso = s.replace(' UTC', 'Z').replace(' ', 'T');
  const d = new Date(iso);
  return isNaN(d) ? null : d;
};

const todayUTC = () => {
  const d = new Date();
  return d.toISOString().slice(0, 10);
};

const countToday = (entries, timeKey = 'time') => {
  if (!Array.isArray(entries)) return 0;
  const today = todayUTC();
  return entries.filter(e => {
    const t = parseTime(e[timeKey]);
    return t && t.toISOString().slice(0, 10) === today;
  }).length;
};

// ── header clock ───────────────────────────────────────────────────
const updateClock = () => {
  const now = new Date();
  const t = now.toISOString().slice(11, 19) + ' UTC';
  const d = now.toISOString().slice(0, 10);
  $('#dash-time').textContent = `${d} ${t}`;
};
setInterval(updateClock, 1000);
updateClock();

// ── engine status ──────────────────────────────────────────────────
const ENGINES = [
  { id: 'agent',     name: 'prior.agent',     cap: 6,  workflow: 'prior-bot.yml',       cron: 'every 4h · :17',    paused: false },
  { id: 'memes',     name: 'prior.memes',     cap: 3,  workflow: 'prior-memes.yml',     cron: 'every 8h · :42',    paused: false },
  { id: 'monitor',   name: 'prior.monitor',   cap: 4,  workflow: 'prior-monitor.yml',   cron: 'every 15m',         paused: false },
  { id: 'replies',   name: 'prior.replies',   cap: 8,  workflow: 'prior-replies.yml',   cron: 'every 30m',         paused: true },
  { id: 'backrooms', name: 'prior.backrooms', cap: 1,  workflow: 'prior-backrooms.yml', cron: 'daily · 03:11 UTC', paused: false },
];

const renderEngines = (data) => {
  const grid = $('#engine-grid');
  grid.innerHTML = '';
  ENGINES.forEach(eng => {
    const card = el('div', 'engine-card');
    const status = data[eng.id].status;       // paused | live | blocked | ok
    const last   = data[eng.id].lastWhen;
    const today  = data[eng.id].today ?? 0;
    const note   = data[eng.id].note ?? '';

    card.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <span class="engine-name">${eng.name}</span>
        <span class="engine-status ${status}">${status}</span>
      </div>
      <div class="engine-meta">
        cron · ${escapeHTML(eng.cron)}<br>
        last · <b>${ago(last)}</b><br>
        today · <b>${today}/${eng.cap}</b>${note ? '<br>' + escapeHTML(note) : ''}
      </div>
    `;
    grid.appendChild(card);
  });
  $('#engines-sub').textContent = `4 engines · all paused (X verification)`;
};

// ── posts ──────────────────────────────────────────────────────────
const renderPosts = (log) => {
  const list = $('#posts-list');
  if (!log || !log.length) {
    list.innerHTML = '<div class="dash-loading">no posts yet — first run pending</div>';
    $('#posts-sub').textContent = '0 posts';
    return;
  }
  list.innerHTML = '';
  log.slice(0, 10).forEach(e => {
    const item = el('div', 'dash-item');
    const linkHTML = e.url
      ? `<div class="dash-item-meta"><a href="${escapeHTML(e.url)}" target="_blank" rel="noopener">view on x ↗</a></div>`
      : `<div class="dash-item-meta">— dry run · not posted —</div>`;
    const imgHTML = e.image
      ? `<div class="dash-item-img"><img src="${escapeHTML(e.image)}" alt="meme" loading="lazy"></div>`
      : '';
    const typeBadge = e.type === 'meme' ? '<span class="dash-tag">meme</span> ' : '';
    item.innerHTML = `
      <span class="dash-item-time">${typeBadge}${escapeHTML(e.time || '')}</span>
      ${imgHTML}
      <div class="dash-item-body">${escapeHTML(e.body || '')}</div>
      ${linkHTML}
    `;
    list.appendChild(item);
  });
  $('#posts-sub').textContent = `${log.length} total · today ${countToday(log)}`;
};

// ── alerts ─────────────────────────────────────────────────────────
const renderAlerts = (alerts) => {
  const list = $('#alerts-list');
  if (!alerts || !alerts.length) {
    list.innerHTML = '<div class="dash-loading">no alerts yet — monitor awaiting first trigger</div>';
    $('#alerts-sub').textContent = '0 alerts';
    return;
  }
  list.innerHTML = '';
  alerts.slice(0, 10).forEach(a => {
    const item = el('div', 'dash-item');
    item.innerHTML = `
      <span class="dash-item-time">${escapeHTML(a.time || '')} · ${escapeHTML(a.id || '')}</span>
      <div class="dash-item-body">${escapeHTML(a.body || '')}</div>
      <div class="dash-item-quote">trigger: ${escapeHTML(a.trigger || '?')} · source: ${a.source_url ? `<a href="${escapeHTML(a.source_url)}" target="_blank" rel="noopener">${escapeHTML(a.source || 'link')}</a>` : escapeHTML(a.source || '?')}</div>
    `;
    list.appendChild(item);
  });
  $('#alerts-sub').textContent = `${alerts.length} total · today ${countToday(alerts)}`;
};

// ── replies ────────────────────────────────────────────────────────
const renderReplies = (replies) => {
  const list = $('#replies-list');
  if (!replies || !replies.length) {
    list.innerHTML = '<div class="dash-loading">no replies yet — awaiting first worthy mention</div>';
    $('#replies-sub').textContent = '0 replies · live every 15m';
    return;
  }
  list.innerHTML = '';
  replies.slice(0, 10).forEach(r => {
    const item = el('div', 'dash-item');
    item.innerHTML = `
      <span class="dash-item-time">${escapeHTML(r.time || '')} · → @${escapeHTML(r.to_user || '?')}</span>
      <div class="dash-item-body">${escapeHTML(r.body || '')}</div>
      <div class="dash-item-quote">re: ${escapeHTML((r.to_text || '').slice(0, 140))}${(r.to_text || '').length > 140 ? '…' : ''}</div>
      ${r.tweet_url ? `<div class="dash-item-meta"><a href="${escapeHTML(r.tweet_url)}" target="_blank" rel="noopener">view on x ↗</a></div>` : ''}
    `;
    list.appendChild(item);
  });
  $('#replies-sub').textContent = `${replies.length} total · today ${countToday(replies)}`;
};

// ── backrooms ──────────────────────────────────────────────────────
const renderBackrooms = (rooms) => {
  const list = $('#backrooms-list');
  if (!rooms || !rooms.length) {
    list.innerHTML = '<div class="dash-loading">no archives yet</div>';
    $('#backrooms-sub').textContent = '0 archives';
    return;
  }
  list.innerHTML = '';
  rooms.slice(0, 6).forEach(r => {
    const item = el('div', 'dash-item');
    const msgs = r.messages || r.turns || [];
    const firstMsg = msgs[0] || {};
    const firstText = firstMsg.text || firstMsg.body || '';
    const isLive = r.trigger?.type === 'insider_alert' || (r.id || '').startsWith('br-live');
    const isHistorical = (r.id || '').startsWith('br-h');
    const tag = isLive ? '<span class="dash-tag" style="background:var(--red);color:white">live</span> '
              : isHistorical ? '<span class="dash-tag" style="background:var(--phos-dim)">archive</span> '
              : '';
    item.innerHTML = `
      <span class="dash-item-time">${tag}${escapeHTML(r.date || '')} · ${escapeHTML(r.title || '')} · ${msgs.length} msgs</span>
      <div class="dash-item-body">${escapeHTML((firstText || '').slice(0, 220))}${firstText.length > 220 ? '…' : ''}</div>
      <div class="dash-item-meta"><a href="/backrooms.html#${escapeHTML(r.id || r.date || '')}">read full archive →</a></div>
    `;
    list.appendChild(item);
  });
  const liveCount  = rooms.filter(r => r.trigger?.type === 'insider_alert' || (r.id||'').startsWith('br-live')).length;
  const histCount  = rooms.filter(r => (r.id||'').startsWith('br-h')).length;
  $('#backrooms-sub').textContent = `${rooms.length} total · ${histCount} archive · ${liveCount} live`;
};

// ── monitor health ─────────────────────────────────────────────────
const renderMonitor = (m) => {
  const kv = $('#monitor-kv');
  if (!m) {
    kv.innerHTML = '<div class="dash-loading">monitor data unavailable</div>';
    return;
  }
  const last = m.last_check_at ? ago(m.last_check_at) : 'never';
  const lastCls = m.last_check_at ? 'ok' : 'warn';
  kv.innerHTML = `
    <div class="dash-kv-row"><span class="dash-kv-key">status</span><span class="dash-kv-val ${m.last_check_at ? 'ok' : 'warn'}">${escapeHTML(m.status || 'unknown')}</span></div>
    <div class="dash-kv-row"><span class="dash-kv-key">last poll</span><span class="dash-kv-val ${lastCls}">${last}</span></div>
    <div class="dash-kv-row"><span class="dash-kv-key">feeds</span><span class="dash-kv-val">${m.feeds_count ?? '?'}</span></div>
    <div class="dash-kv-row"><span class="dash-kv-key">alerts fired</span><span class="dash-kv-val">${m.alerts_count ?? 0}</span></div>
  `;
  $('#monitor-sub').textContent = m.last_check_at ? `last poll ${last}` : 'awaiting first run';
};

// ── github actions ─────────────────────────────────────────────────
const renderGH = (runs) => {
  const tbl = $('#gh-runs');
  if (!runs || !runs.length) {
    tbl.innerHTML = '<div class="dash-loading">github api unreachable (rate limit?)</div>';
    return;
  }
  tbl.innerHTML = '';
  // header
  const head = el('div', 'gh-row gh-row-head');
  head.innerHTML = `
    <span>workflow</span>
    <span>started</span>
    <span class="gh-hide-mobile">trigger</span>
    <span class="gh-hide-mobile">duration</span>
    <span>status</span>
    <span style="text-align:right">action</span>
  `;
  tbl.appendChild(head);

  runs.slice(0, 15).forEach(r => {
    const row = el('div', 'gh-row');
    const dur = r.run_started_at && r.updated_at
      ? Math.round((new Date(r.updated_at) - new Date(r.run_started_at)) / 1000) + 's'
      : '—';
    const concl = r.conclusion || r.status || '—';
    const cls = `gh-status-${concl.replace(/[^a-z_]/g, '')}`;
    row.innerHTML = `
      <span>${escapeHTML(r.name || '?')}</span>
      <span>${escapeHTML(ago(r.run_started_at))}</span>
      <span class="gh-hide-mobile">${escapeHTML(r.event || '')}</span>
      <span class="gh-hide-mobile">${dur}</span>
      <span class="${cls}">${escapeHTML(concl)}</span>
      <span style="text-align:right"><a href="${escapeHTML(r.html_url)}" target="_blank" rel="noopener">log ↗</a></span>
    `;
    tbl.appendChild(row);
  });
  $('#gh-sub').textContent = `${runs.length} fetched · public api`;
};

// ── budget ─────────────────────────────────────────────────────────
const renderBudget = (counts) => {
  const grid = $('#budget-grid');
  grid.innerHTML = '';
  const total = counts.posts + counts.memes + counts.alerts + counts.replies;
  const items = [
    { name: 'autonomous posts', count: counts.posts,   cap: 6 },
    { name: 'memes',            count: counts.memes,   cap: 3 },
    { name: 'monitor alerts',   count: counts.alerts,  cap: 4 },
    { name: 'replies',          count: counts.replies, cap: 8 },
    { name: 'total today',      count: total,          cap: 17 },
  ];
  items.forEach(it => {
    const pct = Math.min(100, (it.count / it.cap) * 100);
    const fillCls = pct >= 100 ? 'full' : pct >= 75 ? 'warn' : '';
    const card = el('div', 'budget-card');
    card.innerHTML = `
      <div class="budget-name">${escapeHTML(it.name)}</div>
      <div><span class="budget-count">${it.count}</span><span class="budget-cap"> / ${it.cap}</span></div>
      <div class="budget-bar"><div class="budget-bar-fill ${fillCls}" style="width:${pct}%"></div></div>
    `;
    grid.appendChild(card);
  });
};

// ── master refresh ─────────────────────────────────────────────────
async function refresh() {
  const [log, alerts, replies, rooms, monitor, ghData] = await Promise.all([
    fetchJSON('/data/log.json'),
    fetchJSON('/data/alerts.json'),
    fetchJSON('/data/replies.json'),
    fetchJSON('/data/backrooms.json'),
    fetchJSON('/data/monitor-public.json'),
    fetchJSON(`https://api.github.com/repos/${REPO}/actions/runs?per_page=20`),
  ]);

  const ghRuns = ghData?.workflow_runs || [];
  const runsByWorkflow = {};
  ENGINES.forEach(e => {
    runsByWorkflow[e.id] = ghRuns
      .filter(r => r.path && r.path.endsWith(e.workflow))
      .sort((a, b) => new Date(b.run_started_at) - new Date(a.run_started_at));
  });

  // Engine status synthesis
  const engineData = {};
  ENGINES.forEach(e => {
    const runs = runsByWorkflow[e.id] || [];
    const last = runs[0];
    let status = 'paused';
    let note = '';
    if (e.id === 'replies' && last && last.conclusion === 'failure') {
      status = 'blocked';
      note = 'X auth (verification pending)';
    }
    engineData[e.id] = {
      status,
      lastWhen: last?.run_started_at,
      today: runs.filter(r => {
        const t = new Date(r.run_started_at);
        return !isNaN(t) && t.toISOString().slice(0, 10) === todayUTC();
      }).length,
      note,
    };
  });

  // Override "today" counts with actual data-based counts where available
  const memeCount = (log || []).filter(e => e.type === 'meme').length;
  const memeToday = countToday((log || []).filter(e => e.type === 'meme'));
  const textPosts = (log || []).filter(e => e.type !== 'meme');
  engineData.agent.today     = countToday(textPosts);
  engineData.memes.today     = memeToday;
  engineData.monitor.today   = countToday(alerts);
  engineData.replies.today   = countToday(replies);
  engineData.backrooms.today = countToday(rooms || [], 'date');

  renderEngines(engineData);
  renderPosts(log);
  renderAlerts(alerts);
  renderReplies(replies);
  renderBackrooms(rooms);
  renderMonitor(monitor);
  renderGH(ghRuns);
  renderBudget({
    posts:   engineData.agent.today,
    memes:   engineData.memes.today,
    alerts:  engineData.monitor.today,
    replies: engineData.replies.today,
  });
}

refresh();
setInterval(refresh, REFRESH_MS);
