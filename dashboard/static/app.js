const $=s=>document.querySelector(s);const $$=s=>[...document.querySelectorAll(s)];
const names={overview:"Übersicht",tasks:"Aufgaben",agents:"Agenten",commands:"Kommandozentrale",activity:"Aktivitäten",security:"Sicherheit",settings:"Einstellungen"};
let tasks=[];let toastTimer;
function toast(msg){const el=$("#toast");el.textContent=msg;el.classList.add("show");clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove("show"),2600)}
function esc(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function statusName(s){return({queued:"Warteschlange",in_progress:"In Bearbeitung",blocked:"Blockiert",completed:"Abgeschlossen",failed:"Fehlgeschlagen",cancelled:"Abgebrochen"})[s]||s}
async function api(path,opts={}){const res=await fetch(path,{...opts,headers:{"Content-Type":"application/json",...(opts.headers||{})}});const data=await res.json().catch(()=>({error:"Ungültige Serverantwort"}));if(!res.ok)throw Error(data.error||"Anfrage fehlgeschlagen");return data}
function taskMarkup(t){return '<div class="task-row"><div><div class="task-title">'+esc(t.title)+'</div><div class="task-meta">Priorität '+t.priority+' · '+new Date(t.created_at).toLocaleString('de-DE')+'</div></div><span class="task-badge '+esc(t.status)+'">'+esc(statusName(t.status))+'</span><div class="task-controls"><select aria-label="Status ändern" data-task="'+esc(t.id)+'"><option value="">Status ändern …</option>'+["queued","in_progress","blocked","completed","failed","cancelled"].map(s=>'<option value="'+s+'">'+statusName(s)+'</option>').join("")+'</select></div></div>'}
function renderTasks(){const filtered=tasks.filter(t=>!$("#task-filter")?.value||t.status===$("#task-filter").value);$("#task-count").textContent=tasks.length;$("#task-total-label").textContent=filtered.length+" Einträge";$("#all-tasks").innerHTML=filtered.length?filtered.map(taskMarkup).join(""):'<div class="empty">Keine Aufgaben in diesem Filter.</div>';$("#recent-tasks").innerHTML=tasks.length?tasks.slice(0,5).map(taskMarkup).join(""):'<div class="empty">Noch keine Aufgaben vorhanden.</div>';const counts={total:tasks.length,progress:tasks.filter(t=>t.status==="in_progress").length,queued:tasks.filter(t=>t.status==="queued").length,done:tasks.filter(t=>t.status==="completed").length};$("#stat-total").textContent=counts.total;$("#stat-progress").textContent=counts.progress;$("#stat-queued").textContent=counts.queued;$("#stat-done").textContent=counts.done;renderActivity()}
async function renderActivity(){const list=$("#activity-list");const recent=tasks.slice().sort((a,b)=>b.updated_at.localeCompare(a.updated_at)).slice(0,20);if(!recent.length){list.innerHTML='<div class="empty">Noch keine Aktivitäten vorhanden.</div>';return}list.innerHTML='<div class="empty">Ereignisverlauf wird geladen …</div>';const results=await Promise.allSettled(recent.map(async task=>{const data=await api("/api/tasks/"+encodeURIComponent(task.id)+"/history");return data.events.map(event=>({...event,title:task.title}))}));const events=results.filter(result=>result.status==="fulfilled").flatMap(result=>result.value).sort((a,b)=>b.created_at.localeCompare(a.created_at)).slice(0,50);if(!events.length){list.innerHTML='<div class="empty">Keine gespeicherten Ereignisse gefunden.</div>';return}list.innerHTML=events.map(event=>'<div class="activity-item"><b>'+esc(event.title)+'</b> · '+esc(event.old_status?statusName(event.old_status)+" → ":"")+esc(statusName(event.new_status))+'<small>'+esc(event.note||"Statusereignis")+' · '+new Date(event.created_at).toLocaleString("de-DE")+'</small></div>').join("");}
async function refreshDiagnostics(){
  const button=$('[data-command="diagnostics-refresh"]');
  if(button){button.disabled=true;button.textContent="Prüfung läuft …"}
  const set=(id,value)=>{const el=$("#"+id);if(el)el.textContent=value};
  try{
    const results=await Promise.allSettled([api("/api/system"),api("/api/agent-status")]);
    const system=results[0].status==="fulfilled"?results[0].value:null;
    const agent=results[1].status==="fulfilled"?results[1].value:null;
    set("diag-platform",system?system.platform+" "+system.release:"Nicht verfügbar");
    set("diag-python",system?system.python:"Nicht verfügbar");
    set("diag-memory",system&&system.memory?fmtBytes(system.memory.total_bytes-system.memory.available_bytes)+" / "+fmtBytes(system.memory.total_bytes):"Nicht verfügbar");
    set("diag-disk",system?fmtBytes(system.disk.free_bytes)+" frei ("+system.disk.used_percent+"% belegt)":"Nicht verfügbar");
    set("diag-agent",agent?(agent.available?"Erreichbar":"Nicht erreichbar"):"Prüfung fehlgeschlagen");
    set("diag-endpoint",agent?agent.endpoint||"Konfiguriert":"Nicht verfügbar");
    set("diag-updated","Letzte Prüfung: "+new Date().toLocaleString("de-DE")+" · Nur lesende lokale Statusabfragen");
    if(!system&&!agent)toast("Systemdiagnose konnte nicht geladen werden");
  }finally{if(button){button.disabled=false;button.textContent="Diagnose starten"}}
}
async function refreshBackups(){
  const list=$("#backup-list");
  if(!list)return;
  list.textContent="Sicherungen werden geladen …";
  try{
    const data=await api("/api/backups");
    if(!data.backups.length){list.innerHTML='<div class="empty">Noch keine Backups vorhanden.</div>';return}
    list.innerHTML=data.backups.map(item=>'<div class="backup-row"><div><b>'+esc(item.filename)+'</b><small>'+new Date(item.modified_at).toLocaleString("de-DE")+'</small></div><span>'+fmtBytes(item.size)+'</span></div>').join("");
  }catch(err){list.innerHTML='<div class="empty">Backup-Verlauf nicht verfügbar: '+esc(err.message)+'</div>'}
}
function fmtBytes(n){if(n===null||n===undefined)return "Nicht verfügbar";const u=["B","KB","MB","GB","TB"];let i=0;while(n>=1024&&i<u.length-1){n/=1024;i++}return n.toFixed(i?1:0)+" "+u[i]}
function fmtDuration(n){if(n===null||n===undefined)return "Nicht verfügbar";const d=Math.floor(n/86400),h=Math.floor(n%86400/3600),m=Math.floor(n%3600/60);return (d?d+" T ":"")+h+" Std. "+m+" Min."}
async function refreshAgentModels(){
  const list=$("#agent-model-list"),note=$("#agent-model-note");
  if(!list)return;
  list.textContent="Modellliste wird geprüft …";
  try{
    const data=await api("/api/agent-models");
    if(!data.available){list.innerHTML='<div class="empty">Ollama ist nicht erreichbar.</div>';const selector=$("#inference-model");if(selector)selector.innerHTML='<option value="">Ollama nicht erreichbar</option>';return}
    if(!data.models.length){list.innerHTML='<div class="empty">'+esc(data.error||"Keine installierten Modelle gefunden.")+'</div>';const selector=$("#inference-model");if(selector)selector.innerHTML='<option value="">Keine Modelle installiert</option>';return}
    list.innerHTML=data.models.map(model=>'<div class="agent-model-row"><div><b>'+esc(model.name)+'</b><small>'+esc(model.modified_at?new Date(model.modified_at).toLocaleDateString("de-DE"):"Änderungsdatum unbekannt")+'</small></div><span>'+fmtBytes(model.size)+'</span></div>').join("");
    const selector=$("#inference-model");
    if(selector){const previous=selector.value;selector.innerHTML=data.models.map(model=>'<option value="'+esc(model.name)+'">'+esc(model.name)+'</option>').join("");if(data.models.some(model=>model.name===previous))selector.value=previous;}
    if(note)note.textContent=data.models.length+" Modell(e) gefunden · Nur Metadaten gelesen";
  }catch(err){list.innerHTML='<div class="empty">Modellliste nicht verfügbar: '+esc(err.message)+'</div>'}
}
function approvalStatus(status){return ({pending:"WARTET AUF FREIGABE",approved:"FREIGEGEBEN · NOCH NICHT AUSGEFÜHRT",rejected:"ABGELEHNT",expired:"ABGELAUFEN",consumed:"VERBRAUCHT"})[status]||status}
async function refreshApprovals(){
  const list=$("#approval-list");if(!list)return;
  list.textContent="Freigaben werden geladen …";
  try{
    const data=await api("/api/approvals");
    if(!data.approvals.length){list.innerHTML='<div class="empty">Keine Freigaben vorhanden.</div>';return}
    list.innerHTML=data.approvals.map(item=>{
      const payload=item.payload||{};
      const details=payload.title?"Aufgabe: "+payload.title:"";
      const controls=item.status==="pending"
        ?'<button class="subtle-button" data-approval-decision="approve" data-approval-id="'+esc(item.request_id)+'">Freigeben</button><button class="subtle-button danger-button" data-approval-decision="reject" data-approval-id="'+esc(item.request_id)+'">Ablehnen</button>'
        :item.status==="approved"
          ?'<button class="primary-button" data-approval-execute data-approval-id="'+esc(item.request_id)+'">Jetzt ausführen</button>'
          :"";
      return '<div class="approval-row"><div class="approval-copy"><b>'+esc(item.action)+'</b><small>'+esc(details)+' · läuft ab '+new Date(item.expires_at*1000).toLocaleTimeString("de-DE")+'</small><span class="approval-status '+esc(item.status)+'">'+esc(approvalStatus(item.status))+'</span></div><div class="approval-controls">'+controls+'</div></div>';
    }).join("");
  }catch(err){list.innerHTML='<div class="empty">Freigaben nicht verfügbar: '+esc(err.message)+'</div>'}
}
async function refreshExecutions(){
  const list=$("#execution-list");if(!list)return;
  try{
    const data=await api("/api/agent-executions");
    if(!data.executions.length){list.innerHTML='<div class="empty">Noch keine Agentenausführungen.</div>';return}
    list.innerHTML=data.executions.map(item=>'<div class="execution-row"><div><b>'+esc(item.agent)+'</b><small>'+new Date(item.created_at*1000).toLocaleString("de-DE")+'</small></div><span class="approval-status '+esc(item.status)+'">'+esc(item.status==="completed"?"ERFOLGREICH":item.status==="failed"?"FEHLGESCHLAGEN":item.status.toUpperCase())+'</span></div>').join("");
  }catch(err){list.innerHTML='<div class="empty">Ausführungsverlauf nicht verfügbar: '+esc(err.message)+'</div>'}
}
async function refreshControlledAgents(){await Promise.all([refreshApprovals(),refreshExecutions()])}
async function refreshAgentStatus(){const state=$("#ollama-state"),detail=$("#ollama-detail"),button=$('[data-command="agent-refresh"]');if(!state||!detail)return;if(button){button.disabled=true;button.textContent="Prüfe Verbindung …"}try{const d=await api("/api/agent-status");state.textContent=d.available?"ERREICHBAR":"NICHT ERREICHBAR";state.classList.toggle("online",d.available);detail.textContent=d.available?"Ollama-Version "+(d.version||"unbekannt")+" · "+d.endpoint:"Nicht erreichbar · "+d.endpoint}catch(e){state.textContent="STATUS UNBEKANNT";state.classList.remove("online");detail.textContent="Dashboard-Server nicht erreichbar"}finally{if(button){button.disabled=false;button.textContent="Verbindung prüfen"}}}
async function refreshSystem(){try{const d=await api("/api/system"),m=d.memory;$("#memory-value").textContent=m?m.used_percent+"%":"Nicht verfügbar";$("#memory-bar").style.width=m?m.used_percent+"%":"0%";$("#memory-detail").textContent=m?fmtBytes(m.total_bytes-m.available_bytes)+" von "+fmtBytes(m.total_bytes)+" belegt":"Auf diesem System nicht verfügbar";$("#disk-value").textContent=d.disk.used_percent+"%";$("#disk-bar").style.width=d.disk.used_percent+"%";$("#disk-detail").textContent=fmtBytes(d.disk.free_bytes)+" frei · Home-Speicher";$("#load-value").textContent=d.load_average?d.load_average.map(v=>v.toFixed(2)).join(" / "):"Nicht verfügbar";$("#uptime-value").textContent=fmtDuration(d.uptime_seconds);$("#host-detail").textContent=d.platform+" "+d.release+" · Python "+d.python;$("#telemetry-state").textContent="LIVE"}catch(e){$("#telemetry-state").textContent="OFFLINE"}}
async function refresh(){try{const data=await api("/api/status");tasks=data.tasks;renderTasks();$("#system-title").textContent="NClaw Dashboard verbunden";$("#system-detail").textContent="Lokale Task Engine erreichbar · "+data.runtime+" · "+data.storage;$("#system-tag").textContent="VERBUNDEN";$("#footer-status").textContent="API verbunden · "+new Date().toLocaleTimeString("de-DE");}catch(e){$("#system-title").textContent="Dashboard-Server nicht erreichbar";$("#system-detail").textContent="Starte das Dashboard mit: python -m dashboard.server";$("#system-tag").textContent="OFFLINE";$("#footer-status").textContent="Keine lokale Verbindung";toast(e.message)}refreshSystem()}
function navigate(page){if(!names[page])page="overview";$$(".page").forEach(p=>p.classList.toggle("active",p.id==="page-"+page));$$(".nav-link").forEach(a=>a.classList.toggle("active",a.dataset.page===page));$("#page-crumb").textContent=names[page];location.hash=page;$("#sidebar").classList.remove("open");if(page==="commands"){refreshBackups();refreshControlledAgents()}if(page==="agents")refreshAgentModels()}
function openDialog(){$("#task-dialog").showModal();$("#title").focus()}
$("#agent-action-form").addEventListener("submit",async e=>{
  e.preventDefault();const button=e.target.querySelector('button[type="submit"]');button.disabled=true;
  const payload={title:$("#agent-task-title").value,description:$("#agent-task-description").value,priority:Number($("#agent-task-priority").value)};
  try{const result=await api("/api/agent-actions/propose",{method:"POST",body:JSON.stringify({agent:"task-assistant",payload})});toast("Freigabe angelegt · "+result.approval.request_id);e.target.reset();$("#agent-task-priority").value="3";await refreshControlledAgents();}
  catch(err){toast("Freigabe konnte nicht angelegt werden: "+err.message)}
  finally{button.disabled=false}
});
$("#inference-form").addEventListener("submit",async e=>{
  e.preventDefault();const button=e.target.querySelector('button[type="submit"]'),output=$("#inference-output");button.disabled=true;button.textContent="Modell antwortet …";output.textContent="Inferenz läuft. Das Modell erhält nur den Prompt; es werden keine Agentenaktionen gestartet.";
  try{const result=await api("/api/inference",{method:"POST",body:JSON.stringify({model:$("#inference-model").value,prompt:$("#inference-prompt").value})});output.textContent=result.answer;toast("Modell-Inferenz abgeschlossen");}
  catch(err){output.textContent="Inferenz fehlgeschlagen: "+err.message;toast(err.message)}
  finally{button.disabled=false;button.textContent="Modell jetzt ausführen"}
});
$("#task-form").addEventListener("submit",async e=>{e.preventDefault();const body={title:$("#title").value,description:$("#description").value,priority:Number($("#priority").value)};try{await api("/api/tasks",{method:"POST",body:JSON.stringify(body)});$("#task-dialog").close();e.target.reset();$("#priority").value="3";await refresh();toast("Aufgabe lokal gespeichert")}catch(err){toast(err.message)}});
$("#close-dialog").onclick=$("#cancel-dialog").onclick=()=>$("#task-dialog").close();
$("#new-task").onclick=openDialog;$("#refresh").onclick=refresh;$("#task-filter").onchange=renderTasks;$("#menu-toggle").onclick=()=>$("#sidebar").classList.toggle("open");
document.addEventListener("click",async e=>{const link=e.target.closest("[data-page]");if(link){e.preventDefault();navigate(link.dataset.page)}const go=e.target.closest("[data-go]");if(go)navigate(go.dataset.go);const decision=e.target.closest("[data-approval-decision]");if(decision){decision.disabled=true;try{await api("/api/approvals/"+encodeURIComponent(decision.dataset.approvalId)+"/decision",{method:"POST",body:JSON.stringify({decision:decision.dataset.approvalDecision})});toast(decision.dataset.approvalDecision==="approve"?"Aktion freigegeben · noch nicht ausgeführt":"Aktion abgelehnt");await refreshControlledAgents()}catch(err){toast(err.message);decision.disabled=false}}
const execute=e.target.closest("[data-approval-execute]");if(execute){execute.disabled=true;execute.textContent="Ausführung läuft …";try{const result=await api("/api/agent-executions",{method:"POST",body:JSON.stringify({approval_id:execute.dataset.approvalId,agent:"task-assistant"})});toast("Agentenaktion erfolgreich ausgeführt");await refresh();await refreshControlledAgents()}catch(err){toast("Ausführung fehlgeschlagen: "+err.message);await refreshControlledAgents()}}
const cmd=e.target.closest("[data-command]");if(cmd){if(cmd.dataset.command==="create")openDialog();else if(cmd.dataset.command==="approvals-refresh"||cmd.dataset.command==="executions-refresh"){refreshControlledAgents()}else if(cmd.dataset.command==="backup"){cmd.disabled=true;const label=cmd.querySelector("b");const oldLabel=label.textContent;label.textContent="Sicherung läuft …";try{const result=await api("/api/backup",{method:"POST",body:"{}"});toast("Backup erstellt: "+result.filename);label.textContent="Backup erstellt";await refreshBackups();}catch(err){toast("Backup fehlgeschlagen: "+err.message);label.textContent=oldLabel;}finally{cmd.disabled=false;setTimeout(()=>{label.textContent=oldLabel},2200)}}else if(cmd.dataset.command==="backups-refresh"){refreshBackups()}else if(cmd.dataset.command==="diagnostics-refresh"){refreshDiagnostics()}else if(cmd.dataset.command==="agent-models-refresh"){refreshAgentModels()}else if(cmd.dataset.command==="agent-refresh"){refreshAgentStatus()}else{refresh();toast("Lokale Daten aktualisiert")}}});
document.addEventListener("change",async e=>{const sel=e.target.closest("[data-task]");if(!sel||!sel.value)return;try{await api("/api/tasks/"+encodeURIComponent(sel.dataset.task)+"/status",{method:"POST",body:JSON.stringify({status:sel.value,note:"Status über Dashboard geändert"})});await refresh();toast("Aufgabenstatus aktualisiert")}catch(err){toast(err.message);sel.value=""}});
window.addEventListener("hashchange",()=>navigate(location.hash.slice(1)));$("#today").textContent=new Intl.DateTimeFormat("de-DE",{weekday:"long",day:"2-digit",month:"long"}).format(new Date()).toUpperCase();navigate(location.hash.slice(1)||"overview");refresh();refreshAgentStatus();refreshAgentModels();refreshControlledAgents();setInterval(refreshSystem,10000);setInterval(refreshAgentStatus,15000);

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {
      // Offline caching is optional; the dashboard remains usable online.
    });
  });
}
