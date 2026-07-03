import json

from .config import ACCENT
from .i18n import get_language

LABELS = {
    "en": {
        "title": "Timora",
        "dow": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
        "mon": ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
        "tabs": {"day": "Day", "week": "Week", "month": "Month", "year": "Year", "all": "All"},
        "today": "Today", "yesterday": "Yesterday", "tomorrow": "Tomorrow",
        "thisWeek": "This week", "thisMonth": "This month", "thisYear": "This year",
        "allTime": "All time",
        "totlbl": {"day": "This day", "week": "This week", "month": "This month",
                   "year": "This year", "all": "All time"},
        "logged": "Logged", "trend": "Trend",
        "last7": "Last 7 days", "byWeekday": "By weekday", "byDay": "By day",
        "byMonth": "By month", "last12": "Last 12 months",
        "noRecords": "No records.", "noTasks": "No tasks registered.",
        "noRecordsYet": "No records yet.",
        "estVsActual": "Est vs Actual", "estVsActualTotal": "Est vs Actual (total)",
        "actual": "actual", "est": "est", "noEstimate": "no estimate",
        "done": "done", "count": "x", "uh": "h", "um": "m", "us": "s",
    },
    "ko": {
        "title": "Timora",
        "dow": ["일", "월", "화", "수", "목", "금", "토"],
        "mon": ["1월", "2월", "3월", "4월", "5월", "6월",
                "7월", "8월", "9월", "10월", "11월", "12월"],
        "tabs": {"day": "일", "week": "주", "month": "월", "year": "년", "all": "전체"},
        "today": "오늘", "yesterday": "어제", "tomorrow": "내일",
        "thisWeek": "이번 주", "thisMonth": "이번 달", "thisYear": "올해",
        "allTime": "전체 기간",
        "totlbl": {"day": "이 날 한 일", "week": "이 주 한 일", "month": "이 달 한 일",
                   "year": "이 해 한 일", "all": "전체 한 일"},
        "logged": "한 일", "trend": "추이",
        "last7": "최근 7일", "byWeekday": "요일별", "byDay": "일별",
        "byMonth": "월별", "last12": "최근 12개월",
        "noRecords": "기록이 없어요.", "noTasks": "등록된 할 일이 없어요.",
        "noRecordsYet": "아직 기록이 없어요.",
        "estVsActual": "예상 vs 실제", "estVsActualTotal": "예상 vs 실제 (누적)",
        "actual": "실제", "est": "예상", "noEstimate": "예상 미설정",
        "done": "완료", "count": "회", "uh": "시간", "um": "분", "us": "초",
    },
}


def build_report(db):
    data_json = json.dumps(db, ensure_ascii=False)
    labels = LABELS.get(get_language(), LABELS["en"])
    return (REPORT_HTML
            .replace("__DATA__", data_json)
            .replace("__ACCENT__", ACCENT)
            .replace("__L__", json.dumps(labels, ensure_ascii=False)))


REPORT_HTML = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Timora</title>
<style>
:root{--bg:#0f1117;--card:#1a1d27;--card2:#232734;--line:#2c3140;--txt:#e7e9ee;--sub:#9aa1b1;--accent:#6366f1;--accent2:#8b5cf6;--green:#22c55e;}
*{box-sizing:border-box;}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Segoe UI",sans-serif;background:var(--bg);color:var(--txt);padding:18px;max-width:780px;margin:0 auto;}
h1{font-size:20px;margin:4px 0 16px;}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:14px;}
.label{font-size:12px;color:var(--sub);margin-bottom:8px;font-weight:600;}
.datenav{display:flex;align-items:center;justify-content:space-between;gap:8px;}
.datenav button{background:var(--card2);color:var(--txt);border:none;border-radius:10px;padding:8px 16px;font-size:18px;cursor:pointer;}
.cur{text-align:center;font-weight:600;font-size:15px;}.cur small{display:block;color:var(--sub);font-size:12px;font-weight:400;}
.total{display:flex;justify-content:space-between;align-items:baseline;}.total .big{font-size:28px;font-weight:700;}
.entry{display:flex;align-items:center;gap:10px;padding:11px 0;border-bottom:1px solid var(--line);}.entry:last-child{border-bottom:none;}
.dot{width:10px;height:10px;border-radius:50%;flex-shrink:0;}.entry .meta{flex:1;min-width:0;}
.entry .nm{font-size:15px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}.entry .tm{font-size:12px;color:var(--sub);}
.entry .dur{font-variant-numeric:tabular-nums;font-weight:600;}.empty{color:var(--sub);text-align:center;padding:20px 0;font-size:14px;}
.catstat{margin:10px 0;}.catstat .top{display:flex;justify-content:space-between;font-size:13px;margin-bottom:5px;}
.catstat .bar{height:9px;border-radius:5px;background:var(--card2);overflow:hidden;}.catstat .fill{height:100%;border-radius:5px;}
.chart{display:flex;align-items:flex-end;gap:8px;height:150px;padding-top:8px;}
.chart .col{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;height:100%;justify-content:flex-end;cursor:pointer;}
.chart .barwrap{width:100%;flex:1;display:flex;align-items:flex-end;}
.chart .b{width:100%;border-radius:6px 6px 0 0;background:linear-gradient(180deg,var(--accent),var(--accent2));min-height:2px;}
.chart .b.today{background:linear-gradient(180deg,var(--green),#15803d);}
.chart .lbl{font-size:11px;color:var(--sub);}.chart .val{font-size:10px;color:var(--sub);height:12px;}
.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px;}
.tab{padding:7px 14px;border-radius:20px;font-size:13px;cursor:pointer;background:var(--card2);border:1px solid var(--line);color:var(--sub);user-select:none;}
.tab.on{background:var(--accent);color:#fff;border-color:transparent;}
</style></head><body>
<h1 id="h1"></h1>
<div class="card">
  <div class="tabs" id="tabs"></div>
  <div class="datenav">
    <button id="prev" onclick="move(-1)">&lsaquo;</button>
    <div class="cur"><span id="vd"></span></div>
    <button id="next" onclick="move(1)">&rsaquo;</button>
  </div>
</div>
<div class="card"><div class="total"><div class="label" style="margin:0" id="totlbl"></div><div class="big" id="tot">0</div></div>
  <div id="list" style="margin-top:12px"></div></div>
<div class="card"><div class="label" id="chartlbl"></div><div class="chart" id="week"></div></div>
<div class="card"><div class="label" id="cmplbl"></div><div id="cmp"></div></div>
<script>
const DB=__DATA__;
const ACCENT="__ACCENT__";
const L=__L__;
const DOW=L.dow, MON=L.mon;
const PERIODS=[["day",L.tabs.day],["week",L.tabs.week],["month",L.tabs.month],["year",L.tabs.year],["all",L.tabs.all]];
let mode="day";
let anchor=midnight(new Date());
document.getElementById("h1").textContent=L.title;
function midnight(d){return new Date(d.getFullYear(),d.getMonth(),d.getDate());}
function sec(d){return d.getTime()/1000;}
function col(){return ACCENT;}
function fdur(s){s=Math.floor(s);const h=Math.floor(s/3600),m=Math.floor((s%3600)/60);if(h)return m?h+L.uh+" "+m+L.um:h+L.uh;if(m)return m+L.um;return s+L.us;}
function tod(ts){const d=new Date(ts*1000);return String(d.getHours()).padStart(2,"0")+":"+String(d.getMinutes()).padStart(2,"0");}
function md(ts){const d=new Date(ts*1000);return (d.getMonth()+1)+"/"+d.getDate();}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function weekStart(d){const x=midnight(d);const wd=(x.getDay()+6)%7;x.setDate(x.getDate()-wd);return x;}
function range(){
  const a=anchor;
  if(mode==="day"){const s=midnight(a);return {s:sec(s),e:sec(s)+86400};}
  if(mode==="week"){const s=weekStart(a);const e=new Date(s);e.setDate(e.getDate()+7);return {s:sec(s),e:sec(e)};}
  if(mode==="month"){return {s:sec(new Date(a.getFullYear(),a.getMonth(),1)),e:sec(new Date(a.getFullYear(),a.getMonth()+1,1))};}
  if(mode==="year"){return {s:sec(new Date(a.getFullYear(),0,1)),e:sec(new Date(a.getFullYear()+1,0,1))};}
  return {s:0,e:Date.now()/1000+86400};
}
function setMode(m){mode=m;anchor=midnight(new Date());render();}
function move(n){
  if(mode==="all")return;
  const a=anchor;const shift=k=>{if(mode==="day")a.setDate(a.getDate()+k);else if(mode==="week")a.setDate(a.getDate()+7*k);else if(mode==="month")a.setMonth(a.getMonth()+k);else if(mode==="year")a.setFullYear(a.getFullYear()+k);};
  shift(n);
  if(range().s>Date.now()/1000){shift(-n);return;}
  render();
}
function periodLabel(){
  const a=anchor,now=new Date();
  if(mode==="day"){const diff=Math.round((midnight(a)-midnight(now))/86400000);
    if(diff===0)return L.today;if(diff===-1)return L.yesterday;if(diff===1)return L.tomorrow;
    return MON[a.getMonth()]+" "+a.getDate()+" ("+DOW[a.getDay()]+")";}
  if(mode==="week"){const s=weekStart(a),e=new Date(s);e.setDate(e.getDate()+6);
    const cur=weekStart(now).getTime()===s.getTime();
    return (cur?L.thisWeek+" - ":"")+(s.getMonth()+1)+"/"+s.getDate()+" ~ "+(e.getMonth()+1)+"/"+e.getDate();}
  if(mode==="month"){const cur=a.getFullYear()===now.getFullYear()&&a.getMonth()===now.getMonth();
    return MON[a.getMonth()]+" "+a.getFullYear()+(cur?" - "+L.thisMonth:"");}
  if(mode==="year"){const cur=a.getFullYear()===now.getFullYear();return a.getFullYear()+(cur?" - "+L.thisYear:"");}
  return L.allTime;
}
function inRange(){const r=range();return DB.entries.filter(x=>x.start>=r.s&&x.start<r.e);}
function bucketSum(s,e){return DB.entries.filter(x=>x.start>=s&&x.start<e).reduce((a,x)=>a+x.dur,0);}
function render(){
  document.getElementById("tabs").innerHTML=PERIODS.map(p=>'<div class="tab'+(p[0]===mode?" on":"")+'" onclick="setMode(\''+p[0]+'\')">'+p[1]+'</div>').join("");
  document.getElementById("vd").textContent=periodLabel();
  const vis=mode==="all"?"hidden":"visible";
  document.getElementById("prev").style.visibility=vis;document.getElementById("next").style.visibility=vis;
  const list=inRange().sort((a,b)=>a.start-b.start);
  const total=list.reduce((s,e)=>s+e.dur,0);
  document.getElementById("totlbl").textContent=L.totlbl[mode];
  document.getElementById("tot").textContent=fdur(total);
  renderList(list);renderChart();renderCmp();
}
function renderList(list){
  const lb=document.getElementById("list");
  if(!list.length){lb.innerHTML='<div class="empty">'+L.noRecords+'</div>';return;}
  if(mode==="day"||mode==="week"){
    lb.innerHTML=list.map(e=>'<div class="entry"><span class="dot" style="background:'+col()+'"></span><div class="meta"><div class="nm">'+esc(e.name)+'</div><div class="tm">'+(mode==="week"?md(e.start)+" ":"")+tod(e.start)+'~'+tod(e.end)+'</div></div><div class="dur">'+fdur(e.dur)+'</div></div>').join("");
  }else{
    const agg={};list.forEach(e=>{const k=e.name;(agg[k]=agg[k]||{name:e.name,sec:0,n:0});agg[k].sec+=e.dur;agg[k].n++;});
    lb.innerHTML=Object.values(agg).sort((a,b)=>b.sec-a.sec).map(a=>'<div class="entry"><span class="dot" style="background:'+col()+'"></span><div class="meta"><div class="nm">'+esc(a.name)+'</div><div class="tm">'+a.n+L.count+'</div></div><div class="dur">'+fdur(a.sec)+'</div></div>').join("");
  }
}
function renderChart(){
  const w=document.getElementById("week"),lbl=document.getElementById("chartlbl"),now=new Date();let b=[];
  if(mode==="day"){lbl.textContent=L.last7;
    for(let i=6;i>=0;i--){const d=new Date(anchor);d.setDate(d.getDate()-i);const s=sec(midnight(d));b.push({l:DOW[d.getDay()],s,e:s+86400,hl:midnight(d).getTime()===midnight(now).getTime()});}}
  else if(mode==="week"){lbl.textContent=L.byWeekday;const ws=weekStart(anchor);
    for(let i=0;i<7;i++){const d=new Date(ws);d.setDate(d.getDate()+i);const s=sec(midnight(d));b.push({l:DOW[d.getDay()],s,e:s+86400,hl:midnight(d).getTime()===midnight(now).getTime()});}}
  else if(mode==="month"){lbl.textContent=L.byDay;const y=anchor.getFullYear(),m=anchor.getMonth(),last=new Date(y,m+1,0).getDate();
    for(let day=1;day<=last;day++){const d=new Date(y,m,day),s=sec(d);b.push({l:String(day),s,e:s+86400,hl:midnight(now).getTime()===d.getTime(),sm:1});}}
  else if(mode==="year"){lbl.textContent=L.byMonth;const y=anchor.getFullYear();
    for(let mo=0;mo<12;mo++){b.push({l:MON[mo],s:sec(new Date(y,mo,1)),e:sec(new Date(y,mo+1,1)),hl:now.getFullYear()===y&&now.getMonth()===mo,sm:1});}}
  else{lbl.textContent=L.last12;
    for(let i=11;i>=0;i--){const d=new Date(now.getFullYear(),now.getMonth()-i,1);b.push({l:MON[d.getMonth()],s:sec(d),e:sec(new Date(d.getFullYear(),d.getMonth()+1,1)),hl:i===0,sm:1});}}
  b.forEach(x=>x.sec=bucketSum(x.s,x.e));
  const max=Math.max(1,...b.map(x=>x.sec));
  w.innerHTML=b.map(x=>'<div class="col"><div class="val">'+(x.sec>0?(Math.round(x.sec/360)/10)+"h":"")+'</div><div class="barwrap"><div class="b'+(x.hl?" today":"")+'" style="height:'+Math.round(x.sec/max*100)+'%"></div></div><div class="lbl"'+(x.sm?' style="font-size:9px"':'')+'>'+x.l+'</div></div>').join("");
}
function renderCmp(){
  const box=document.getElementById("cmp"),tasks=DB.tasks||[];
  document.getElementById("cmplbl").textContent=L.estVsActualTotal;
  if(!tasks.length){box.innerHTML='<div class="empty">'+L.noTasks+'</div>';return;}
  const actBy={};DB.entries.forEach(e=>{actBy[e.name]=(actBy[e.name]||0)+e.dur;});
  if(DB.active){const r=Math.max(0,Date.now()/1000-DB.active.start);actBy[DB.active.name]=(actBy[DB.active.name]||0)+r;}
  const rows=tasks.map(t=>({t,act:actBy[t.name]||0})).filter(r=>r.act>0||(r.t.est||0)>0)
    .sort((a,b)=>(a.t.done?1:0)-(b.t.done?1:0)||b.act-a.act);
  if(!rows.length){box.innerHTML='<div class="empty">'+L.noRecordsYet+'</div>';return;}
  box.innerHTML=rows.map(({t,act})=>{
    const est=(t.est||0)*60;let right,fillW,fillC;
    const nm=(t.done?'['+L.done+'] ':'')+esc(t.name);
    if(est>0){const pct=Math.round(act/est*100),over=act>est,diff=Math.abs(act-est);
      right=L.actual+' '+fdur(act)+' / '+L.est+' '+fdur(est)+'  <b style="color:'+(over?"#ef4444":"#22c55e")+'">'+pct+'%</b>'+(act>0?' ('+(over?"+":"-")+fdur(diff)+')':'');
      fillW=Math.min(100,pct);fillC=over?"#ef4444":"#22c55e";}
    else{right=L.actual+' '+fdur(act)+' - <span style="color:var(--sub)">'+L.noEstimate+'</span>';fillW=act>0?100:0;fillC=col();}
    return '<div class="catstat"><div class="top"><span><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:'+col()+';margin-right:6px"></span>'+nm+'</span><span style="color:var(--sub)">'+right+'</span></div><div class="bar"><div class="fill" style="width:'+fillW+'%;background:'+fillC+'"></div></div></div>';
  }).join("");
}
render();
</script></body></html>"""
