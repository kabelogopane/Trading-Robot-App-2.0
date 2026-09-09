const statusEl = document.getElementById("status");
const runButton = document.getElementById("runButton");
const tradeBody = document.getElementById("tradeBody");

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined) return "—";
  return Number(value).toFixed(digits);
}

function renderSummary(summary) {
  document.getElementById("trades").textContent = summary.trades ?? "—";
  document.getElementById("winRate").textContent =
    summary.win_rate_pct == null ? "—" : `${formatNumber(summary.win_rate_pct)}%`;
  document.getElementById("netR").textContent =
    summary.net_r == null ? "—" : `${formatNumber(summary.net_r)}R`;
  document.getElementById("drawdown").textContent =
    summary.max_drawdown_r == null ? "—" : `${formatNumber(summary.max_drawdown_r)}R`;
}

function renderTrades(trades) {
  if (!trades.length) {
    tradeBody.innerHTML = '<tr><td colspan="8">No qualifying trades found.</td></tr>';
    return;
  }

  tradeBody.innerHTML = trades.map((trade) => `
    <tr>
      <td>${trade.session_date}</td>
      <td>${trade.window}</td>
      <td>${trade.direction}</td>
      <td>${formatNumber(trade.entry)}</td>
      <td>${formatNumber(trade.stop)}</td>
      <td>${formatNumber(trade.target)}</td>
      <td>${trade.outcome}</td>
      <td>${trade.r_multiple == null ? "—" : `${formatNumber(trade.r_multiple)}R`}</td>
    </tr>
  `).join("");
}

async function runBacktest() {
  runButton.disabled = true;
  runButton.textContent = "Running...";

  try {
    const response = await fetch("/api/backtest");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    renderSummary(data.summary);
    renderTrades(data.trades);
    statusEl.textContent = "Paper backtest ready";
  } catch (error) {
    statusEl.textContent = "Backtest error";
    tradeBody.innerHTML = `<tr><td colspan="8">${error.message}</td></tr>`;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run paper backtest";
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    statusEl.textContent = data.status === "ok" ? "System online" : "System unavailable";
  } catch (_) {
    statusEl.textContent = "Server unavailable";
  }
}

runButton.addEventListener("click", runBacktest);
checkHealth();
