/* ═══════════════════════════════════════════════════
   $PRIOR — boot sequence, live clock, CA copy, feed
   ═══════════════════════════════════════════════════ */

// Year stamp
document.getElementById('year').textContent = new Date().getFullYear();

// ── STATUS CLOCK + UPTIME ──
(() => {
  const clockEl  = document.getElementById('status-clock');
  const upEl     = document.getElementById('status-uptime');
  const started  = Date.now();
  const pad = n => String(n).padStart(2, '0');
  const tick = () => {
    const now = new Date();
    clockEl.textContent = `${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())} UTC`;
    const diff = Math.floor((Date.now() - started) / 1000);
    const h = Math.floor(diff / 3600);
    const m = Math.floor((diff % 3600) / 60);
    const s = diff % 60;
    upEl.textContent = `${pad(h)}:${pad(m)}:${pad(s)}`;
  };
  tick();
  setInterval(tick, 1000);
})();

// ── BOOT SEQUENCE TYPEWRITER ──
(() => {
  const lines = [
    { text: '> initializing PRIOR.agent ...',       delay: 50 },
    { text: '> loading memory [■■■■■■■■■■] 100%',   delay: 45 },
    { text: '> archives mounted: 7,140,000 tokens', delay: 40 },
    { text: '> voice channel: x.com',               delay: 40 },
    { text: '> status: watching ...',               delay: 60 },
    { text: '',                                      delay: 400 },
    { text: 'prior> hello, outsider.',              delay: 50 },
  ];
  const out = document.getElementById('boot-out');
  if (!out) return;

  let li = 0;
  const typeLine = () => {
    if (li >= lines.length) return;
    const line = lines[li];
    let ci = 0;
    const typer = setInterval(() => {
      out.textContent += line.text[ci] || '';
      ci++;
      if (ci >= line.text.length) {
        clearInterval(typer);
        out.textContent += '\n';
        li++;
        setTimeout(typeLine, line.delay * 3);
      }
    }, line.delay);
  };
  // Delay start for dramatic effect
  setTimeout(typeLine, 400);
})();

// ── BURGER ──
const burger = document.getElementById('burger');
const drawer = document.getElementById('drawer');
if (burger && drawer) {
  burger.addEventListener('click', () => {
    burger.classList.toggle('open');
    drawer.classList.toggle('open');
    document.body.style.overflow = drawer.classList.contains('open') ? 'hidden' : '';
  });
}
function closeMenu() {
  burger.classList.remove('open');
  drawer.classList.remove('open');
  document.body.style.overflow = '';
}
window.closeMenu = closeMenu;

// ── CA COPY ──
function copyCA(textId, btnId, labelId) {
  const el = document.getElementById(textId);
  const btn = document.getElementById(btnId);
  const label = document.getElementById(labelId);
  const ca = (el && el.dataset.ca) || (el && el.textContent.trim()) || '';
  if (!ca) return;

  const write = async () => {
    try { await navigator.clipboard.writeText(ca); }
    catch {
      const ta = document.createElement('textarea');
      ta.value = ca;
      document.body.appendChild(ta);
      ta.select();
      try { document.execCommand('copy'); } catch {}
      document.body.removeChild(ta);
    }
  };
  write().then(() => {
    btn.classList.add('copied');
    label.textContent = ca.startsWith('TBA') ? '[ NOT YET ]' : '[ COPIED ]';
    setTimeout(() => {
      btn.classList.remove('copied');
      label.textContent = '[ COPY ]';
    }, 1800);
  });
}
window.copyCA = copyCA;

// ── PUMP.FUN AUTO-LINK ──
(() => {
  const el = document.getElementById('ca-text');
  if (!el) return;
  const ca = el.dataset.ca;
  if (!ca || ca.startsWith('TBA')) return;
  document.querySelectorAll('a.pumpfun-btn').forEach(link => {
    link.href = 'https://pump.fun/coin/' + ca;
  });
})();

// ── X LINK (optional, once @prior_agent is live) ──
(() => {
  // Replace this with your actual X handle once the bot is live
  const X_HANDLE = 'prior_agent';
  const xLink = document.getElementById('x-link');
  if (xLink) xLink.href = 'https://x.com/' + X_HANDLE;
})();

// ── LIVE-ISH FEED ──
// Attempts to load latest posts from a static JSON file at /data/log.json
// If absent, leaves the hardcoded HTML feed in place.
(async () => {
  const feedEl = document.getElementById('feed');
  if (!feedEl) return;
  try {
    const res = await fetch('/data/log.json', { cache: 'no-store' });
    if (!res.ok) return;
    const data = await res.json();
    if (!Array.isArray(data) || !data.length) return;

    feedEl.innerHTML = '';
    // Latest first, cap at 20
    data.slice(0, 20).forEach((p, i) => {
      const art = document.createElement('article');
      art.className = 'post';
      const id = String(data.length - i).padStart(4, '0');
      art.innerHTML = `
        <header>
          <span class="post-id">#${id}</span>
          <span class="post-time">${p.time || ''}</span>
        </header>
        ${(p.body || '').split('\n\n').map(para => `<p>${escapeHtml(para).replace(/\n/g, '<br/>')}</p>`).join('')}
        <p class="post-sig">— prior</p>
      `;
      feedEl.appendChild(art);
    });
  } catch { /* keep hardcoded */ }
})();

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

// ── ALERT FEED (live monitor) ──
(async () => {
  const feed = document.getElementById('alert-feed');
  if (!feed) return;
  try {
    const [aRes, sRes] = await Promise.all([
      fetch('/data/alerts.json', { cache: 'no-store' }),
      fetch('/data/monitor-public.json', { cache: 'no-store' }),
    ]);

    if (sRes.ok) {
      const s = await sRes.json();
      const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
      if (s.status)         set('monitor-status', s.status);
      if (s.feeds_count)    set('feeds-count', String(s.feeds_count));
      if (s.alerts_count != null) set('alerts-count', String(s.alerts_count));
      if (s.last_check_at) {
        try { set('last-check', new Date(s.last_check_at).toISOString().replace('T',' ').slice(0,16) + ' UTC'); }
        catch { set('last-check', s.last_check_at); }
      }
    }

    if (!aRes.ok) return;
    const alerts = await aRes.json();
    if (!Array.isArray(alerts) || !alerts.length) return;

    feed.innerHTML = '';
    alerts.slice(0, 20).forEach(a => {
      const art = document.createElement('article');
      art.className = 'post post-alert';
      const body = (a.body || '').split('\n').map(line => `<p>${escapeHtml(line)}</p>`).join('');
      const sourceLine = a.source_feed
        ? `<p class="post-source">~ source: ${escapeHtml(a.source_feed)} · <a href="${escapeHtml(a.source_url || '#')}" target="_blank" rel="noopener">${escapeHtml((a.source_title || '').slice(0, 80))}${(a.source_title || '').length > 80 ? '…' : ''}</a></p>`
        : '';
      art.innerHTML = `
        <header>
          <span class="post-id alert-id">${escapeHtml(a.id || 'ALERT')}</span>
          <span class="post-time">${escapeHtml(a.time || '')}</span>
        </header>
        ${body}
        ${sourceLine}
        <p class="post-sig">— prior · informant</p>
      `;
      feed.appendChild(art);
    });
  } catch { /* keep hardcoded */ }
})();
