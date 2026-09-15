const API = window.TRADING_ROBOT_API || "https://trading-robot-app-2.onrender.com";
const $ = (id) => document.getElementById(id);

function num(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function setText(id, value) {
  const el = $(id);
  if (el) el.textContent = value;
}

function renderSummary(summary = {}) {
  setText("trades", summary.trades ?? "—");
  setText("win", summary.win_rate_pct == null ? "—" : `${num(summary.win_rate_pct)}%`);
  setText("net", summary.net_r == null ? "—" : `${num(summary.net_r)}R`);
  setText("dd", summary.max_drawdown_r == null ? "—" : `${num(summary.max_drawdown_r)}R`);
}

function renderTrades(trades = []) {
  const body = $("body");
  if (!body) return;
  if (!trades.length) {
    body.innerHTML = '<tr><td colspan="8" class="empty">No qualifying paper trades found.</td></tr>';
    return;
  }
  body.innerHTML = trades.map((trade) => `
    <tr>
      <td>${trade.session_date ?? "—"}</td>
      <td>${trade.window ?? "—"}</td>
      <td>${(trade.direction ?? "—").toUpperCase()}</td>
      <td>${num(trade.entry)}</td>
      <td>${num(trade.stop)}</td>
      <td>${num(trade.target)}</td>
      <td>${trade.outcome ?? "—"}</td>
      <td>${trade.r_multiple == null ? "—" : `${num(trade.r_multiple)}R`}</td>
    </tr>
  `).join("");
}

function renderExecutionState(state = {}) {
  setText("ah", num(state.reference_high));
  setText("al", num(state.reference_low));
  setText("direction", (state.direction || "neutral").toUpperCase());
  setText("liq", state.sweep_type ? state.sweep_type.replaceAll("_", " ").toUpperCase() : "WAITING");
  setText("disp", state.status === "qualified" ? "CONFIRMED" : "WAITING");
  setText("struct", state.status === "qualified" ? (state.direction || "neutral").toUpperCase() : "NEUTRAL");
  setText("entry", state.entry == null ? "—" : num(state.entry));
  setText("stop", state.invalidation == null ? "—" : num(state.invalidation));
  setText("target", state.target == null ? "—" : num(state.target));
  setText("qual", state.status === "qualified" ? `QUALIFIED · ${state.sweep_type || "reaction"}` : (state.reason || "Waiting for objective confirmation"));
}

function parseTime(value) {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? null : d;
}

function renderChart(bars = [], state = {}) {
  const chart = document.querySelector(".chart");
  if (!chart || !bars.length) return;

  const points = bars.map((bar) => ({
    time: parseTime(bar.timestamp),
    close: Number(bar.close),
  })).filter((p) => p.time && Number.isFinite(p.close));
  if (points.length < 2) return;

  const width = 1000;
  const height = 350;
  const padX = 25;
  const padY = 25;
  const min = Math.min(...points.map((p) => p.close), Number(state.reference_low || Infinity));
  const max = Math.max(...points.map((p) => p.close), Number(state.reference_high || -Infinity));
  const range = Math.max(max - min, 0.000001);
  const x = (i) => padX + (i / (points.length - 1)) * (width - padX * 2);
  const y = (price) => height - padY - ((price - min) / range) * (height - padY * 2);
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(p.close).toFixed(1)}`).join(" ");

  const anchorIndex = points.findIndex((p) => {
    const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(p.time);
    const h = Number(parts.find((v) => v.type === "hour")?.value);
    const m = Number(parts.find((v) => v.type === "minute")?.value);
    return h === 9 && m === 45;
  });
  const anchorX = anchorIndex >= 0 ? x(anchorIndex) : null;
  const highY = Number.isFinite(Number(state.reference_high)) ? y(Number(state.reference_high)) : null;
  const lowY = Number.isFinite(Number(state.reference_low)) ? y(Number(state.reference_low)) : null;

  chart.innerHTML = `<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
    <g stroke="#1c314a" stroke-width="1">
      <path d="M0 60H1000"/><path d="M0 130H1000"/><path d="M0 200H1000"/><path d="M0 270H1000"/>
    </g>
    <path d="${path}" fill="none" stroke="#49a6ff" stroke-width="3"/>
    ${highY == null ? "" : `<path d="M0 ${highY}H1000" stroke="#49d39a" stroke-width="1" stroke-dasharray="5 5"/><text x="15" y="${Math.max(15, highY - 6)}" fill="#91a4bd" font-size="12">08:45 high</text>`}
    ${lowY == null ? "" : `<path d="M0 ${lowY}H1000" stroke="#49d39a" stroke-width="1" stroke-dasharray="5 5"/><text x="15" y="${Math.min(340, lowY + 14)}" fill="#91a4bd" font-size="12">08:45 low</text>`}
    ${anchorX == null ? "" : `<path d="M${anchorX} 20V330" stroke="#f1bd62" stroke-width="2" stroke-dasharray="7 7"/><text x="${Math.min(anchorX + 10, 900)}" y="35" fill="#f1bd62" font-size="14">09:45 MAIN</text>`}
  </svg>`;
}

function updateClock() {
  setText("clock", new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(new Date()));
}

async function runPaperSimulation() {
  const run = $("run");
  if (run) {
    run.disabled = true;
    run.textContent = "Running…";
  }
  setText("model", "RUNNING");

  try {
    const risk = Number($("risk")?.value) || 1;
    const rr = Number($("rr")?.value) || 2;

    const response = await fetch(`${API}/api/backtest?risk_percent=${encodeURIComponent(risk)}&risk_reward=${encodeURIComponent(rr)}`);
    if (!response.ok) throw new Error(`Backtest failed (HTTP ${response.status})`);
    const data = await response.json();

    renderSummary(data.summary);
    renderTrades(data.trades);

    const stateResponse = await fetch(`${API}/api/execution-state`);
    let state = {};
    if (stateResponse.ok) {
      state = await stateResponse.json();
      renderExecutionState(state);
    }
    renderChart(data.bars, state);

    setText("model", "READY");
  } catch (error) {
    setText("model", "ERROR");
    const body = $("body");
    if (body) body.innerHTML = `<tr><td colspan="8" class="empty">Backend connection failed: ${error.message}</td></tr>`;
  } finally {
    if (run) {
      run.disabled = false;
      run.textContent = "Run paper simulation";
    }
  }
}

window.addEventListener("load", () => {
  updateClock();
  setInterval(updateClock, 1000);
  const run = $("run");
  if (run) run.onclick = runPaperSimulation;
});
