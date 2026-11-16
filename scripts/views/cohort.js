"use strict";
const data = JSON.parse(document.getElementById("study-data").textContent);
const byId = id => document.getElementById(id);
const viewNames = {observed:"已有观测", complete_case:"完整病例", imputed:"简单填补"};
const groupNames = {ckd:"CKD", notckd:"非 CKD", unknown:"诊断缺失"};
const featureNames = {age:"年龄",bp:"血压",sg:"尿比重",al:"白蛋白分级",su:"尿糖分级",rbc:"红细胞评估",pc:"脓细胞",pcc:"脓细胞团",ba:"细菌",bgr:"随机血糖",bu:"血尿素",sc:"血清肌酐",sod:"血钠",pot:"血钾",hemo:"血红蛋白",pcv:"红细胞压积",wbcc:"白细胞计数",rbcc:"红细胞计数",htn:"高血压",dm:"糖尿病",cad:"冠心病",appet:"食欲",pe:"足部水肿",ane:"贫血"};
const clinicalQuestions = {
  sc: ["al", "白蛋白分级与血清肌酐", "比较各白蛋白等级的肌酐。肾脏滤过与肌肉量均可影响肌酐；这里的白蛋白等级 0–5 也缺少换算为定量尿白蛋白/肌酐比的依据。", "NIDDK 肌酐解读", "https://www.niddk.nih.gov/research-funding/research-programs/kidney-clinical-research-epidemiology/laboratory/factors-affecting-egfr-accuracy/clinical-measurements"],
  bu: ["al", "白蛋白分级与血尿素", "可与同等级的血清肌酐对照。肾脏清除和脱水都可能影响血尿素；单个较高读数不足以区分原因。bu 沿用 UCI 的血尿素定义。", "NHS 尿素检验", "https://www.southtees.nhs.uk/services/pathology/tests/Urea/"],
  hemo: ["ane", "贫血记录与血红蛋白", "比较记录有、无贫血者的血红蛋白。肾病相关的促红细胞生成素减少、缺铁及炎症均可能参与贫血。此表没有铁代谢指标，UCI 的血红蛋白单位也未给出浓度分母。", "NIDDK 肾病与贫血", "https://www.niddk.nih.gov/health-information/kidney-disease/anemia"],
  bgr: ["dm", "糖尿病记录与随机血糖", "随机血糖反映采血时点的读数。对照糖尿病记录时，需考虑进餐时间、降糖用药和糖化血红蛋白在本表中均未记录。", "NIDDK 糖尿病检验", "https://www.niddk.nih.gov/health-information/professionals/clinical-tools-patient-management/diabetes/diabetes-prediabetes"],
  bp: ["htn", "高血压记录与血压", "每行只提供一个血压值，字典未指明收缩压或舒张压。可比较原始高血压记录各层的读数分布，判断血压控制情况还需规范的重复测量。", "WHO 高血压说明", "https://www.who.int/news-room/fact-sheets/detail/hypertension"]
};
const states = {measured:"原始实测",absent:"该项缺失",filled:"该项已填补",removed:"整行剔除"};
const marks = {observed:"●",complete_case:"◆",imputed:"▲"};
const views = Object.keys(viewNames);
const ruleNames={all24:"全部 24 项",core5:"5 个核心指标",current:"当前分析所需字段"};
const {quantile,correlation,retained}=RenalMath;
const rule=()=>byId("deletion-rule").value;
const keep=(p,fields)=>retained(p,rule(),data.measures,fields);
const inGroup=(p,group)=>group==="all" || p.group===group;
const number = new Intl.NumberFormat("zh-CN",{maximumSignificantDigits:4});
const fmt = n => Number.isFinite(n) ? number.format(n) : "—";
const share = (n,total) => total ? (100*n/total).toFixed(1)+"%" : "—";
const featureLabel = f => featureNames[f] || f;
const withUnit = f => featureLabel(f)+"（"+data.units[f]+"）";
const idMap = new Map(data.patients.map(p => [String(p.id),p]));
const pairs = data.correlations.filter(r => r.view === "observed");
let pairIndex = pairs.findIndex(r => r.feature_x === "sc" && r.feature_y === "bu");
if (pairIndex < 0) pairIndex = 0;
function el(tag,cls="",text="") {
  const out=document.createElement(tag);
  out.className=cls;
  out.textContent=text;
  return out;
}
function draw(parent,tag,attrs,text="") {
  const out=document.createElementNS("http://www.w3.org/2000/svg",tag);
  for(const [key,value] of Object.entries(attrs)) out.setAttribute(key,value);
  out.textContent=text;
  parent.append(out);
  return out;
}
function options(select,items) {
  for (const [value,label] of items) select.add(new Option(label,value));
}
function stateOf(p,feature,view) {
  if(view === "complete_case" && !keep(p,[feature])) return "removed";
  if(!p.missing.includes(feature)) return "measured";
  return view === "imputed" ? "filled" : "absent";
}
function patientDetail() {
  const patient = idMap.get(byId("patient").value);
  if (!patient) return;
  const f = byId("feature").value, view = byId("view").value;
  const status = stateOf(patient,f,view);
  const value = (view === "imputed" ? patient.imputed : patient.observed)[f];
  const missing = patient.missing.map(featureLabel).join("、") || "无";
  const reading = Number.isFinite(value) ? "，"+fmt(value)+" "+data.units[f] : "";
  const valueText = status === "removed" && reading ? "（该项原有实测值 "+fmt(value)+" "+data.units[f]+"）" : reading;
  byId("patient-detail").textContent = "行 "+patient.id+" · "+groupNames[patient.group]+" · "+featureLabel(f)+"："+states[status]+valueText+"。原始缺失 "+patient.missing.length+" 项："+missing+"。";
  for(const cell of byId("people").querySelectorAll("button")) {
    const active = cell.dataset.id === String(patient.id);
    cell.setAttribute("aria-pressed",active);
    cell.tabIndex = active ? 0 : -1;
  }
  byId("patient-search").value=patient.id;
  byId("state-summary").textContent="行 "+patient.id+" · "+featureLabel(f)+" · 患者矩阵："+viewNames[view]+" · 完整要求："+ruleNames[rule()]+" · 散点："+viewNames[byId("scatter-view").value]+" / "+(byId("scatter-group").value==="all"?"全体":groupNames[byId("scatter-group").value]);
  RenalState.links();
}
function renderPeople() {
  const f=byId("feature").value, view=byId("view").value, box=byId("people");
  box.replaceChildren();
  const retained = data.patients.filter(p => view !== "complete_case" || keep(p,[f])).length;
  for(const [group,label] of Object.entries(groupNames)) {
    const people = data.patients.filter(p => p.group === group);
    if(!people.length) continue;
    const section = el("div","people-group"), heading = el("h3","",label), cells = el("div","cells");
    let n = 0, valid = 0;
    for(const p of people) {
      const state = stateOf(p,f,view), button = el("button",state);
      if(state !== "removed") n++;
      if(state === "measured" || state === "filled") valid++;
      button.type="button";
      button.dataset.id=String(p.id);
      button.title="行 "+p.id+" · "+featureLabel(f)+" · "+states[state];
      button.setAttribute("aria-label",button.title);
      cells.append(button);
    }
    heading.append(el("small","","保留 "+n+" / "+people.length+" 人（"+share(n,people.length)+"） · 占当前队列 "+share(n,retained)+" · 该项有效 n="+valid));
    section.append(heading,cells);
    box.append(section);
  }
  patientDetail();
  renderRuleComparison();
}
function renderRuleComparison() {
  const body=byId("rule-comparison"),feature=byId("feature").value;
  body.replaceChildren();
  for(const key of Object.keys(ruleNames)) {
    const selected=data.patients.filter(p=>retained(p,key,data.measures,[feature]));
    const ckd=selected.filter(p=>p.group==="ckd").length,other=selected.filter(p=>p.group==="notckd").length;
    const row=el("tr");
    const original=group=>data.patients.filter(p=>p.group===group).length;
    for(const value of [ruleNames[key],selected.length+" / "+data.patients.length,ckd+" / "+original("ckd"),other+" / "+original("notckd"),share(ckd,selected.length)]) row.append(el("td","",value));
    body.append(row);
  }
  const selected=data.patients.filter(p=>p.group==="ckd" && keep(p,[feature]));
  const glucose=selected.map(p=>p.observed.bgr).filter(Number.isFinite), high=glucose.filter(v=>v>=200).length;
  byId("rule-outcomes").textContent="所选完整要求下，CKD 中随机血糖实测且 ≥200 mg/dL 为 "+high+" / "+glucose.length+"（"+share(high,glucose.length)+"）；保留 CKD "+selected.length+" 人。当前字段集合："+(rule()==="all24"?"全部 24 项":(rule()==="core5"?data.measures:[feature]).map(featureLabel).join("、"))+"。";
}
function renderMissingComparison() {
  const svg=byId("missing-comparison");svg.replaceChildren();
  draw(svg,"text",{x:180,y:18},"原诊断组内缺失率（%）；● CKD（250 人）　◇ 非 CKD（150 人）");
  const x=mapper([0,1],180,615);
  data.missing_rates.slice(0,6).forEach((r,i)=>{
    const y=48+i*27, rates=["ckd","notckd"].map(group=>{
      const patients=data.patients.filter(p=>p.group===group);
      return patients.filter(p=>p.missing.includes(r.feature)).length/patients.length;
    });
    draw(svg,"text",{x:4,y:y+4},featureLabel(r.feature));
    draw(svg,"line",{x1:x(rates[0]),x2:x(rates[1]),y1:y,y2:y,stroke:"#a7b9b8"});
    draw(svg,"circle",{cx:x(rates[0]),cy:y,r:4,fill:"#156368"});
    draw(svg,"path",{d:`M ${x(rates[1])} ${y-5} l5 5 -5 5 -5 -5z`,fill:"white",stroke:"#455775"});
    draw(svg,"text",{x:640,y:y+4},rates.map(v=>(100*v).toFixed(1)+"%").join(" / "));
  });
  xAxis(svg,[0,100],180,615,208);
}
function summaryRow(view,group,feature) {
  if(view!=="complete_case") return data.summary.find(r=>r.view===view && r.group===group && r.feature===feature);
  const people=data.patients.filter(p=>inGroup(p,group) && keep(p,[feature]));
  const values=people.map(p=>p.observed[feature]).filter(Number.isFinite);
  const ref=data.summary.find(r=>r.view==="observed" && r.group==="all" && r.feature===feature).observed_global_median;
  const q1=quantile(values,.25),q3=quantile(values,.75);
  return {view,group,feature,n:values.length,n_records:people.length,q1,q3,median:quantile(values,.5),iqr:q3-q1,observed_global_median:ref};
}
function extent(values) {
  const xs=values.filter(Number.isFinite);
  if(!xs.length) return [0,1];
  const lo=Math.min(...xs), hi=Math.max(...xs);
  const margin=lo===hi ? Math.max(Math.abs(lo)*.05,1) : (hi-lo)*.045;
  return [lo-margin,hi+margin];
}
function mapper(domain,start,end) {
  return x => start + (x-domain[0])*(end-start)/(domain[1]-domain[0]);
}
function xAxis(svg,domain,left,right,y) {
  draw(svg,"line",{x1:left,x2:right,y1:y,y2:y,stroke:"#85948f"});
  for(let i=0;i<=4;i++) {
    const pos=left+(right-left)*i/4;
    draw(svg,"line",{x1:pos,x2:pos,y1:y,y2:y+4,stroke:"#85948f"});
    draw(svg,"text",{x:pos,y:y+20,"text-anchor":"middle"},fmt(domain[0]+(domain[1]-domain[0])*i/4));
  }
}
function renderDistribution() {
  const f=byId("feature").value, group=byId("dist-group").value, svg=byId("quartiles");
  const rows=views.map(view => summaryRow(view,group,f));
  const ref=rows[0].observed_global_median;
  const domain=extent([ref,...rows.flatMap(r => [r.q1,r.q3])]);
  const x=mapper(domain,154,595);
  svg.replaceChildren();
  draw(svg,"text",{x:154,y:18},withUnit(f));
  if(Number.isFinite(ref)) draw(svg,"line",{x1:x(ref),x2:x(ref),y1:26,y2:164,stroke:"#a74724","stroke-dasharray":"4 4"});
  for(const [i,r] of rows.entries()) {
    const y=52+48*i;
    draw(svg,"text",{x:4,y:y+4},viewNames[r.view]+" · n="+r.n);
    if(!Number.isFinite(r.median)) {
      draw(svg,"text",{x:615,y:y+4},"无有效读数");
      continue;
    }
    const color={observed:"#27242a",complete_case:"#941344",imputed:"#156368"}[r.view];
    draw(svg,"line",{x1:x(r.q1),x2:x(r.q3),y1:y,y2:y,stroke:color,"stroke-width":5,"stroke-dasharray":r.view==="complete_case"?"7 4":r.view==="imputed"?"2 3":"none"});
    const point=draw(svg,"circle",{cx:x(r.median),cy:y,r:6,fill:color});
    draw(point,"title",{},"Q1 / 中位数 / Q3："+[r.q1,r.median,r.q3].map(fmt).join(" / "));
    draw(svg,"text",{x:615,y:y+4},[r.q1,r.median,r.q3].map(fmt).join("  /  "));
  }
  draw(svg,"text",{x:615,y:18},"Q1  /  中位数  /  Q3");
  xAxis(svg,domain,154,595,174);
  const r=rows[2], measured=r.n_at_observed_global_median-r.n_imputed;
  const bar=byId("concentration");
  bar.replaceChildren();
  const description = "全队列填充值 "+fmt(ref)+" "+data.units[f]+"。深色实心 "+measured+" 人原本等于该值，斜纹 "+r.n_imputed+" 人由填补落到该值，浅灰 "+(r.n-r.n_at_observed_global_median)+" 人为其他读数。前两部分合计占 "+share(r.n_at_observed_global_median,r.n)+"（n="+r.n+"）。";
  for(const [cls,n] of [["at-reference",measured],["at-fill",r.n_imputed],["elsewhere",r.n-r.n_at_observed_global_median]]) {
    const segment=el("span",cls);
    segment.style.width=(r.n ? 100*n/r.n : 0)+"%";
    bar.append(segment);
  }
  bar.setAttribute("aria-label",description);
  byId("dist-count").textContent=description;
  renderExtremes();
}
function renderExtremes() {
  const feature=byId("feature").value, group=byId("dist-group").value, view=byId("extreme-view").value;
  const subset=summaryRow(view,"all",feature);
  const rows=data.patients.filter(p=>inGroup(p,group) && (view!=="complete_case" || keep(p,[feature])))
    .filter(p=>Number.isFinite(p.observed[feature]))
    .map(p=>({row_id:p.id,value:p.observed[feature]}))
    .filter(r=>r.value<subset.q1-1.5*subset.iqr || r.value>subset.q3+1.5*subset.iqr);
  const select=byId("extreme");
  select.replaceChildren(new Option(rows.length ? "选择一位患者" : "无标记记录",""));
  options(select,rows.map(r => [r.row_id,fmt(r.value)+" "+data.units[feature]+" · 行 "+r.row_id]));
  select.disabled=!rows.length;
  byId("locate-extreme").disabled=true;
  const bounds = subset.n ? "界限 "+fmt(subset.q1-1.5*subset.iqr)+" 至 "+fmt(subset.q3+1.5*subset.iqr)+" "+data.units[feature]+"，参照 n="+subset.n+"。" : "当前视角没有有效读数可估计界限。";
  byId("extreme-count").textContent = bounds+" 所选人群内可复核 "+rows.length+" 条实测记录。";
}
function renderCorrelations() {
  const method=byId("method").value, list=byId("corr-list");
  list.replaceChildren();
  for(const [i,pair] of pairs.entries()) {
    const row=el("button","corr-row"), track=el("span","r-track"), counts=[], descriptions=[];
    row.type="button";
    row.dataset.index=String(i);
    row.setAttribute("aria-pressed",i===pairIndex);
    row.append(el("span","",featureLabel(pair.feature_x)+" × "+featureLabel(pair.feature_y)));
    for(const [k,view] of views.entries()) {
      const r=pairStats(pair,view);
      counts.push(r.n_pairs);
      descriptions.push(viewNames[view]+" "+fmt(r[method])+"（n="+r.n_pairs+"）");
      if(!Number.isFinite(r[method])) continue;
      const mark=el("span","r-mark r-"+view,marks[view]);
      mark.style.left=50*(1+Math.max(-1,Math.min(1,r[method])))+"%";
      mark.style.top=(21+29*k)+"%";
      track.append(mark);
    }
    row.title=descriptions.join(" · ");
    row.setAttribute("aria-label",row.firstChild.textContent+"，"+row.title);
    row.append(track,el("span","n-pairs",counts.join(" / ")));
    list.append(row);
  }
}
function pairStats(pair,view) {
  const group=byId("scatter-group").value,fields=[pair.feature_x,pair.feature_y];
  const people=data.patients.filter(p=>inGroup(p,group) && (view!=="complete_case" || keep(p,fields)));
  const points=people.map(p=>fields.map(f=>(view==="imputed"?p.imputed:p.observed)[f])).filter(p=>p.every(Number.isFinite));
  return {n_pairs:points.length,pearson:correlation(points,"pearson"),spearman:correlation(points,"spearman")};
}
function renderScatter() {
  const pair=pairs[pairIndex], view=byId("scatter-view").value, svg=byId("scatter");
  const method=byId("method").value, fx=pair.feature_x, fy=pair.feature_y;
  const record=pairStats(pair,view),group=byId("scatter-group").value;
  const people=data.patients.filter(p=>inGroup(p,group));
  const log=byId("scatter-scale").value==="log",transform=v=>log?Math.log10(v):v;
  const xDom=extent(people.map(p=>p.imputed[fx]).filter(v=>Number.isFinite(v) && (!log || v>0)).map(transform));
  const yDom=extent(people.map(p=>p.imputed[fy]).filter(v=>Number.isFinite(v) && (!log || v>0)).map(transform));
  const x=mapper(xDom,92,790), y=mapper(yDom,270,28), counts=[0,0,0];
  svg.replaceChildren();
  draw(svg,"line",{x1:92,x2:790,y1:270,y2:270,stroke:"#85948f"});
  for(let i=0;i<=4;i++) {
    const value=xDom[0]+(xDom[1]-xDom[0])*i/4,pos=x(value);
    draw(svg,"line",{x1:pos,x2:pos,y1:270,y2:274,stroke:"#85948f"});
    draw(svg,"text",{x:pos,y:293,"text-anchor":"middle"},fmt(log?10**value:value));
  }
  draw(svg,"text",{x:440,y:330,"text-anchor":"middle"},withUnit(fx)+(log?" · 对数坐标":""));
  draw(svg,"text",{x:12,y:16},withUnit(fy)+(log?" · 对数坐标":""));
  draw(svg,"line",{x1:92,x2:92,y1:28,y2:270,stroke:"#85948f"});
  for(let i=0;i<=4;i++) {
    const value=yDom[0]+(yDom[1]-yDom[0])*i/4;
    draw(svg,"text",{x:80,y:y(value)+5,"text-anchor":"end"},fmt(log?10**value:value));
  }
  if(view==="imputed") {
    const median=f => data.summary.find(r => r.feature===f && r.group==="all" && r.view==="observed").observed_global_median;
    const mx=x(transform(median(fx))), my=y(transform(median(fy)));
    draw(svg,"line",{x1:mx,x2:mx,y1:28,y2:270,stroke:"#b78569","stroke-dasharray":"4 4"});
    draw(svg,"line",{x1:92,x2:790,y1:my,y2:my,stroke:"#b78569","stroke-dasharray":"4 4"});
  }
  for(const p of people) {
    if(view==="complete_case" && !keep(p,[fx,fy])) continue;
    const values=view==="imputed" ? p.imputed : p.observed;
    if(!Number.isFinite(values[fx]) || !Number.isFinite(values[fy])) continue;
    if(log && (values[fx]<=0 || values[fy]<=0)) continue;
    const filled=view==="imputed" ? Number(p.missing.includes(fx))+Number(p.missing.includes(fy)) : 0;
    const px=x(transform(values[fx])), py=y(transform(values[fy]));
    let point;
    if(filled===0) point=draw(svg,"circle",{cx:px,cy:py,r:3.6,fill:"#245a57","fill-opacity":.46});
    else if(filled===1) point=draw(svg,"path",{d:"M"+px+" "+(py-4.4)+"l4.5 8h-9z",fill:"#d17b4b","fill-opacity":.68,stroke:"#7d3821","stroke-width":.7});
    else point=draw(svg,"rect",{x:px-4,y:py-4,width:8,height:8,fill:"none",stroke:"#702e15","stroke-width":1.5});
    point.setAttribute("data-patient",p.id);
    point.style.cursor="pointer";
    if(String(p.id)===byId("patient").value) draw(svg,"circle",{cx:px,cy:py,r:8,fill:"none",stroke:"#941344","stroke-width":2,"pointer-events":"none"});
    counts[filled]++;
    draw(point,"title",{},"行 "+p.id+" · "+featureLabel(fx)+" "+fmt(values[fx])+" · "+featureLabel(fy)+" "+fmt(values[fy])+" · "+filled+" 项填补");
  }
  byId("pair-value").textContent=featureLabel(fx)+" × "+featureLabel(fy)+" · "+(method==="pearson"?"Pearson":"Spearman")+" "+fmt(record[method])+" · n="+record.n_pairs;
  byId("point-count").textContent="● 两项实测 "+counts[0]+" 人　▲ 一项填补 "+counts[1]+" 人　□ 两项填补 "+counts[2]+" 人";
  patientDetail();
}
function changeFeature(event) {
  byId("dist-feature").value=byId("feature").value=event.target.value;
  renderPeople();
  renderDistribution();
  renderCorrelations();
  renderScatter();
  RenalState.save();
}
function renderClinicalStrata() {
  const feature = byId("clinical-question").value;
  const group = byId("clinical-group").value;
  const [context, label, interpretation, sourceName, sourceUrl] = clinicalQuestions[feature];
  const bothGroups = data.clinical_strata.filter(r => r.feature === feature && r.context === context);
  const rows = bothGroups.filter(r => r.group === group);
  const domain = extent(bothGroups.flatMap(r => [r.q1, r.q3]));
  const position = mapper(domain, 0, 100);
  const head = byId("clinical-head"), body = byId("clinical-body");
  head.replaceChildren();
  body.replaceChildren();
  const citation = el("a", "", sourceName);
  citation.href = sourceUrl;
  byId("clinical-interpretation").replaceChildren(interpretation + " ", citation);
  byId("clinical-caption").textContent = groupNames[group] + " · " + label + " · " + withUnit(feature);
  const contextHeading = el("th", "", "原始" + featureLabel(context));
  contextHeading.scope = "col";
  head.append(contextHeading);
  for (const view of views) {
    const heading = el("th", "", viewNames[view]);
    heading.scope = "col";
    const groupN = rows.find(r => r.view === view).n_group;
    heading.append(el("small", "", "组内 " + groupN + " 人"));
    head.append(heading);
  }
  const levelNames = {yes:"记录为有", no:"记录为无", unrecorded:"未记录"};
  for (const baseline of rows.filter(r => r.view === "observed")) {
    const tr = el("tr");
    const levelHeading = el("th", "", levelNames[baseline.level] || "等级 " + baseline.level);
    levelHeading.scope = "row";
    tr.append(levelHeading);
    for (const view of views) {
      const row = rows.find(r => r.view === view && r.level === baseline.level);
      const cell = el("td");
      if (row.n_used) {
        cell.append(el("strong", "", fmt(row.median) + " ［" + fmt(row.q1) + "，" + fmt(row.q3) + "］"));
        const rail = el("span", "clinical-range"), band = el("i"), median = el("b");
        rail.setAttribute("aria-hidden", "true");
        band.style.left = position(row.q1) + "%";
        band.style.width = (position(row.q3) - position(row.q1)) + "%";
        median.style.left = position(row.median) + "%";
        rail.append(band, median);
        cell.append(rail);
      } else {
        cell.append(el("strong", "", row.n_stratum ? "无有效读数" : "该层无人"));
      }
      cell.append(el("small", "", "有效 " + row.n_used + " / 层内 " + row.n_stratum + " 人"));
      cell.append(el("small", "", "实测 " + row.n_measured + " · 填补 " + row.n_imputed));
      tr.append(cell);
    }
    body.append(tr);
  }
}
options(byId("clinical-question"), Object.entries(clinicalQuestions).map(([feature, question]) => [feature, question[1]]));
byId("clinical-question").addEventListener("change", renderClinicalStrata);
byId("clinical-group").addEventListener("change", renderClinicalStrata);
for(const id of ["feature","dist-feature"]) {
  options(byId(id),data.measures.map(f => [f,featureLabel(f)]));
  byId(id).addEventListener("change",changeFeature);
}
for(const id of ["view","scatter-view","extreme-view"]) options(byId(id),Object.entries(viewNames));
byId("view").value=byId("extreme-view").value=byId("scatter-view").value="complete_case";
options(byId("patient"),data.patients.map(p => [p.id,"行 "+p.id+" · "+groupNames[p.group]]));
for(const r of data.missing_rates) {
  const entry=el("li");
  entry.append(el("span","",featureLabel(r.feature)+" · "+r.feature),el("span","",r.n_missing+" / "+r.n_records+"（"+share(r.n_missing,r.n_records)+"）"));
  byId("missing-list").append(entry);
}
const stateIds=["patient","feature","view","deletion-rule","dist-group","extreme-view","scatter-view","scatter-group","method","scatter-scale","linked-view","clinical-question","clinical-group"];
RenalState.restore(stateIds);
byId("dist-feature").value=byId("feature").value;
function renderAll() {
  renderPeople();renderDistribution();renderCorrelations();renderScatter();
}
function selectPatient(id) {
  if(!idMap.has(String(id))) return;
  byId("patient").value=String(id);patientDetail();renderScatter();RenalState.save();
}
byId("view").addEventListener("change",() => {
  byId("extreme-view").value=byId("view").value;
  if(byId("linked-view").checked) byId("scatter-view").value=byId("view").value;
  renderAll();
});
byId("deletion-rule").addEventListener("change",renderAll);
byId("patient").addEventListener("change",()=>selectPatient(byId("patient").value));
byId("patient-search").addEventListener("change",event=>{
  const valid=idMap.has(event.target.value);
  event.target.setCustomValidity(valid?"":"请输入 1–400 之间的原始行号");
  if(valid) selectPatient(event.target.value);else event.target.reportValidity();
});
byId("people").addEventListener("click",event => {
  const cell=event.target.closest("button");
  if(cell) selectPatient(cell.dataset.id);
});
byId("people").addEventListener("keydown",event => {
  const step={ArrowRight:1,ArrowLeft:-1}[event.key];
  if(!step) return;
  const cells=[...byId("people").querySelectorAll("button")], next=cells[cells.indexOf(event.target)+step];
  if(next) { event.preventDefault(); next.focus(); next.click(); }
});
byId("dist-group").addEventListener("change",renderDistribution);
byId("extreme-view").addEventListener("change",() => {
  byId("view").value=byId("extreme-view").value;
  if(byId("linked-view").checked) byId("scatter-view").value=byId("view").value;
  renderAll();
});
byId("extreme").addEventListener("change",() => {
  const row=byId("extreme").value;
  byId("locate-extreme").disabled=!row;
  if(row) selectPatient(row);
});
byId("locate-extreme").addEventListener("click",() => {
  const cell=byId("people").querySelector('button[aria-pressed="true"]');
  if(cell) cell.focus();
});
byId("method").addEventListener("change",() => { renderCorrelations(); renderScatter(); });
byId("corr-list").addEventListener("click",event => {
  const row=event.target.closest("button");
  if(!row) return;
  pairIndex=Number(row.dataset.index);
  const url=new URL(location.href);url.searchParams.set("pair",String(pairIndex));history.replaceState(null,"",url);
  for(const b of byId("corr-list").children) b.setAttribute("aria-pressed",b===row);
  renderScatter();
});
byId("scatter-view").addEventListener("change",()=>{byId("linked-view").checked=false;renderScatter();});
byId("linked-view").addEventListener("change",()=>{
  if(byId("linked-view").checked) byId("scatter-view").value=byId("view").value;
  renderScatter();
});
byId("scatter-group").addEventListener("change",()=>{renderCorrelations();renderScatter();});
byId("scatter-scale").addEventListener("change",renderScatter);
byId("scatter").addEventListener("click",event=>{
  const point=event.target.closest("[data-patient]");if(point) selectPatient(point.dataset.patient);
});
for(const button of document.querySelectorAll("[data-preset]")) button.addEventListener("click",()=>{
  const preset=button.dataset.preset;
  if(preset==="reset") {
    byId("feature").value="hemo";byId("patient").value="1";byId("deletion-rule").value="all24";
    byId("view").value="complete_case";byId("dist-group").value="all";
    byId("scatter-group").value="all";byId("method").value="pearson";byId("scatter-scale").value="linear";
    pairIndex=pairs.findIndex(r=>r.feature_x==="sc" && r.feature_y==="bu");
  } else if(preset==="case") {
    byId("feature").value="bgr";byId("patient").value="43";byId("view").value="complete_case";byId("deletion-rule").value="all24";
  } else if(preset==="extreme") {
    const largest=data.patients.filter(p=>Number.isFinite(p.observed.sc)).sort((a,b)=>b.observed.sc-a.observed.sc)[0];
    byId("feature").value="sc";byId("patient").value=String(largest.id);byId("view").value="observed";
  } else if(preset==="imputation") {
    byId("feature").value="hemo";byId("view").value="imputed";
    byId("patient").value=String(data.patients.find(p=>p.missing.includes("hemo")).id);
  }
  byId("dist-feature").value=byId("feature").value;
  byId("extreme-view").value=byId("scatter-view").value=byId("view").value;byId("linked-view").checked=true;
  const url=new URL(location.href);url.searchParams.set("pair",String(pairIndex));history.replaceState(null,"",url);
  renderAll();RenalState.save();
});
const savedPair=Number(new URLSearchParams(location.search).get("pair"));
if(new URLSearchParams(location.search).has("pair") && Number.isInteger(savedPair) && pairs[savedPair]) pairIndex=savedPair;
renderMissingComparison();
renderAll();
renderClinicalStrata();
