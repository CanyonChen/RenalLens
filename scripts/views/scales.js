"use strict";
const study = JSON.parse(document.getElementById("study-data").textContent);
const patients = study.patients;
const measures = study.measures;
const names = {hemo:"血红蛋白", sc:"血清肌酐", bu:"血尿素", bgr:"血糖", bp:"血压"};
const scales = ["raw", "zscore"];
const groups = {ckd:"CKD", notckd:"非 CKD", unknown:"诊断缺失"};
const groupSymbols = {ckd:"●", notckd:"◇", unknown:"×"};
const fmt = new Intl.NumberFormat("zh-CN", {maximumSignificantDigits:4});
const num = x => Number.isFinite(x) ? fmt.format(x) : "—";
const pct = x => (100 * x).toFixed(1) + "%";
const get = id => document.getElementById(id);
const svgNS = "http://www.w3.org/2000/svg";
function svg(parent, tag, attrs, label) {
  const el = document.createElementNS(svgNS, tag);
  for (const [key, val] of Object.entries(attrs)) el.setAttribute(key, val);
  if (label != null) el.textContent = label;
  parent.append(el);
  return el;
}
function el(parent, tag, label) {
  const child = document.createElement(tag);
  if (label != null) child.textContent = label;
  parent.append(child);
  return child;
}
function tableRow(body, heading, values) {
  const row = el(body, "tr");
  el(row, "th", heading).scope = "row";
  for (const value of values) el(row, "td", value);
  return row;
}
function ticks(lo, hi) {
  const approx = (hi - lo) / 4;
  const power = 10 ** Math.floor(Math.log10(approx));
  const step = [1, 2, 5, 10].find(n => n * power >= approx) * power;
  const values = [];
  for (let i = Math.ceil(lo / step); i <= Math.floor(hi / step); i++) values.push(i * step);
  return values;
}
const patientPicker = get("patient");
const projectionLayers = {};
let activeIndex = 0;

function drawProjection(scale) {
  const chart = get("projection-" + scale);
  const scores = patients.map(p => p.scores[scale]);
  const xs = scores.map(s => s[0]), ys = scores.map(s => s[1]);
  const xlo = Math.min(...xs), xhi = Math.max(...xs), ylo = Math.min(...ys), yhi = Math.max(...ys);
  const left = 52, right = 439, top = 27, bottom = 253;
  // The two axes share one unit length inside a panel; each PCA fit has its own range.
  const unit = 1.1 * (Math.max((xhi - xlo) / (right - left), (yhi - ylo) / (bottom - top)) || 1);
  const xmid = (xlo + xhi) / 2, ymid = (ylo + yhi) / 2;
  const x = v => (left + right) / 2 + (v - xmid) / unit;
  const y = v => (top + bottom) / 2 - (v - ymid) / unit;
  const xhalf = unit * (right - left) / 2, yhalf = unit * (bottom - top) / 2;
  for (const v of ticks(xmid - xhalf, xmid + xhalf)) {
    svg(chart,"line",{x1:x(v),x2:x(v),y1:top,y2:bottom,stroke:v === 0 ? "#a3b3ab" : "#e1e7e1"});
    svg(chart,"text",{x:x(v),y:bottom + 17,"text-anchor":"middle"},num(v));
  }
  for (const v of ticks(ymid - yhalf, ymid + yhalf)) {
    svg(chart,"line",{x1:left,x2:right,y1:y(v),y2:y(v),stroke:v === 0 ? "#a3b3ab" : "#e1e7e1"});
    svg(chart,"text",{x:left - 6,y:y(v) + 4,"text-anchor":"end"},num(v));
  }
  const variance = study.variance.filter(row => row.scale === scale);
  function axisName(pc) {
    const row = variance.find(r => r.component === pc);
    return pc + " · " + pct(row.explained_fraction) + " 解释方差";
  }
  svg(chart,"text",{x:left,y:16,class:"axis-name"},axisName("PC2"));
  svg(chart,"text",{x:right,y:bottom + 40,"text-anchor":"end",class:"axis-name"},axisName("PC1"));
  patients.forEach((p,i) => {
    const [a,b] = scores[i], px = x(a), py = y(b);
    const mark = svg(chart,"g",{class:"mark","data-index":i,opacity:0.68,transform:"translate(" + px + " " + py + ")"});
    if (p.group === "ckd") svg(mark,"circle",{r:3.4,fill:"#29706e"});
    else if (p.group === "notckd") svg(mark,"path",{d:"M 0 -4 L 4 0 L 0 4 L -4 0 Z",fill:"#f7faf7",stroke:"#455775","stroke-width":1.3});
    else svg(mark,"path",{d:"M -3 -3 L 3 3 M -3 3 L 3 -3",stroke:"#5b5651","stroke-width":1.7});
    svg(mark,"title",{},"行 " + p.id + " · " + groups[p.group] + " · PC1 " + num(a) + " · PC2 " + num(b));
  });
  chart.addEventListener("click", event => {
    const mark = event.target.closest(".mark");
    if (mark) selectPatient(Number(mark.dataset.index));
  });
  const selected = svg(chart,"g",{"pointer-events":"none"});
  svg(selected,"circle",{r:7.7,fill:"none",stroke:"#fff","stroke-width":5});
  svg(selected,"circle",{r:7.7,fill:"none",stroke:"#ae411e","stroke-width":2.5});
  projectionLayers[scale] = {selected, x, y};
}

function showWeights() {
  const pc = get("component").value, body = get("weights");
  body.replaceChildren();
  for (const f of measures) {
    const row = tableRow(body, names[f], []);
    for (const scale of scales) {
      const metric = study.loadings.find(r => r.scale === scale && r.component === pc && r.feature === f);
      const weight = metric.eigenvector_weight;
      const cell = el(row, "td");
      cell.className = "coef-cell";
      const track = el(cell, "span");
      track.className = "coef";
      track.setAttribute("aria-hidden","true");
      const bar=el(track,"i");
      bar.style.width=(Math.abs(weight)*50)+"%";
      bar.style.left=(weight<0?50+weight*50:50)+"%";
      bar.style.backgroundColor=weight<0?"#941344":"#156368";
      cell.append((weight>0?"+":"")+num(weight));
      el(cell,"small","平方占比 "+pct(weight**2));
    }
  }
}

function blend(a, b, t) {
  return "rgb(" + a.map((v,i) => Math.round(v + (b[i] - v) * t)).join(",") + ")";
}
const pale = [244,246,239], blue = [32,86,116], rust = [142,66,32];
function drawStrip() {
  const key = get("strip-scale").value;
  const all = patients.flatMap(p => measures.map(f => p[key][f]));
  const central=key==="z" && get("strip-range").value==="central";
  const range = central?3:Math.max(...all.map(Math.abs)) || 1;
  const lo = key === "raw" ? Math.min(...all) : -range;
  const hi = key === "raw" ? Math.max(...all) : range;
  const color = value => key === "raw" ? blend(pale,blue,(value - lo) / (hi - lo || 1))
    : blend(pale,value < 0 ? blue : rust,Math.min(1,Math.abs(value) / range));
  const strip = get("strip");
  strip.width = patients.length; strip.height = measures.length;
  const ctx = strip.getContext("2d");
  patients.forEach((p,i) => measures.forEach((f,j) => {
    ctx.fillStyle = color(p[key][f]);
    ctx.fillRect(i,j,1,1);
  }));
  const legend = get("strip-key");
  legend.replaceChildren();
  el(legend, "span", key === "raw" ? "共用原值色标，各行单位见下表" : "z 分数色标，浅色为零");
  el(legend, "span", num(lo));
  const swatches = el(legend,"span");
  swatches.className = "swatches"; swatches.setAttribute("aria-hidden","true");
  for (let i = 0; i <= 12; i++) el(swatches,"i").style.backgroundColor = color(lo + i * (hi - lo) / 12);
  el(legend, "span",num(hi));
  if(central) el(legend,"span","超界 "+all.filter(v=>Math.abs(v)>3).length+" / "+all.length+" 个读数以端点颜色显示；原数值保留在下表。");
}

const logPicker = get("log-feature");
const logSeries = new Map();
for (const r of study.log_pairs) {
  if (!logSeries.has(r.feature)) logSeries.set(r.feature, []);
  logSeries.get(r.feature).push(r);
}
for (const [f, rows] of logSeries) {
  rows.sort((a,b) => a.raw - b.raw || a.row_id - b.row_id);
  logPicker.add(new Option(names[f], f));
}
function showTails() {
  if (!logSeries.size) return;
  const f = logPicker.value, rows = logSeries.get(f), patient = patients[activeIndex];
  const first = rows[0], last = rows[rows.length - 1];
  const chart = get("tails"), body = get("quantiles");
  chart.replaceChildren(); body.replaceChildren();
  const x = (row,key) => 97 + 582 * (row[key] - first[key]) / (last[key] - first[key] || 1);
  const track = {raw:48, ln:116};
  for (const [key,y] of Object.entries(track)) {
    svg(chart,"line",{x1:97,x2:679,y1:y,y2:y,stroke:"#6a817c"});
    svg(chart,"text",{x:8,y:y + 4,class:"axis-name"},key === "raw" ? "原值" : "自然对数");
    const rug = rows.map(r => "M" + x(r,key).toFixed(2) + "," + (y - 4) + "v8").join(" ");
    svg(chart,"path",{d:rug,fill:"none",stroke:"#839c97","stroke-width":1});
    const tickY = key === "raw" ? y - 13 : y + 22;
    svg(chart,"text",{x:97,y:tickY,"text-anchor":"start"},num(first[key]));
    svg(chart,"text",{x:679,y:tickY,"text-anchor":"end"},num(last[key]));
  }
  get("raw-unit").textContent = "原值（" + study.units[f] + "）";
  const ranks = [
    {label:"P50", fraction:0.5, dash:"none", symbol:"━"},
    {label:"P90", fraction:0.9, dash:"7 4", symbol:"┅"},
    {label:"P99", fraction:0.99, dash:"2 3", symbol:"┈"}
  ];
  function connect(r,color,width,dash) {
    svg(chart,"line",{x1:x(r,"raw"),y1:track.raw,x2:x(r,"ln"),y2:track.ln,stroke:color,"stroke-width":width,"stroke-dasharray":dash});
  }
  for (const q of ranks) {
    const r = rows[Math.ceil(q.fraction * rows.length) - 1];
    connect(r,"#335a59",1.6,q.dash);
    tableRow(body, q.symbol + " " + q.label, [num(r.raw),num(r.ln)]);
  }
  const paired = rows.find(r => String(r.row_id) === String(patient.id));
  let selectedText = "当前患者原记录缺失此项。";
  if (paired) {
    connect(paired,"#ae411e",3,"none");
    for (const [key,y] of Object.entries(track)) svg(chart,"circle",{cx:x(paired,key),cy:y,r:4.4,fill:"#ae411e",stroke:"#fff","stroke-width":1});
    selectedText = "行 " + patient.id + " 的实测值 " + num(paired.raw) + " " + study.units[f] + "，自然对数 " + num(paired.ln) + "。";
  }
  get("log-readout").textContent = names[f] + "，配对 n = " + rows.length + "。" + selectedText;
}

function selectPatient(index) {
  activeIndex = index;
  patientPicker.selectedIndex = index;
  const p = patients[index];
  for (const scale of scales) {
    const {selected,x,y} = projectionLayers[scale];
    const [a,b] = p.scores[scale];
    selected.setAttribute("transform","translate(" + x(a) + " " + y(b) + ")");
    get("score-" + scale).textContent = "行 " + p.id + " · PC1 " + num(a) + " · PC2 " + num(b);
  }
  get("record-label").textContent = "行 " + p.id + " · " + groups[p.group];
  get("ruler").style.left = "calc(" + (100 * (index + 0.5) / patients.length) + "% - 1px)";
  const record = get("record");
  record.replaceChildren();
  for (const f of measures) {
    const source = p.missing.includes(f) ? "◇ 中位数填补" : "● 实测";
    tableRow(record, names[f] + " · " + f, [num(p.raw[f]) + " " + study.units[f], num(p.z[f]), source]);
  }
  showTails();
  RenalState.save();
}

for (const p of patients) patientPicker.add(new Option("行 " + p.id + " · " + groups[p.group], p.id));
get("cohort-count").textContent = "两图使用同一批 " + patients.length + " 位患者和相同的五项指标，缺失项先用中位数填补。诊断标签用于标记点形。环标追踪同一条记录，两图各自拟合坐标轴，距离在各自图内解读。";
for (const [group,label] of Object.entries(groups)) {
  const n = patients.filter(p => p.group === group).length;
  if (n) el(get("group-key"),"span",groupSymbols[group] + " " + label + "（n = " + n + "）");
}
el(get("group-key"),"span","◎ 选中患者");
for (const f of measures) el(get("strip-labels"), "span", names[f]);
for (const scale of scales) drawProjection(scale);
showWeights();
drawStrip();
if (!logSeries.size) {
  get("log-figure").hidden = true;
  get("log-control").hidden = true;
  get("log-rule").append(" 本队列没有符合条件的指标。");
}
RenalState.restore(["patient","component","strip-scale","strip-range","log-feature"]);
const sharedFeature=new URLSearchParams(location.search).get("feature");
if(sharedFeature && logSeries.has(sharedFeature)) logPicker.value=sharedFeature;
if(get("strip-range").value==="central") get("strip-scale").value="z";
showWeights();drawStrip();
selectPatient(patientPicker.selectedIndex<0?0:patientPicker.selectedIndex);
patientPicker.addEventListener("change", () => selectPatient(patientPicker.selectedIndex));
get("component").addEventListener("change", showWeights);
get("strip-scale").addEventListener("change",()=>{
  if(get("strip-scale").value==="raw") get("strip-range").value="full";
  drawStrip();
});
get("strip-range").addEventListener("change",()=>{
  if(get("strip-range").value==="central") get("strip-scale").value="z";
  drawStrip();
});
logPicker.addEventListener("change", showTails);
get("strip").addEventListener("click", event => {
  const rect = event.currentTarget.getBoundingClientRect();
  const index = Math.floor((event.clientX - rect.left) / rect.width * patients.length);
  selectPatient(Math.min(patients.length - 1, Math.max(0, index)));
});
get("strip").addEventListener("keydown", event => {
  if (event.key !== "ArrowLeft" && event.key !== "ArrowRight") return;
  event.preventDefault();
  const step = event.key === "ArrowRight" ? 1 : -1;
  selectPatient(Math.min(patients.length - 1, Math.max(0,activeIndex + step)));
});
