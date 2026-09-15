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
  setText("qual", state.status === "qualified" ? `QUALIFIED · ${state.sweep_type || "reaction"}` : (state.reason || "Waiting for objective confirmation"));
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
  const model = $("model");
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
    if (stateResponse.ok) renderExecutionState(await stateResponse.json());

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
