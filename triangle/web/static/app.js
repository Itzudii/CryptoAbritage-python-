(() => {
  const sel = (q) => document.querySelector(q);
  const fmtTime = (isoOrTs) => {
    try {
      const d = typeof isoOrTs === 'number' ? new Date(isoOrTs * 1000) : new Date(isoOrTs);
      return d.toLocaleString();
    } catch { return String(isoOrTs); }
  };

  const els = {
    mode: sel('#mode'),
    running: sel('#running'),
    iterations: sel('#iterations'),
    oppsFound: sel('#oppsFound'),
    tradesExec: sel('#tradesExec'),
    oppsBody: sel('#oppsBody'),
    tradesBody: sel('#tradesBody'),
    startBtn: sel('#startBtn'),
    stopBtn: sel('#stopBtn'),
    scanBtn: sel('#scanBtn'),
    walletBody: sel('#walletBody'),
    totalUSDT: sel('#totalUSDT'),
    totalProfit: sel('#totalProfit'),
    dailyPNL: sel('#dailyPNL'),
    totalProfit2: sel('#totalProfit2'),
    dataSource: sel('#dataSource'),
    toggleNetBtn: sel('#toggleNetBtn'),
    toggleWsBtn: sel('#toggleWsBtn')
  };

  async function refreshStatus() {
    try {
      const res = await fetch('/api/status');
      const data = await res.json();
      paintStatus(data);
    } catch (e) { /* noop */ }
  }

  // Config badge and toggles
  async function refreshConfigBadge() {
    try {
      const res = await fetch('/api/config');
      const cfg = await res.json();
      const net = cfg.use_testnet ? 'Testnet' : 'Mainnet';
      const ws = cfg.use_websocket ? 'WS' : 'REST';
      if (els.dataSource) {
        els.dataSource.textContent = `${net} • ${ws}`;
        els.dataSource.className = 'pill ' + (cfg.use_testnet ? 'warn' : 'ok');
        els.dataSource.title = `API: ${cfg.api_url}\nWS: ${cfg.ws_url}`;
      }
    } catch {}
  }

  async function setConfig(partial) {
    const qs = new URLSearchParams();
    if (partial.use_testnet !== undefined) qs.set('use_testnet', String(partial.use_testnet));
    if (partial.use_websocket !== undefined) qs.set('use_websocket', String(partial.use_websocket));
    const headers = { };
    // Optional: ask for dashboard API key once if needed
    try {
      const key = window.localStorage.getItem('dash_api_key') || '';
      if (key) headers['X-API-Key'] = key;
    } catch {}
    const res = await fetch('/api/config?' + qs.toString(), { method: 'POST', headers });
    const data = await res.json();
    if (data && data.changed) {
      refreshConfigBadge();
    }
    return data;
  }

  if (els.toggleNetBtn) {
    els.toggleNetBtn.addEventListener('click', async () => {
      const cfg = await (await fetch('/api/config')).json();
      await setConfig({ use_testnet: !cfg.use_testnet });
    });
  }

  if (els.toggleWsBtn) {
    els.toggleWsBtn.addEventListener('click', async () => {
      const cfg = await (await fetch('/api/config')).json();
      await setConfig({ use_websocket: !cfg.use_websocket });
    });
  }

  function paintWallet(data) {
    if (!data) return;
    const { total_value_usdt = 0, balances = [] } = data;
    els.totalUSDT.textContent = Number(total_value_usdt).toFixed(2);
    els.walletBody.innerHTML = balances.map(b => {
      return `<tr><td>${b.asset}</td><td>${Number(b.free).toFixed(8)}</td><td>${Number(b.locked).toFixed(8)}</td><td>${Number(b.value_usdt).toFixed(2)}</td></tr>`;
    }).join('');
  }

  async function refreshWallet() {
    try {
      const res = await fetch('/api/wallet');
      const data = await res.json();
      paintWallet(data);
    } catch {}
  }

  async function refreshProfit() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      els.totalProfit.textContent = Number(data.total_profit || 0).toFixed(2);
    } catch {}
  }

  function paintStatus(s) {
    const running = !!s.running;
    els.running.textContent = String(running);
    els.running.className = 'pill ' + (running ? 'ok' : 'bad');
    els.mode.textContent = s.mode || 'UNKNOWN';
    els.mode.className = 'pill ' + (s.mode === 'DRY_RUN' ? 'warn' : (s.mode === 'LIVE' ? 'ok' : 'bad'));
    els.iterations.textContent = s.iteration_count ?? 0;
    els.oppsFound.textContent = s.opportunities_found ?? 0;
    els.tradesExec.textContent = s.trades_executed ?? 0;
  }

  function paintOpps(list) {
    if (!Array.isArray(list)) return;
    els.oppsBody.innerHTML = list.map(o => {
      const path = (o.triangle?.path || []).join(' -> ');
      const profit = Number(o.profit || 0).toFixed(2);
      const pct = Number(o.profit_percent || 0).toFixed(2);
      const ts = fmtTime(o.timestamp || Date.now());
      return `<tr><td>${ts}</td><td>${path}</td><td>${profit}</td><td>${pct}%</td></tr>`;
    }).join('');
  }

  function paintTrades(list) {
    if (!Array.isArray(list)) return;
    els.tradesBody.innerHTML = list.map(t => {
      const ts = fmtTime(t.timestamp || Date.now());
      const path = t.triangle_path || '';
      const profitNum = Number(t.profit || 0);
      const profit = profitNum.toFixed(2);
      const cls = profitNum >= 0 ? 'pos' : 'neg';
      const status = t.executed ? 'EXECUTED' : 'SKIPPED';
      return `<tr><td>${ts}</td><td>${path}</td><td class="${cls}">${profit}</td><td>${status}</td></tr>`;
    }).join('');
  }

  // Buttons
  els.startBtn.addEventListener('click', async () => {
    await fetch('/api/start?dry_run=true', { method: 'POST' });
    refreshStatus();
  });
  els.stopBtn.addEventListener('click', async () => {
    await fetch('/api/stop', { method: 'POST' });
    refreshStatus();
  });
  els.scanBtn.addEventListener('click', async () => {
    const res = await fetch('/api/scan');
    const data = await res.json();
    if (data && data.ok) {
      paintOpps(data.opportunities || []);
    }
  });

  // WebSocket live feed
  function connectWS() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const ws = new WebSocket(`${proto}://${location.host}/ws/live`);
    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data);
        if (msg.type === 'status') paintStatus(msg.data || {});
        else if (msg.type === 'trades') paintTrades(msg.data || []);
        else if (msg.type === 'opportunities') paintOpps(msg.data || []);
        else if (msg.type === 'scan') paintOpps(msg.data?.opportunities || []);
      } catch {}
    };
    ws.onclose = () => setTimeout(connectWS, 2000);
    ws.onerror = () => ws.close();
  }

  // Initial load
  refreshStatus();
  refreshWallet();
  refreshProfit();
  // PNL fetchers
  async function refreshRisk() {
    try {
      const res = await fetch('/api/risk');
      const data = await res.json();
      const v = Number(data.daily_pnl || 0);
      if (els.dailyPNL) {
        els.dailyPNL.textContent = v.toFixed(2);
        els.dailyPNL.className = v >= 0 ? 'pos' : 'neg';
      }
    } catch {}
  }
  async function refreshTotalProfit2() {
    try {
      const res = await fetch('/api/stats');
      const data = await res.json();
      const v = Number(data.total_profit || 0);
      if (els.totalProfit2) {
        els.totalProfit2.textContent = v.toFixed(2);
        els.totalProfit2.className = v >= 0 ? 'pos' : 'neg';
      }
    } catch {}
  }
  refreshRisk();
  refreshTotalProfit2();
  refreshConfigBadge();
  connectWS();
  // Poll status every 10s as backup
  setInterval(refreshStatus, 10000);
  // Poll wallet and profit every 20s
  setInterval(refreshWallet, 20000);
  setInterval(refreshProfit, 20000);
  setInterval(refreshRisk, 20000);
  setInterval(refreshTotalProfit2, 20000);
})();
