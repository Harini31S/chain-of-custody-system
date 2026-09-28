const $=s=>document.querySelector(s),ETYPES=['Mobile','Laptop','Hard Disk','USB Drive','Email Evidence','Log File'],
ACTIONS=['Collected','Seized','Transferred','Examined','Stored','Submitted to Court','Returned'],
CSTAT=['Open','In Progress','Under Review','Closed'],ESTAT=['Collected','In Transit','Under Analysis','In Storage','In Court','Returned'],
CTYPES=['Mobile','Email Phishing','USB','Laptop','Hard Disk'],today=()=>new Date().toISOString().slice(0,10);
let ME=null;
async function api(u,m='GET',b){const r=await fetch(u,{method:m,headers:{'Content-Type':'application/json'},body:b?JSON.stringify(b):undefined});
 const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.error||'Error');return d}
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
$('#toR').onclick=()=>{$('#lf').classList.add('hide');$('#rf').classList.remove('hide')};
$('#toL').onclick=()=>{$('#rf').classList.add('hide');$('#lf').classList.remove('hide')};
$('#lb').onclick=async()=>{try{await api('/api/login','POST',{email:$('#le').value,password:$('#lp').value});start()}catch(e){$('#lerr').textContent=e.message}};
$('#rb').onclick=async()=>{try{await api('/api/register','POST',{name:$('#rn').value,email:$('#re').value,password:$('#rp').value,role:$('#rr').value});
 $('#toL').click();$('#le').value=$('#re').value;$('#lp').value='';$('#lerr').textContent='Registered! Please login.'}catch(e){$('#rerr').textContent=e.message}};
const PAGES={Dashboard:dash,Cases:cases,Evidence:evidence,'Chain of Custody':custody,'Activity Logs':activity,Reports:reports};
async function start(){try{ME=await api('/api/me')}catch{return}
 $('#auth').classList.add('hide');$('#app').classList.remove('hide');
 $('#nav').innerHTML=Object.keys(PAGES).map(k=>`<a data-p="${k}">${k}</a>`).join('')+'<a id="lo">Logout</a>';
 document.querySelectorAll('#nav a[data-p]').forEach(a=>a.onclick=()=>go(a.dataset.p));
 $('#lo').onclick=async()=>{await api('/api/logout','POST');location.reload()};go('Dashboard')}
function go(p){document.querySelectorAll('#nav a').forEach(a=>a.classList.toggle('on',a.dataset.p==p));PAGES[p]()}
function tbl(cols,rows,click){return `<table><thead><tr>${cols.map(c=>`<th>${c.replace(/_/g,' ')}</th>`).join('')}</tr></thead><tbody>${rows.map((r,i)=>
 `<tr ${click?`class=c data-i=${i}`:''}>${cols.map(c=>`<td title="${esc(r[c])}">${['status','action','type','case_type','role'].includes(c)?`<span class=b>${esc(r[c])}</span>`:esc(r[c])}</td>`).join('')}</tr>`).join('')||`<tr><td>No records</td></tr>`}</tbody></table>`}
function modal(h){const m=document.createElement('div');m.className='modal';m.innerHTML=`<div class=mc>${h}</div>`;m.onclick=e=>{if(e.target==m)m.remove()};document.body.appendChild(m);return m}
function form(title,fields,vals,save){const m=modal(`<h3>${title}</h3><form>${fields.map(([n,l,t,o])=>`<label>${l}${t=='select'?`<select name=${n}>${o.map(x=>`<option ${vals[n]==x?'selected':''}>${x}</option>`).join('')}</select>`:
 t=='textarea'?`<textarea name=${n}>${esc(vals[n])}</textarea>`:`<input name=${n} type=${t} value="${esc(vals[n])}" ${n=='remarks'||n=='description'?'':'required'}>`}</label>`).join('')}<div class=err></div>
 <button class=btn>Save</button> <button type=button class="btn g" id=cx>Cancel</button></form>`);
 m.querySelector('#cx').onclick=()=>m.remove();
 m.querySelector('form').onsubmit=async e=>{e.preventDefault();try{await save(Object.fromEntries(new FormData(e.target)));m.remove()}catch(x){m.querySelector('.err').textContent=x.message}}}
async function listPage(kind,title,cols,opts,o={}){main.innerHTML=`<h2>${title}</h2><div class=bar><input id=q placeholder="Search ${title}..."><select id=f><option value="">All</option>${opts.map(x=>`<option>${x}</option>`).join('')}</select>
 ${o.add?`<button class=btn id=add>+ ${o.add}</button>`:''}</div><div class=tw id=tb></div>`;let rows=[];
 const load=async()=>{rows=await api(`/api/${kind}?q=${encodeURIComponent($('#q').value)}&f=${encodeURIComponent($('#f').value)}`);
  $('#tb').innerHTML=tbl(cols,rows,!!o.click);$('#tb').querySelectorAll('tr.c').forEach(t=>t.onclick=()=>o.click(rows[t.dataset.i],load))};
 $('#q').oninput=load;$('#f').onchange=load;if(o.add)$('#add').onclick=()=>o.onAdd(load);load()}
async function dash(){const s=await api('/api/stats'),a=await api('/api/activity?q='),
 card=(n,l)=>`<div class=stat><b>${n}</b><span>${l}</span></div>`;
 main.innerHTML=`<h2>Welcome, ${esc(ME.name)}</h2><p style="color:var(--mt)">Role: <span class=b>${esc(ME.role)}</span> &nbsp; Logged in: ${ME.login_time}</p>
 <div class=grid>${card(s.cases,'Total Cases')}${card(s.evidence,'Total Evidence')}${card(s.custody,'Custody Transfers')}${card(s.users,'Registered Users')}</div>
 <h2 style="font-size:16px">Recent Activity</h2><div class=tw>${tbl(['user_name','role','action','detail','timestamp'],a.slice(0,10))}</div>`}
const caseForm=(t,v,cb)=>form(t,[['case_name','Case Name','text'],['case_type','Case Type','select',CTYPES],['officer','Investigation Officer','text'],['created_date','Created Date','date'],['status','Status','select',CSTAT]],v,cb);
function cases(){listPage('cases','Cases',['case_id','case_name','case_type','officer','created_date','status'],CSTAT,{add:'Create Case',
 onAdd:l=>caseForm('Create Case',{created_date:today(),status:'Open'},async d=>{await api('/api/cases','POST',d);l()}),
 click:(r,l)=>caseForm('Edit '+r.case_id,r,async d=>{await api('/api/cases/'+r.case_id,'PUT',d);l()})})}
const evForm=(t,v,cb)=>form(t,[['case_id','Case ID','text'],['name','Evidence Name','text'],['type','Evidence Type','select',ETYPES],['description','Description','textarea'],['collection_date','Collection Date','date'],['status','Status','select',ESTAT]],v,cb);
function evidence(){listPage('evidence','Evidence',['evidence_id','case_id','name','type','description','collection_date','status'],ETYPES,{add:'Add Evidence',
 onAdd:l=>evForm('Add Evidence',{collection_date:today(),status:'Collected'},async d=>{await api('/api/evidence','POST',d);l()}),click:r=>evDetail(r.evidence_id)})}
async function evDetail(id){let e,logs;try{[e,logs]=await Promise.all([api('/api/evidence/'+id),api('/api/custody?eid='+id)])}catch(x){return alert(x.message)}
 const m=modal(`<h3>${e.evidence_id} — ${esc(e.name)}</h3><div class=kv>${['case_id','type','description','collection_date','status','md5','sha256'].map(k=>`<span>${k.replace('_',' ')}</span><b>${esc(e[k])}</b>`).join('')}</div>
 <button class=btn id=vf>🔍 Verify Integrity</button> <button class="btn g" id=ed>Edit</button> <button class="btn g" id=ad>+ Custody Transfer</button><div id=vr></div>
 <h3 style="margin-top:18px">Custody Timeline</h3><div class=tl>${logs.map(l=>`<div class=ti><i></i><b>${l.action}</b><span>${l.transfer_date} ${l.transfer_time}</span>
 <p>${esc(l.from_person)} → ${esc(l.to_person)} @ ${esc(l.location)}</p><small>${esc(l.remarks)}</small></div>`).join('')||'No custody records'}</div>`);
 m.querySelector('#vf').onclick=async()=>{const r=await api(`/api/evidence/${id}/verify`,'POST');
  m.querySelector('#vr').innerHTML=r.ok?`<div class=ok>✔ Integrity Maintained<br><small>Stored and current MD5/SHA256 hashes match.</small></div>`:
  `<div class=bad>✖ Integrity Failed<br><small>Stored MD5: ${r.stored_md5}<br>Current MD5: ${r.current_md5}</small></div>`};
 m.querySelector('#ed').onclick=()=>{m.remove();evForm('Update '+id,e,async d=>{await api('/api/evidence/'+id,'PUT',d);evDetail(id)})};
 m.querySelector('#ad').onclick=()=>{m.remove();custForm(id,()=>evDetail(id))}}
function custForm(id,cb){form('Create Custody Transfer',[['evidence_id','Evidence ID','text'],['from_person','From Person','text'],['to_person','To Person','text'],['transfer_date','Transfer Date','date'],
 ['transfer_time','Transfer Time','time'],['location','Location','text'],['action','Action','select',ACTIONS],['remarks','Remarks','textarea']],
 {evidence_id:id||'',transfer_date:today(),transfer_time:new Date().toTimeString().slice(0,5),from_person:ME.name},async d=>{await api('/api/custody','POST',d);cb()})}
function custody(){listPage('custody','Chain of Custody',['log_id','evidence_id','from_person','to_person','transfer_date','transfer_time','location','action','remarks'],ACTIONS,
 {add:'Transfer Evidence',onAdd:l=>custForm('',l),click:r=>evDetail(r.evidence_id)})}
function activity(){listPage('activity','Activity Logs',['id','user_name','role','action','detail','timestamp'],['User Login','User Logout','Evidence Added','Evidence Updated','Custody Transfer Created','Integrity Verified'])}
function reports(){main.innerHTML=`<h2>Reports</h2><div class=grid>${[['cases','Case Report'],['evidence','Evidence Report'],['custody','Custody Report']].map(([k,t])=>
 `<div class=stat><b style="font-size:18px">${t}</b><br><a class=btn href="/api/report/${k}/pdf">PDF</a> <a class="btn g" href="/api/report/${k}/csv">CSV</a></div>`).join('')}</div>`}
start();
