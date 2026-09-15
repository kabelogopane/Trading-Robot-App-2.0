const $ = (id) => document.getElementById(id);
const API_BASE = (window.TRADING_ROBOT_API_URL || "").replace(/\/$/, "");
const api = (path) => `${API_BASE}${path}`;
const statusEl = $("status"), runButton = $("runButton"), tradeBody = $("tradeBody");

function num(v, d = 2) {
  if (v == null || Number.isNaN(Number(v))) return "—";
  return Number(v).toLocaleString(undefined, { minimumFractionDigits: d, maximumFractionDigits: d });
}

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

function renderSummary(s = {}) {
  setText("trades", s.trades ?? "—");
  setText("winRate", s.win_rate_pct == null ? "—" : `${num(s.win_rate_pct)}%`);
  setText("netR", s.net_r == null ? "—" : `${num(s.net_r)}R`);
  setText("drawdown", s.max_drawdown_r == null ? "—" : `${num(s.max_drawdown_r)}R`);
}

function renderTrades(ts = []) {
  if (!tradeBody) return;
  tradeBody.innerHTML = ts.length
    ? ts.map(t => `<tr><td>${t.session_date ?? "—"}</td><td>${t.window ?? "—"}</td><td>${(t.direction ?? "—").toUpperCase()}</td><td>${num(t.entry)}</td><td>${num(t.stop)}</td><td>${num(t.target)}</td><td>${t.outcome ?? "—"}</td><td>${t.r_multiple == null ? "—" : num(t.r_multiple) + "R"}</td></tr>`).join("")
    : '<tr><td colspan="8">No qualifying paper trades found.</td></tr>';
}

function renderState(s = {}) {
  setText("anchorHigh", num(s.reference_high));
  setText("anchorLow", num(s.reference_low));
  setText("anchorState", s.anchor || "Waiting");
  setText("referenceState", s.reference_high != null ? "Captured" : "Waiting");
  setText("direction", (s.direction || "neutral").toUpperCase());
  setText("liquidity", s.sweep_type || "Monitoring");
  setText("displacement", s.status === "qualified" ? "Confirmed" : "Waiting");
  setText("structure", s.direction ? s.direction.toUpperCase() : "Neutral");
  setText("qualification", s.status === "qualified" ? `QUALIFIED · ${s.sweep_type || "reaction"}` : s.reason || "Waiting for confirmation");
  setText("windowState", s.confirmation_time ? new Date(s.confirmation_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Monitoring");
}

async function runBacktest() {
  if (!runButton) return;
  runButton.disabled = true;
  runButton.textContent = "Running…";
  setText("modelState", "RUNNING");
  try {
    const rr = Number($("rr")?.value) || 2;
    const risk = Number($("risk")?.value) || 1;
    const r = await fetch(api(`/api/backtest?risk_percent=${encodeURIComponent(risk)}&risk_reward=${encodeURIComponent(rr)}`));
    if (!r.ok) throw Error(`Backtest failed (HTTP ${r.status})`);
    const d = await r.json();
    renderSummary(d.summary);
    renderTrades(d.trades);
    drawChart(d.bars || []);
    const stateResponse = await fetch(api("/api/execution-state"));
    if (!stateResponse.ok) throw Error(`Execution state failed (HTTP ${stateResponse.status})`);
    renderState(await stateResponse.json());
    setText("dataSource", "US500.F · 3M PAPER DATA");
    setText("chartMode", "45M + 3M");
    setText("modelState", "READY");
    statusEl.innerHTML = "<i></i> System online · paper mode";
  } catch (e) {
    setText("modelState", "ERROR");
    statusEl.innerHTML = "<i></i> Backend unavailable";
    if (tradeBody) tradeBody.innerHTML = `<tr><td colspan="8">${e.message}. Start the FastAPI backend or configure the deployed API URL.</td></tr>`;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run paper backtest";
  }
}

async function checkHealth() {
  try {
    const r = await fetch(api("/api/health"));
    const d = await r.json();
    statusEl.innerHTML = r.ok && d.status === "ok" ? "<i></i> System online · paper mode" : "<i></i> System unavailable";
  } catch (e) {
    statusEl.innerHTML = "<i></i> Backend unavailable";
  }
}

function drawChart(bars = []) {
  const c = $("priceChart");
  if (!c) return;
  const rect = c.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  c.width = rect.width * dpr;
  c.height = rect.height * dpr;
  const xctx = c.getContext("2d");
  xctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = rect.width, h = rect.height, p = 25;
  xctx.clearRect(0, 0, w, h);
  if (!bars.length) return;
  const vals = bars.map(b => +b.close).filter(Number.isFinite);
  if (!vals.length) return;
  const min = Math.min(...vals), max = Math.max(...vals);
  const x = i => p + i / Math.max(vals.length - 1, 1) * (w - p * 2);
  const y = v => h - p - (v - min) / Math.max(max - min, 1) * (h - p * 2);
  xctx.strokeStyle = "#1d2b40";
  xctx.lineWidth = 1;
  for (let i = 1; i < 5; i++) {
    const yy = p + i * (h - p * 2) / 5;
    xctx.beginPath(); xctx.moveTo(p, yy); xctx.lineTo(w - p, yy); xctx.stroke();
  }
  xctx.strokeStyle = "#5e9bff";
  xctx.lineWidth = 2;
  xctx.beginPath();
  vals.forEach((v, i) => i ? xctx.lineTo(x(i), y(v)) : xctx.moveTo(x(i), y(v)));
  xctx.stroke();
  const anchorIndex = bars.findIndex(b => {
    const t = new Date(b.timestamp);
    return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(t) === "09:45";
  });
  if (anchorIndex >= 0) {
    xctx.setLineDash([5, 5]);
    xctx.strokeStyle = "#e0ad4f";
    xctx.beginPath(); xctx.moveTo(x(anchorIndex), p); xctx.lineTo(x(anchorIndex), h - p); xctx.stroke();
    xctx.setLineDash([]);
    xctx.fillStyle = "#7488a5";
    xctx.font = "10px system-ui";
    xctx.fillText("09:45 MAIN", Math.min(x(anchorIndex) + 6, w - 80), p + 12);
  }
}

if (runButton) runButton.addEventListener("click", runBacktest);
window.addEventListener("resize", () => drawChart([]));
setInterval(() => {
  setText("clock", new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false }).format(new Date()));
}, 1000);
if ("serviceWorker" in navigator) window.addEventListener("load", () => navigator.serviceWorker.register("./service-worker.js").catch(() => {}));
checkHealth();
