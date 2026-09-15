const API = window.TRADING_ROBOT_API || "https://trading-robot-app-2.onrender.com";
const $ = (id) => document.getElementById(id);

function num(value, digits = 2) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return Number(value).toLocaleString(undefined, { minimumFractionDigits: digits, maximumFractionDigits: digits });
}
function setText(id, value) { const el = $(id); if (el) el.textContent = value; }
function renderSummary(summary = {}) { setText("trades", summary.trades ?? "—"); setText("win", summary.win_rate_pct == null ? "—" : `${num(summary.win_rate_pct)}%`); setText("net", summary.net_r == null ? "—" : `${num(summary.net_r)}R`); setText("dd", summary.max_drawdown_r == null ? "—" : `${num(summary.max_drawdown_r)}R`); }

function renderHistoricalData(data = {}) {
  const total = data.total || {}, model = data.model_period || {};
  setText("data-status", data.status === "ready" ? "READY" : "EMPTY");
  setText("data-source", data.source === "repository_sample_csv" ? "Repository sample CSV" : (data.source || "—"));
  setText("data-candles", total.rows ?? "—"); setText("data-sessions", total.sessions ?? "—");
  setText("data-timeframe", total.timeframe_minutes ? `${total.timeframe_minutes} min` : "—"); setText("data-model-candles", model.rows ?? "—");
}

async function loadHistoricalData() {
  try { const r = await fetch(`${API}/api/historical-data`); if (!r.ok) throw new Error(`Historical data failed (HTTP ${r.status})`); renderHistoricalData(await r.json()); }
  catch (e) { setText("data-status", "ERROR"); setText("data-source", e.message); }
}

async function loadQuality(dataset) {
  try {
    const r = await fetch(`${API}/api/data-quality?dataset=${encodeURIComponent(dataset)}`);
    if (!r.ok) throw new Error(`Quality check failed (HTTP ${r.status})`);
    const data = await r.json(), q = data.quality || data;
    const passed = q.passed ?? q.valid;
    setText("quality", passed === true ? "DATA QUALITY: PASS · Ready for paper research" : passed === false ? `DATA QUALITY: REVIEW · ${q.reason || "Check the dataset before using it"}` : "Data-quality report loaded");
  } catch (e) { setText("quality", `DATA QUALITY: UNAVAILABLE · ${e.message}`); }
}

function renderTrades(trades = []) {
  const body = $("body"); if (!body) return;
  if (!trades.length) { body.innerHTML = '<tr><td colspan="8" class="empty">No qualifying paper trades found.</td></tr>'; return; }
  body.innerHTML = trades.map((trade) => `<tr><td>${trade.session_date ?? "—"}</td><td>${trade.window ?? "—"}</td><td>${(trade.direction ?? "—").toUpperCase()}</td><td>${num(trade.entry)}</td><td>${num(trade.stop)}</td><td>${num(trade.target)}</td><td>${trade.outcome ?? "—"}</td><td>${trade.r_multiple == null ? "—" : `${num(trade.r_multiple)}R`}</td></tr>`).join("");
}
function renderExecutionState(state = {}) {
  setText("ah", num(state.reference_high)); setText("al", num(state.reference_low)); setText("direction", (state.direction || "neutral").toUpperCase());
  setText("liq", state.sweep_type ? state.sweep_type.replaceAll("_", " ").toUpperCase() : "WAITING"); setText("disp", state.displacement == null ? "WAITING" : `CONFIRMED ${num(state.displacement, 2)}x`);
  setText("struct", state.structure ? state.structure.toUpperCase() : "NEUTRAL"); setText("entry", state.entry == null ? "—" : num(state.entry)); setText("stop", state.invalidation == null ? "—" : num(state.invalidation)); setText("target", state.target == null ? "—" : num(state.target));
  setText("qual", state.status === "qualified" ? `QUALIFIED · ${state.sweep_type || "reaction"}` : (state.reason || "Waiting for objective confirmation"));
}
function parseTime(value) { const d = new Date(value); return Number.isNaN(d.getTime()) ? null : d; }
function nyParts(date) { const parts = new Intl.DateTimeFormat("en-US", { timeZone: "America/New_York", hour: "2-digit", minute: "2-digit", hour12: false }).formatToParts(date); return { hour: Number(parts.find((v) => v.type === "hour")?.value), minute: Number(parts.find((v) => v.type === "minute")?.value) }; }
function minutesFromMidnight(date) { const { hour, minute } = nyParts(date); return hour * 60 + minute; }
function renderChart(bars = [], state = {}) {
  const chart = document.querySelector(".chart"); if (!chart || !bars.length) return;
  const points = bars.map((bar) => ({ time: parseTime(bar.timestamp), close: Number(bar.close) })).filter((p) => p.time && Number.isFinite(p.close)); if (points.length < 2) return;
  const width=1000,height=350,padX=25,padY=25,prices=points.map(p=>p.close); [state.reference_low,state.reference_high,state.entry,state.invalidation,state.target].forEach(v=>{if(v!=null&&Number.isFinite(Number(v)))prices.push(Number(v));});
  const min=Math.min(...prices),max=Math.max(...prices),range=Math.max(max-min,.000001),x=i=>padX+(i/(points.length-1))*(width-padX*2),y=p=>height-padY-((p-min)/range)*(height-padY*2); const path=points.map((p,i)=>`${i?'L':'M'}${x(i).toFixed(1)} ${y(p.close).toFixed(1)}`).join(" ");
  const firstMinutes=minutesFromMidnight(points[0].time),lastMinutes=minutesFromMidnight(points[points.length-1].time),totalMinutes=Math.max(lastMinutes-firstMinutes,1),xForMinutes=m=>padX+((m-firstMinutes)/totalMinutes)*(width-padX*2);
  const starts=[[585,"09:45"],[630,"10:30"],[675,"11:15"],[720,"12:00"],[765,"12:45"],[810,"13:30"],[855,"14:15"],[900,"15:00"],[945,"15:45"]];
  const boundaryLines=starts.filter(([m])=>m>=firstMinutes&&m<=lastMinutes).map(([m,label])=>{const bx=xForMinutes(m);return `<path d="M${bx.toFixed(1)} 20V330" stroke="#6f86a1" stroke-width="1" stroke-dasharray="3 6"/><text x="${Math.min(bx+5,925).toFixed(1)}" y="318" fill="#91a4bd" font-size="10">${label}</text>`;}).join("");
  const anchorX=585>=firstMinutes&&585<=lastMinutes?xForMinutes(585):null,highY=Number.isFinite(Number(state.reference_high))?y(Number(state.reference_high)):null,lowY=Number.isFinite(Number(state.reference_low))?y(Number(state.reference_low)):null,entryY=Number.isFinite(Number(state.entry))?y(Number(state.entry)):null,stopY=Number.isFinite(Number(state.invalidation))?y(Number(state.invalidation)):null,targetY=Number.isFinite(Number(state.target))?y(Number(state.target)):null,confirmationX=state.confirmation_time?xForMinutes(minutesFromMidnight(parseTime(state.confirmation_time))):null;
  chart.innerHTML=`<svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"><g stroke="#1c314a" stroke-width="1"><path d="M0 60H1000"/><path d="M0 130H1000"/><path d="M0 200H1000"/><path d="M0 270H1000"/></g>${boundaryLines}<path d="${path}" fill="none" stroke="#49a6ff" stroke-width="3"/>${highY==null?"":`<path d="M0 ${highY}H1000" stroke="#49d39a" stroke-width="1" stroke-dasharray="5 5"/><text x="15" y="${Math.max(15,highY-6)}" fill="#91a4bd" font-size="12">08:45 high</text>`}${lowY==null?"":`<path d="M0 ${lowY}H1000" stroke="#49d39a" stroke-width="1" stroke-dasharray="5 5"/><text x="15" y="${Math.min(340,lowY+14)}" fill="#91a4bd" font-size="12">08:45 low</text>`}${anchorX==null?"":`<path d="M${anchorX} 20V330" stroke="#f1bd62" stroke-width="2" stroke-dasharray="7 7"/><text x="${Math.min(anchorX+10,900)}" y="35" fill="#f1bd62" font-size="14">09:45 MAIN</text>`}${confirmationX==null?"":`<path d="M${confirmationX.toFixed(1)} 20V330" stroke="#b58cff" stroke-width="2" stroke-dasharray="4 4"/><text x="${Math.min(confirmationX+8,900).toFixed(1)}" y="55" fill="#b58cff" font-size="12">3m confirmation</text>`}${entryY==null?"":`<path d="M0 ${entryY}H1000" stroke="#49a6ff" stroke-width="2"/><text x="15" y="${Math.max(15,entryY-6)}" fill="#49a6ff" font-size="11">PAPER ENTRY</text>`}${stopY==null?"":`<path d="M0 ${stopY}H1000" stroke="#ff7272" stroke-width="2" stroke-dasharray="6 4"/><text x="15" y="${Math.min(340,stopY+14)}" fill="#ff7272" font-size="11">PAPER INVALIDATION</text>`}${targetY==null?"":`<path d="M0 ${targetY}H1000" stroke="#49d39a" stroke-width="2"/><text x="15" y="${Math.max(15,targetY-6)}" fill="#49d39a" font-size="11">PAPER TARGET</text>`}</svg>`;
}
function updateClock(){setText("clock",new Intl.DateTimeFormat("en-US",{timeZone:"America/New_York",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false}).format(new Date()));}
async function runPaperSimulation(){
  const run=$("run"); if(run){run.disabled=true;run.textContent="Running…";} setText("model","RUNNING");
  try{
    const risk=Number($("risk")?.value)||1,rr=Number($("rr")?.value)||2,dataset=$("dataset")?.value||"sample";
    if(dataset==="historical"){const q=await fetch(`${API}/api/data-quality?dataset=historical`);if(!q.ok)throw new Error(`Historical dataset is not ready (HTTP ${q.status})`);const qd=await q.json();if(qd.quality&&qd.quality.passed===false)throw new Error(qd.quality.reason||"Historical data failed quality checks");}
    const response=await fetch(`${API}/api/backtest?dataset=${encodeURIComponent(dataset)}&risk_percent=${encodeURIComponent(risk)}&risk_reward=${encodeURIComponent(rr)}`); if(!response.ok)throw new Error(`Paper simulation failed (HTTP ${response.status})`);
    const data=await response.json();renderSummary(data.summary);renderTrades(data.trades);const stateResponse=await fetch(`${API}/api/execution-state?dataset=${encodeURIComponent(dataset)}&risk_reward=${encodeURIComponent(rr)}`);let state={};if(stateResponse.ok){state=await stateResponse.json();renderExecutionState(state);}renderChart(data.bars,state);setText("model","READY");
  }catch(error){setText("model","ERROR");const body=$("body");if(body)body.innerHTML=`<tr><td colspan="8" class="empty">Paper simulation error: ${error.message}</td></tr>`;}finally{if(run){run.disabled=false;run.textContent="Run paper simulation";}}
}
window.addEventListener("load",()=>{updateClock();setInterval(updateClock,1000);loadHistoricalData();loadQuality($("dataset")?.value||"sample");const ds=$("dataset");if(ds)ds.addEventListener("change",()=>loadQuality(ds.value));const run=$("run");if(run)run.onclick=runPaperSimulation;});
