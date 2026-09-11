const $ = (id) => document.getElementById(id);
const statusEl = $("status");
const runButton = $("runButton");
const tradeBody = $("tradeBody");

function num(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function renderSummary(summary = {}) {
  $("trades").textContent = summary.trades ?? "—";
  $("winRate").textContent = summary.win_rate_pct == null ? "—" : `${num(summary.win_rate_pct)}%`;
  $("netR").textContent = summary.net_r == null ? "—" : `${num(summary.net_r)}R`;
  $("drawdown").textContent = summary.max_drawdown_r == null ? "—" : `${num(summary.max_drawdown_r)}R`;
}

function renderTrades(trades = []) {
  if (!trades.length) {
    tradeBody.innerHTML = '<tr><td colspan="8">No qualifying paper trades found in the selected data.</td></tr>';
    return;
  }
  tradeBody.innerHTML = trades.map(t => `<tr>
    <td>${t.session_date ?? "—"}</td><td>${t.window ?? "—"}</td>
    <td>${(t.direction ?? "—").toUpperCase()}</td><td>${num(t.entry)}</td>
    <td>${num(t.stop)}</td><td>${num(t.target)}</td><td>${t.outcome ?? "—"}</td>
    <td>${t.r_multiple == null ? "—" : `${num(t.r_multiple)}R`}</td>
  </tr>`).join("");
}

function renderSessionState(bars = []) {
  const reference = bars.filter(b => {
    const d = new Date(b.timestamp);
    const ny = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(d);
    return ny >= "08:45" && ny < "09:45";
  });
  if (reference.length) {
    $("anchorHigh").textContent = num(Math.max(...reference.map(b => Number(b.high))));
    $("anchorLow").textContent = num(Math.min(...reference.map(b => Number(b.low))));
    $("referenceState").textContent = "Captured";
  } else {
    $("referenceState").textContent = "No 08:45 data";
  }

  const anchor = bars.find(b => {
    const d = new Date(b.timestamp);
    return new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(d) === "09:45";
  });
  $("anchorState").textContent = anchor ? "Detected" : "Waiting";
  if (bars.length) {
    const last = bars[bars.length - 1];
    const time = new Date(last.timestamp);
    const label = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).format(time);
    $("windowState").textContent = label;
  }
}

function renderSetup(trades = []) {
  const last = trades[trades.length - 1];
  if (!last) return;
  $("direction").textContent = (last.direction || "neutral").toUpperCase();
  $("entry").textContent = num(last.entry);
  $("stop").textContent = num(last.stop);
  $("target").textContent = num(last.target);
  $("qualification").textContent = last.outcome ? `Last setup: ${last.outcome.replaceAll("_", " ")}` : "Qualified paper setup";
}

async function runBacktest() {
  runButton.disabled = true;
  runButton.textContent = "Running…";
  $("modelState").textContent = "RUNNING";
  try {
    const rr = Number($("rr").value) || 2;
    const risk = Number($("risk").value) || 1;
    const response = await fetch(`/api/backtest?risk_percent=${encodeURIComponent(risk)}&risk_reward=${encodeURIComponent(rr)}`);
    if (!response.ok) throw new Error(`Backtest request failed (HTTP ${response.status})`);
    const data = await response.json();
    renderSummary(data.summary);
    renderTrades(data.trades);
    renderSetup(data.trades);
    renderSessionState(data.bars || []);
    $("dataSource").textContent = "BACKTEST COMPLETE";
    $("chartMode").textContent = "PAPER DATA";
    $("modelState").textContent = "READY";
    statusEl.innerHTML = "<i></i> System online · paper mode";
    drawChart(data.bars || []);
  } catch (error) {
    $("modelState").textContent = "ERROR";
    statusEl.innerHTML = "<i></i> Backend unavailable";
    tradeBody.innerHTML = `<tr><td colspan="8">${error.message}. Start the FastAPI server with <code>python run_robot.py</code>.</td></tr>`;
  } finally {
    runButton.disabled = false;
    runButton.textContent = "Run paper backtest";
  }
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health");
    const data = await response.json();
    statusEl.innerHTML = data.status === "ok" ? "<i></i> System online · paper mode" : "<i></i> System unavailable";
  } catch (_) {
    statusEl.innerHTML = "<i></i> Start backend to connect";
  }
}

function drawChart(bars) {
  const canvas = $("priceChart");
  const rect = canvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  canvas.width = rect.width * dpr; canvas.height = rect.height * dpr;
  const ctx = canvas.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const w = rect.width, h = rect.height;
  ctx.clearRect(0, 0, w, h);
  if (!bars.length) return drawSampleChart(ctx, w, h);
  const values = bars.map(b => Number(b.close)).filter(Number.isFinite);
  const min = Math.min(...values), max = Math.max(...values), pad = 25;
  const x = i => pad + (i / Math.max(values.length - 1, 1)) * (w - pad * 2);
  const y = v => h - pad - ((v - min) / Math.max(max - min, 1)) * (h - pad * 2);
  ctx.lineWidth = 1;
  ctx.strokeStyle = "#1d2b40";
  for (let i = 1; i < 5; i++) { const yy = pad + i * (h - pad * 2) / 5; ctx.beginPath(); ctx.moveTo(pad, yy); ctx.lineTo(w-pad, yy); ctx.stroke(); }
  ctx.strokeStyle = "#5e9bff"; ctx.lineWidth = 2; ctx.beginPath();
  values.forEach((v,i) => i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v))); ctx.stroke();
}

function drawSampleChart(ctx, w, h) {
  const pad = 25; const points = 80;
  const vals = Array.from({length: points}, (_, i) => 50 + i * .11 + Math.sin(i/5)*2 + Math.sin(i/11)*1.2);
  const min = Math.min(...vals), max = Math.max(...vals);
  const x=i=>pad+i/(points-1)*(w-pad*2), y=v=>h-pad-(v-min)/(max-min)*(h-pad*2);
  ctx.strokeStyle="#1d2b40"; ctx.lineWidth=1;
  for(let i=1;i<5;i++){const yy=pad+i*(h-pad*2)/5;ctx.beginPath();ctx.moveTo(pad,yy);ctx.lineTo(w-pad,yy);ctx.stroke();}
  ctx.strokeStyle="#5e9bff";ctx.lineWidth=2;ctx.beginPath();vals.forEach((v,i)=>i?ctx.lineTo(x(i),y(v)):ctx.moveTo(x(i),y(v)));ctx.stroke();
  ctx.setLineDash([5,5]);ctx.strokeStyle="#e0ad4f";ctx.beginPath();ctx.moveTo(w*.35,pad);ctx.lineTo(w*.35,h-pad);ctx.stroke();ctx.setLineDash([]);
  ctx.fillStyle="#7488a5";ctx.font="10px system-ui";ctx.fillText("09:45 anchor",w*.35+7,pad+12);
}

runButton.addEventListener("click", runBacktest);
window.addEventListener("resize", () => {
  const canvas = $("priceChart");
  if (canvas) drawChart([], canvas.clientWidth, canvas.clientHeight);
});
setInterval(() => {
  $("clock").textContent = new Intl.DateTimeFormat("en-US", { timeZone:"America/New_York", hour:"2-digit", minute:"2-digit", second:"2-digit", hour12:false }).format(new Date());
}, 1000);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/service-worker.js").catch(() => {}));
}

checkHealth();
setTimeout(() => drawChart([]), 50);
