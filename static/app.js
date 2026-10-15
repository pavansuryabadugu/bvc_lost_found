const COLLEGE = 'Bonam Venkata Chalamayya Engineering College';
const CATS = ['Electronics', 'Books', 'ID & Cards', 'Keys', 'Clothing', 'Bags', 'Other'];
const LOCS = ['Main Block', 'Library', 'Canteen', 'Hostel', 'Lab Block', 'Sports Ground', 'Auditorium', 'Parking'];
const BR = ['CSE', 'ECE', 'EEE', 'MECH', 'CIVIL', 'IT', 'AI & DS', 'Other'];
const ICON = {Electronics: '💻', Books: '📚', 'ID & Cards': '🪪', Keys: '🔑', Clothing: '🧥', Bags: '🎒', Other: '📦'};
const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
const fmt = iso => new Date(iso).toLocaleString('en-IN', {day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'});
const nowLocal = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 16); };

let TOKEN = localStorage.getItem('lf_token') || '', ME = null, view = 'feed', tab = 'login';
let F = {q: '', type: '', cat: ''}, PHOTO = null, LAST = null, UNREAD = 0, timer;

async function api(path, opt = {}) {
  const headers = {};
  if (TOKEN) headers.Authorization = 'Bearer ' + TOKEN;
  if (opt.json) { headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(opt.json); }
  const r = await fetch('/api' + path, {method: opt.method, body: opt.body, headers});
  const data = await r.json().catch(() => ({}));
  if (r.status === 401 && TOKEN) { logout(); throw new Error('Please log in again.'); }
  if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : (data.detail?.[0]?.msg || 'Request failed'));
  return data;
}
const err = m => { const e = $('#err'); if (e) e.textContent = m; };
const run = fn => async (...a) => { try { await fn(...a); } catch (e) { err(e.message); } };

/* ---------- login / registration ---------- */
function authView() {
  const L = tab === 'login';
  const lf = `<label>Roll number or email</label><input id="lid" autocomplete="username">
    <label>Password</label><input id="lpw" type="password" autocomplete="current-password">
    <p><button class="pri" style="width:100%" onclick="login()">Login</button></p>`;
  const rf = `<label>Full name</label><input id="rn">
    <div class="row"><div><label>Roll number</label><input id="rr"></div>
    <div><label>Branch</label><select id="rb">${BR.map(b => `<option>${b}</option>`).join('')}</select></div></div>
    <label>WhatsApp number (10 digits)</label><input id="rp" inputmode="numeric" maxlength="10" placeholder="9XXXXXXXXX">
    <label>College email</label><input id="re" type="email">
    <label>Password (min 6 characters)</label><input id="rw" type="password" autocomplete="new-password">
    <p><button class="pri" style="width:100%" onclick="register()">Create account</button></p>`;
  return `<div class="auth"><img class="logo" src="/logo.webp" alt="BVC logo"><h1>${COLLEGE}</h1>
    <p class="m">Odalarevu · Campus Lost &amp; Found</p>
    <div class="panel"><div class="row tabs">
      <button class="${L ? 'on' : ''}" onclick="tab='login';render()">Login</button>
      <button class="${L ? '' : 'on'}" onclick="tab='register';render()">Student registration</button></div>
      ${L ? lf : rf}<p id="err" class="err"></p></div>
    <p class="m">Reports are visible only to registered students after login.</p></div>`;
}
const enter = d => { TOKEN = d.token; localStorage.setItem('lf_token', TOKEN); ME = d.user; view = 'feed'; render(); };
const register = run(async () => {
  const v = id => $('#' + id).value.trim();
  enter(await api('/auth/register', {method: 'POST', json: {name: v('rn'), roll: v('rr'), branch: v('rb'),
    phone: v('rp'), email: v('re'), password: $('#rw').value}}));
});
const login = run(async () => {
  enter(await api('/auth/login', {method: 'POST', json: {identifier: $('#lid').value, password: $('#lpw').value}}));
});
function logout() { TOKEN = ''; ME = null; tab = 'login'; localStorage.removeItem('lf_token'); closeM(); render(); }

/* ---------- layout ---------- */
function shell(body) {
  const v = [['feed', 'Reports'], ['post', 'Report lost / found'], ['mine', 'My activity'],
    ['notes', 'Alerts' + (UNREAD ? ` <span class="dot">${UNREAD}</span>` : '')]];
  if (ME.is_admin) v.push(['admin', 'Admin']);
  return `<header><div class="top"><div class="brand"><img src="/logo.webp" alt="BVC logo">
    <div>BVC Lost &amp; Found<small>${esc(ME.name)} · ${esc(ME.roll)}</small></div></div>
    <nav>${v.map(([k, l]) => `<button class="${view === k ? 'on' : ''}" onclick="go('${k}')">${l}</button>`).join('')}
    <button onclick="logout()">Logout</button></nav></div></header><main>${body}</main>`;
}
const go = v => { view = v; render(); };
const card = i => `<div class="card" onclick="openItem(${i.id})">${i.image_url ? `<img src="${i.image_url}" alt="">` : `<div class="ph">${ICON[i.category] || '📦'}</div>`}
  <div class="b"><span class="tag ${i.type}">${i.type.toUpperCase()}</span>${i.status !== 'open' ? ` <span class="m">· ${esc(i.status)}</span>` : ''}
  <h3>${esc(i.title)}</h3><div class="m">${esc(i.location)} · ${fmt(i.occurred_at)}</div></div></div>`;

/* ---------- views ---------- */
function feed() {
  return `<div class="bar"><input placeholder="Search object or place…" value="${esc(F.q)}" oninput="F.q=this.value;clearTimeout(timer);timer=setTimeout(list,250)">
    <select onchange="F.type=this.value;list()"><option value="">Lost &amp; found</option>
    <option value="lost" ${F.type === 'lost' ? 'selected' : ''}>Lost</option><option value="found" ${F.type === 'found' ? 'selected' : ''}>Found</option></select>
    <select onchange="F.cat=this.value;list()"><option value="">All categories</option>${CATS.map(c => `<option ${F.cat === c ? 'selected' : ''}>${c}</option>`).join('')}</select></div>
    <div id="list" class="grid"><p class="m">Loading…</p></div>`;
}
async function list() {
  const p = new URLSearchParams({q: F.q, type: F.type, category: F.cat});
  const items = await api('/items?' + p);
  const el = $('#list'); if (el) el.innerHTML = items.length ? items.map(card).join('') : '<p class="m">No reports match.</p>';
}
function postForm() {
  PHOTO = null;
  return `<div class="panel"><h2 style="margin-top:0">Lost / found report</h2>
  <label>Report type</label><select id="pt" onchange="$('#qw').style.display=this.value==='found'?'block':'none'">
    <option value="lost">I lost an object</option><option value="found">I found an object</option></select>
  <label>Object name</label><input id="ptl" placeholder="e.g. Black backpack">
  <label>Description (colour, brand, marks)</label><textarea id="pd" rows="3"></textarea>
  <div class="row"><div><label>Category</label><select id="pc">${CATS.map(c => `<option>${c}</option>`).join('')}</select></div>
  <div><label>Place / block</label><select id="pl">${LOCS.map(c => `<option>${c}</option>`).join('')}</select></div></div>
  <label>Exact location</label><input id="ps" placeholder="e.g. 2nd floor corridor near Room 204">
  <label>Exact date and time</label><input id="pdt" type="datetime-local" max="${nowLocal()}" value="${nowLocal()}">
  <label>Photo (optional)</label><input type="file" accept="image/*" onchange="pickPhoto(this)">
  <img id="prev" alt="" style="max-width:160px;border-radius:8px;margin-top:8px;display:none">
  <div id="qw" style="display:none"><label>Verification question (only the real owner can answer)</label><input id="pq"></div>
  <p id="err" class="err"></p><p><button class="pri" onclick="submitItem()">Submit report</button></p></div>`;
}
function pickPhoto(inp) {
  const f = inp.files[0]; if (!f) return;
  const im = new Image();
  im.onload = () => {
    const k = Math.min(1, 1000 / Math.max(im.width, im.height)), c = document.createElement('canvas');
    c.width = im.width * k; c.height = im.height * k;
    c.getContext('2d').drawImage(im, 0, 0, c.width, c.height);
    c.toBlob(b => { PHOTO = b; const p = $('#prev'); p.src = URL.createObjectURL(b); p.style.display = 'block'; }, 'image/jpeg', .8);
  };
  im.src = URL.createObjectURL(f);
}
const submitItem = run(async () => {
  const fd = new FormData();
  fd.append('type', $('#pt').value); fd.append('title', $('#ptl').value); fd.append('description', $('#pd').value);
  fd.append('category', $('#pc').value); fd.append('location', $('#pl').value);
  fd.append('exact_location', $('#ps').value); fd.append('occurred_at', $('#pdt').value);
  fd.append('verification_question', $('#pq').value);
  if (PHOTO) fd.append('photo', PHOTO, 'photo.jpg');
  LAST = await api('/items', {method: 'POST', body: fd});
  view = 'sent'; render();
});
function sent() {
  const t = LAST.whatsapp_text, n = LAST.notified;
  return `<div class="panel"><h2 style="margin-top:0">Report submitted ✅</h2>
  <p>${n} registered student${n === 1 ? '' : 's'} received an alert (and a WhatsApp message if WhatsApp is configured on the server).</p>
  <p class="m">Message sent:</p><pre>${esc(t)}</pre>
  <a class="wa" target="_blank" rel="noopener" href="https://wa.me/?text=${encodeURIComponent(t)}">Also share in a WhatsApp group</a>
  <button onclick="go('feed')">Back to reports</button></div>`;
}
async function openItem(id) {
  const i = await api('/items/' + id), mine = i.owner_id === ME.id;
  const claimBox = mine || i.status !== 'open' ? '' : (i.my_claim ? `<p class="m">You already sent a claim (${esc(i.my_claim)}).</p>` :
    `<label>${i.type === 'found' ? esc(i.question || 'Describe the object to prove it is yours') : 'Where did you find it?'}</label>
     <textarea id="ca" rows="2"></textarea><p id="err" class="err"></p>
     <p><button class="pri" onclick="claim(${id})">${i.type === 'found' ? 'Claim this object' : 'I found this'}</button></p>`);
  $('#modal').innerHTML = `<div class="modal-bg" onclick="if(event.target===this)closeM()"><div class="panel">
    <div class="row" style="justify-content:space-between"><span class="tag ${i.type}">${i.type.toUpperCase()}</span><button onclick="closeM()">Close</button></div>
    <h2 style="margin:8px 0">${esc(i.title)}</h2>${i.image_url ? `<img src="${i.image_url}" alt="">` : ''}
    <p>${esc(i.description) || '<span class="m">No description.</span>'}</p>
    <p class="m">${esc(i.category)} · ${esc(i.location)} — ${esc(i.exact_location)}<br>${fmt(i.occurred_at)} · Status: ${esc(i.status)}<br>Reported by ${mine ? 'you' : esc(i.owner_name)}</p>
    ${i.matches.length ? `<h3>Possible matches</h3>${i.matches.map(m => `<p style="cursor:pointer" onclick="openItem(${m.id})">• <b>${esc(m.title)}</b> (${m.score}% match) <span class="m">${esc(m.location)}</span></p>`).join('')}` : ''}
    ${claimBox}${mine || ME.is_admin ? `<button class="dng" onclick="del(${id})">Delete report</button>` : ''}</div></div>`;
}
const closeM = () => { $('#modal').innerHTML = ''; };
const claim = run(async id => {
  await api(`/items/${id}/claims`, {method: 'POST', json: {answer: $('#ca').value}});
  closeM(); go('mine');
});
async function del(id) { if (!confirm('Delete this report?')) return; await api('/items/' + id, {method: 'DELETE'}); closeM(); render(); }
async function decide(id, status) { await api('/claims/' + id, {method: 'PATCH', json: {status}}); render(); }
async function mine() {
  const [items, got, sentC] = await Promise.all([api('/items?mine=true'), api('/claims/received'), api('/claims/mine')]);
  return `<h2>My reports</h2>${items.length ? items.map(i => `<div class="panel"><div class="row" style="justify-content:space-between">
    <b>${esc(i.title)} <span class="tag ${i.type}">${i.type}</span></b><span class="m">${esc(i.status)}</span></div>
    ${got.filter(c => c.item_id === i.id).map(c => `<div class="m" style="margin-top:8px"><b>${esc(c.claimant_name)}</b>: ${esc(c.answer)} <i>(${esc(c.status)})</i>
    ${c.status === 'pending' ? ` <button class="pri" onclick="decide(${c.id},'approved')">Approve</button> <button onclick="decide(${c.id},'rejected')">Reject</button>` : ''}</div>`).join('')}</div>`).join('') : '<p class="m">You have not posted anything yet.</p>'}
    <h2>My claims</h2>${sentC.length ? sentC.map(c => `<div class="panel">${esc(c.item_title)} — <b>${esc(c.status)}</b></div>`).join('') : '<p class="m">No claims sent.</p>'}`;
}
async function notes() {
  const l = await api('/notifications');
  await api('/notifications/read-all', {method: 'POST'});
  return `<h2>Alerts</h2>${l.length ? l.map(n => `<div class="panel ${n.is_read ? '' : 'unread'}">${esc(n.message)}</div>`).join('') : '<p class="m">No alerts yet.</p>'}`;
}
async function admin() {
  const s = await api('/admin/stats');
  const b = [['students', 'Students'], ['total', 'Total reports'], ['lost', 'Lost'], ['found', 'Found'], ['returned', 'Returned'], ['pending_claims', 'Pending claims']];
  return `<h2>Admin dashboard</h2><div class="stats">${b.map(([k, l]) => `<div><b>${s[k]}</b>${l}</div>`).join('')}</div>`;
}

/* ---------- render ---------- */
const VIEWS = {feed, post: postForm, mine, notes, sent, admin};
async function render() {
  if (!ME) { $('#root').innerHTML = authView(); return; }
  let body;
  try { body = await VIEWS[view](); } catch (e) { body = `<p class="err">${esc(e.message)}</p>`; }
  try { UNREAD = (await api('/notifications/unread')).unread; } catch (e) { return; }
  $('#root').innerHTML = shell(body);
  if (view === 'feed') list();
}
(async () => {
  if (TOKEN) { try { ME = await api('/auth/me'); } catch (e) { ME = null; } }
  render();
})();
