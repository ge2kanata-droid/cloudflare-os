/* Hitomazu task board v0.1 — all task data is browser-local. No network writes or AI inference. */
"use strict";
const STORAGE_KEY = "hitomazu-control-v1";
const STATUSES = {todo:"未着手",doing:"進行中",review:"確認待ち",done:"完了",paused:"保留"};
const PRIORITIES = {high:"高",normal:"通常",low:"低"};
const STARTER_TASKS = [
  {title:"既存note販売導線の監査（候補）",description:"Notion・担当AI・公開済み記事を先に照合。購入導線や説明文の改善余地を確認し、既存商品は勝手に上書きしない。未照合の候補タスク。",owner:"未割当",status:"todo",priority:"high",url:"",due:""},
  {title:"公式HPから商品へのリンク点検（候補）",description:"公式HPの公開ページから既存商品のリンクと案内文を確認。差分を報告し、外部公開は承認待ちにする。未照合の候補タスク。",owner:"未割当",status:"todo",priority:"high",url:"https://hitomazu-tools-home.pages.dev/",due:""},
  {title:"既存素材を使った販促案の整理（候補）",description:"新規大量制作より、既存動画・画像・文章の使い回しと効果測定を優先。SNS予約や公開は既存担当と重複しないこと。未照合の候補タスク。",owner:"未割当",status:"todo",priority:"normal",url:"",due:""}
];
const $ = id => document.getElementById(id);
const safeUrl = raw => {try{const u = new URL(raw);return ["https:","http:"].includes(u.protocol)?u.href:"";}catch{return "";}};
const clean = (v,max=200) => String(v??"").slice(0,max);
const isDate = v => /^\d{4}-\d{2}-\d{2}$/.test(v||"");
const uid = () => (typeof crypto !== "undefined" && crypto.randomUUID)?crypto.randomUUID():String(Date.now())+Math.random().toString(16).slice(2);
function normalizedTask(raw){
 if(!raw || typeof raw!=="object" || !clean(raw.title,120).trim()) return null;
 return {id:clean(raw.id,100)||uid(),title:clean(raw.title,120).trim(),description:clean(raw.description,1500),owner:clean(raw.owner,80)||"未割当",status:STATUSES[raw.status]?raw.status:"todo",priority:PRIORITIES[raw.priority]?raw.priority:"normal",url:safeUrl(raw.url||""),due:isDate(raw.due)?raw.due:""};
}
function initialState(){return {version:1,tasks:STARTER_TASKS.map(t=>normalizedTask({...t,id:uid()})),metrics:{sales:null,orders:null,note:""}};}
function loadState(){
 try{const str=localStorage.getItem(STORAGE_KEY);if(!str)return initialState();const data=JSON.parse(str);
 if(data.version!==1||!Array.isArray(data.tasks))throw Error("bad format");
 return {version:1,tasks:data.tasks.slice(0,500).map(normalizedTask).filter(Boolean),metrics:normalizedMetrics(data.metrics)};
 }catch(e){console.warn("タスクデータを読み込めませんでした",e);return initialState();}
}
const checkedNumber = v => v===null||v===""||v===undefined?null:(Number.isSafeInteger(Number(v))&&Number(v)>=0?Number(v):null);
function normalizedMetrics(m){return {sales:checkedNumber(m?.sales),orders:checkedNumber(m?.orders),note:clean(m?.note,180)};}
let state=loadState();
let toastTimeout;
function toast(message){const node=$("toast");node.textContent=message;node.hidden=false;clearTimeout(toastTimeout);toastTimeout=setTimeout(()=>node.hidden=true,3500);}
function persist(){
 try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));return true;}
 catch(e){console.warn("保存不可",e);toast("このブラウザへの保存に失敗しました。JSONを書き出してください。");return false;}
}
function el(tag,cls,txt){const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n;}
function render(){
 $("total").textContent=state.tasks.length;
 $("running").textContent=state.tasks.filter(t=>t.status==="doing").length;
 $("review").textContent=state.tasks.filter(t=>t.status==="review").length;
 $("done").textContent=state.tasks.filter(t=>t.status==="done").length;
 const owner=$("ownerFilter"), prev=owner.value;
 owner.replaceChildren(new Option("すべて",""));
 [...new Set(state.tasks.map(t=>t.owner))].sort().forEach(v=>owner.add(new Option(v,v)));
 if([...owner.options].some(x=>x.value===prev))owner.value=prev;
 const filtered=state.tasks.filter(t=>(!$("statusFilter").value||t.status===$("statusFilter").value)&&(!owner.value||t.owner===owner.value));
 const host=$("tasks");host.replaceChildren();$("emptyTasks").hidden=filtered.length!==0;
 filtered.forEach(t=>{
  const card=el("article","task"); const top=el("div","task-top"),heading=el("h3","",t.title);top.append(heading);
  const desc=el("p","",t.description||"説明なし");
  const tags=el("div","task-meta");
  [STATUSES[t.status],t.owner,"優先度："+PRIORITIES[t.priority],t.due?"期日："+t.due:""].filter(Boolean).forEach((value,i)=>tags.append(el("span","tag "+(i===0?t.status:i===2?t.priority:""),value)));
  const actions=el("div","task-actions");
  const edit=el("button","secondary","編集");edit.type="button";edit.addEventListener("click",()=>showDialog(t));
  const copy=el("button","secondary","AI依頼文をコピー");copy.type="button";copy.addEventListener("click",()=>copyPrompt(t));
  const next=el("button","secondary",t.status==="done"?"未着手に戻す":"次の状態へ");next.type="button";next.addEventListener("click",()=>{const order=["todo","doing","review","done"];t.status=t.status==="paused"?"todo":order[(order.indexOf(t.status)+1)%order.length];persist();render();});
  const del=el("button","secondary","削除");del.type="button";del.addEventListener("click",()=>{if(confirm("この端末からタスク「"+t.title+"」を削除しますか？")){state.tasks=state.tasks.filter(x=>x.id!==t.id);persist();render();}});
  actions.append(edit,copy,next,del);
  if(t.url){const link=el("a","","関連ページ ↗");link.href=t.url;link.target="_blank";link.rel="noopener noreferrer";actions.append(link);}
  card.append(top,tags,desc,actions);host.append(card);
 });
 $("sales").value=state.metrics.sales??"";
 $("orders").value=state.metrics.orders??"";
 $("metricNote").value=state.metrics.note;
}
function showDialog(t=null){
 $("dialogTitle").textContent=t?"タスク編集":"タスク追加";
 $("taskId").value=t?.id||"";$("taskTitle").value=t?.title||"";$("taskDescription").value=t?.description||"";
 $("taskOwner").value=t?.owner||"";$("taskPriority").value=t?.priority||"normal";
 $("taskStatus").value=t?.status||"todo";$("taskDue").value=t?.due||"";$("taskUrl").value=t?.url||"";
 $("taskDialog").showModal();
}
function buildPrompt(t){
 return ["【ひとまず道具店｜AI実務依頼】","案件："+t.title,"担当："+t.owner,"優先度："+PRIORITIES[t.priority],"状態："+STATUSES[t.status],"成果条件："+(t.description||"作業前に定義する"),t.url?"参照URL："+t.url:"",t.due?"期日："+t.due:"",
 "制約：追加課金禁止。既存担当・Notion台帳・公開実績を先に照合し、重複を防止。中の人の個人活動と世界線記録局は対象外。購入・契約・広告出稿・外部公開・既存商品上書きは事前承認。確認できない数値を0扱いしない。",
 "まず実行可能な非破壊作業を進め、実施結果・未実施事項・検証方法を報告してください。"].filter(Boolean).join("\n");
}
async function copyPrompt(t){
 const message=buildPrompt(t);
 try{await navigator.clipboard.writeText(message);toast("AI依頼文をコピーしました");}
 catch{window.prompt("この文章をコピーしてください",message);}
}
function saveTask(ev){
 ev.preventDefault();
 const title=$("taskTitle").value.trim();if(!title){$("taskTitle").reportValidity();return;}
 const urlText=$("taskUrl").value.trim();if(urlText&&!safeUrl(urlText)){toast("http または https のURLのみ使用可能です");return;}
 const id=$("taskId").value;
 const item=normalizedTask({id:id||uid(),title,description:$("taskDescription").value,owner:$("taskOwner").value||"未割当",priority:$("taskPriority").value,status:$("taskStatus").value,url:urlText,due:$("taskDue").value});
 if(!item)return;
 if(id){const index=state.tasks.findIndex(t=>t.id===id);if(index>=0)state.tasks[index]=item;else state.tasks.push(item);}
 else state.tasks.unshift(item);
 persist();$("taskDialog").close();render();toast("タスクを保存しました");
}
function saveMetrics(){
 state.metrics=normalizedMetrics({sales:$("sales").value,orders:$("orders").value,note:$("metricNote").value});
 if(($("sales").value!==""&&state.metrics.sales===null)||($("orders").value!==""&&state.metrics.orders===null)){toast("件数・金額は0以上の整数で入力してください");return;}
 persist();$("metricsSaved").textContent="記録： "+(state.metrics.note||"日時・媒体未指定")+" / 売上 "+(state.metrics.sales===null?"未確認":state.metrics.sales.toLocaleString()+"円")+" / 注文 "+(state.metrics.orders===null?"未確認":state.metrics.orders+"件");
 toast("実績を端末内に保存しました");
}
function exportJson(){
 const blob=new Blob([JSON.stringify({...state,exportedAt:new Date().toISOString()},null,2)],{type:"application/json;charset=utf-8"});
 const url=URL.createObjectURL(blob),a=document.createElement("a");
 a.href=url;a.download="hitomazu-tasks-"+new Date().toISOString().slice(0,10)+".json";document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500);toast("JSONをダウンロードしました");
}
async function importJson(ev){
 const file=ev.target.files?.[0];ev.target.value="";if(!file)return;
 if(file.size>2000000){toast("2MB以下のJSONを選んでください");return;}
 try{const raw=JSON.parse(await file.text());if(raw.version!==1||!Array.isArray(raw.tasks)||raw.tasks.length>500)throw Error("形式");
 const tasks=raw.tasks.map(normalizedTask);if(tasks.some(t=>!t))throw Error("不正なタスク");
 const ids=new Set(tasks.map(t=>t.id));if(ids.size!==tasks.length)throw Error("タスクIDが重複");
 if(!confirm("この端末の現在のデータをJSONの内容で置き換えます。続行しますか？"))return;
 state={version:1,tasks,metrics:normalizedMetrics(raw.metrics)};
 $("statusFilter").value="";$("ownerFilter").value="";persist();render();toast("データを読み込みました");
 }catch(err){toast("読み込み失敗：有効な業務本部JSONを選択してください");}
}
async function loadSiteStatus(){
 const host=$("siteChecks");
 try{const response=await fetch("./site-status.json",{cache:"no-store"});if(!response.ok)throw Error("未取得");
 const report=await response.json();if(!Array.isArray(report.checks))throw Error("不正");
 host.replaceChildren(el("div","muted","確認時刻： "+String(report.checked_at||"不明")));
 report.checks.forEach(c=>{
 const row=el("div","check");const line=el("div","",clean(c.name,100)+" — "+(c.result==="reachable"?"応答あり":"要確認"));
 line.className=c.result==="reachable"?"status-good":"status-unknown";
 row.append(line,el("div","muted","HTTP "+(c.http_status??"取得不可")+" / "+clean(c.note,180))); if(c.sales_links){row.append(el("div","muted","トップページの直接リンク数：note "+(c.sales_links["note.com"]??"?")+" / SUZURI "+(c.sales_links["suzuri.jp"]??"?")));}if(Array.isArray(c.findings))c.findings.forEach(s=>row.append(el("div","status-unknown",clean(s,300))));host.append(row);
 });
 }catch{host.textContent="未取得：自動点検の設定または実行がまだ完了していません。";}
}

async function loadFunnelStatus(){
 const summary=$("funnelSummary"), findings=$("funnelFindings");
 summary.textContent="監査結果を読み込み中…";findings.replaceChildren();
 try{
  const response=await fetch("./funnel-status.json",{cache:"no-store"});
  if(!response.ok)throw Error("not found");
  const report=await response.json();
  if(report.schema!==1||!report.summary||!Array.isArray(report.findings)||!Array.isArray(report.note_checks))throw Error("bad format");
  summary.replaceChildren();
  const date=el("p","muted","最終監査："+clean(report.checked_at,45));
  const counts=el("div","audit-counts");
  counts.append(el("span","tag done","正常確認 "+(report.summary.verified_ok??"?")+"件"));
  counts.append(el("span","tag review","要確認 "+(report.summary.needs_review??"?")+"件"));
  counts.append(el("span","tag","判定不能 "+(report.summary.unknown??"?")+"件"));
  summary.append(date,counts);
  const store=Array.isArray(report.sites)?report.sites.find(s=>s.url==="https://hitomazu-tools-home.pages.dev/"):null;
  if(store && store.link_inventory){
   const inventory=store.link_inventory;
   const outer=el("div","audit-row");
   outer.append(el("strong","","公式HPトップの販売リンク構成（HTML内）"));
   outer.append(el("div","muted","note個別記事 "+(inventory.note_article??"?")+" / noteプロフィール "+(inventory.note_profile??"?")+
    " / SUZURI個別商品 "+(inventory.suzuri_product??"?")+" / 店舗トップ "+(inventory.suzuri_storefront??"?")+
    " / 商品一覧 "+(inventory.suzuri_category??"?")));
   outer.append(el("div","muted","001有料noteへの直接リンク："+(store.direct_paid_note_001??"未確認")+"件。ページ内遷移・売上実績とは異なります。"));
   if(store.link_advisory)outer.append(el("div","status-unknown",clean(store.link_advisory,350)));
   summary.append(outer);
  }
  for(const c of report.note_checks.slice(0,8)){
   const row=el("div","audit-row");
   const status=c.status==="ok"?"正常確認":c.status==="needs_review"?"リンク要確認":"判定不能";
   row.append(el("strong","",clean(c.name,100)+"： "+status),el("div","muted",clean(c.evidence,220)));
   findings.append(row);
  }
  if(!report.findings.length){
   findings.append(el("p","muted","今回の取得内容では新たな修正候補を検出していません。判定不能の場合は正常と断定できません。"));
  }else{
   const label=el("h3","","既存担当への改善候補");findings.append(label);
   for(const finding of report.findings.slice(0,12)){
    const row=el("div","audit-finding");
    row.append(el("strong","",clean(finding.title,200)),el("p","muted",clean(finding.details,300)));
    row.append(el("div","muted","担当："+clean(finding.owner,100)));
    const actions=el("div","task-actions");
    const copy=el("button","secondary","既存担当への依頼文をコピー");
    copy.addEventListener("click",()=>copyPrompt({
     title:clean(finding.title,120),owner:clean(finding.owner,80),
     priority:finding.severity==="high"?"high":"normal",
     status:"review",description:clean(finding.details,450)+"\n"+clean(finding.action,500),
     url:safeUrl(finding.url),due:""
    }));
    actions.append(copy);
    const link=safeUrl(finding.url);
    if(link){const a=el("a","","公開ページ ↗");a.href=link;a.target="_blank";a.rel="noopener noreferrer";actions.append(a);}
    row.append(actions);findings.append(row);
   }
  }
  findings.append(el("p","muted","監査は定期実行されますが、指摘の修正・外部公開は既存担当の承認フローに従います。"));
 }catch(e){
  summary.textContent="監査結果は未取得です。次のGitHub Actions実行後に反映されます。";
  findings.replaceChildren();
 }
}

$("newBtn").addEventListener("click",()=>showDialog());
$("cancelTask").addEventListener("click",()=>$("taskDialog").close());
$("taskForm").addEventListener("submit",saveTask);
$("statusFilter").addEventListener("change",render);
$("ownerFilter").addEventListener("change",render);
$("saveMetrics").addEventListener("click",saveMetrics);
$("exportBtn").addEventListener("click",exportJson);
$("importInput").addEventListener("change",importJson);
$("refreshChecks").addEventListener("click",loadSiteStatus);
$("refreshFunnel").addEventListener("click",loadFunnelStatus);
render();loadSiteStatus();loadFunnelStatus();