'use strict';
const $ = id => document.getElementById(id);
let config, session, channel = 'FREE', page = 'signals', mode = 'login';
let installPrompt, claimToken = '', setupToken = '', serverOffset = 0, polling = false, currentRows = [], lastFeedKey = '';
const safe = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const number = value => value == null ? 'Unavailable' : new Intl.NumberFormat(undefined,{maximumFractionDigits:6}).format(value);
const localTime = value => new Date(value * 1000).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
const dateTime = value => new Date(value * 1000).toLocaleString([], {day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'});
function notice(text, error = false) { $('notice').textContent = text; $('notice').classList.toggle('error', error); $('notice').hidden = !text; }
async function api(path, options = {}) {
  const headers = {'Content-Type':'application/json', ...(session?.csrf ? {'X-CSRF-Token':session.csrf} : {}), ...options.headers};
  const response = await fetch(path, {...options, headers, credentials:'same-origin', cache:'no-store'});
  let data;
  try { data = await response.json(); } catch { throw new Error('The application could not complete this request.'); }
  if (!response.ok) {
    const error = new Error(typeof data.detail === 'string' ? data.detail : 'Please check your input and try again.');
    error.status = response.status;
    throw error;
  }
  return data;
}
function authScreen() {
  session = null; currentRows = []; lastFeedKey = ''; $('signal-list').replaceChildren();
  $('app').hidden = true; $('auth').hidden = false; $('boot').hidden = true;
  if (setupToken && config?.setup_available) {
    $('auth-title').textContent = 'Make this app yours.';
    $('auth-description').textContent = 'Create your application owner account.';
    $('mode-login').parentElement.hidden = true;
    $('auth-submit').textContent = 'Create owner account ↗';
    $('password').autocomplete = 'new-password';
  }
}
function setMode(value) {
  mode = value;
  $('mode-login').classList.toggle('selected',mode === 'login');
  $('mode-register').classList.toggle('selected',mode === 'register');
  $('auth-submit').textContent = mode === 'login' ? 'Sign in ↗' : 'Create account ↗';
  $('password').autocomplete = mode === 'login' ? 'current-password' : 'new-password';
  $('auth-error').textContent = '';
}
async function refreshSession() {
  session = await api('/api/session');
  $('app').hidden = false; $('auth').hidden = true; $('boot').hidden = true;
  $('admin-nav').hidden = session.role !== 'OWNER';
  $('avatar').textContent = session.email.slice(0,1).toUpperCase();
  $('account-email').textContent = session.email;
  $('account-role').textContent = session.role === 'OWNER' ? 'Application owner' : 'Member';
  const tier = session.access.tier;
  if (!session.allowed_channels.includes(channel)) channel = session.allowed_channels[0] || 'FREE';
  $('plan-name').textContent = tier ? tier[0] + tier.slice(1).toLowerCase() : 'Sync needed';
  $('plan-status').textContent = ['ACTIVE','FREE_FALLBACK'].includes(session.access.access_state) ? 'Active' : 'Access on hold';
  $('plan-summary').textContent = session.access.connected ? 'Connected to your existing subscription.' : 'Connect your existing subscription whenever you are ready.';
  $('subscription-name').textContent = (tier || 'Awaiting sync') + ' membership';
  $('subscription-state').textContent = session.access.connected ? (session.access.access_state === 'UNAVAILABLE' ? 'Subscription evidence needs a fresh sync before protected access can continue.' : `Your subscription is connected.${session.access.expires_at_epoch ? ' Current period ends '+dateTime(session.access.expires_at_epoch)+'.' : ''}`) : 'You are using the Free channel. No additional payment has been created.';
  $('channels').innerHTML = config.channels.map(item => `<button class="channel-button ${item.id === channel ? 'selected' : ''}" data-channel="${safe(item.id)}" type="button" aria-pressed="${item.id === channel}">${safe(item.name)}${session.allowed_channels.includes(item.id) ? '' : '<span class="lock" aria-label="locked">◇</span>'}</button>`).join('');
  $('plan-grid').innerHTML = config.channels.map(item => `<article class="plan-option"><span class="eyebrow">${item.id === tier ? 'Your current plan' : 'Channel'}</span><h3>${safe(item.name)}</h3><p>${item.daily_limit == null ? 'No daily signal cap' : 'Up to '+safe(item.daily_limit)+' entry signals per day'}</p><p>${item.requires_payment ? 'Connect an existing subscription.' : 'Available with your app account.'}</p></article>`).join('');
  renderStatus(session.status);
}
const headings = {
  signals:['Stay in the picture','Your signals','A focused view of what matters, as it happens.'],
  history:['The full picture','Signal history','Revisit the stages exactly as they were published.'],
  subscription:['Your membership','One plan. Your choice.','Keep your subscription connected across both spaces.'],
  account:['Make yourself at home','Your account','Manage this device and your app preferences.'],
  analysis:['Application owner','A clearer overview','Recorded signals, membership and source evidence.']
};
async function navigate() {
  if (!session) return;
  const next = location.hash.replace('#','') || 'signals';
  page = Object.hasOwn(headings,next) ? next : 'signals';
  if (page === 'analysis' && session.role !== 'OWNER') page = 'signals';
  document.querySelectorAll('.page').forEach(el => el.hidden = el.id !== 'page-'+(page === 'history' ? 'signals' : page));
  document.querySelectorAll('.main-nav a').forEach(el => el.classList.toggle('active',el.dataset.page === page));
  const heading = headings[page];
  $('page-kicker').textContent = heading[0]; $('page-title').textContent = heading[1]; $('page-description').textContent = heading[2];
  $('enable-alerts').hidden = !['signals','history'].includes(page);
  currentRows = []; lastFeedKey = '';
  if (['signals','history'].includes(page)) await loadSignals();
  if (page === 'analysis') await loadAnalysis();
}
function renderStatus(status) {
  const labels = {OBSERVING:'Engine observing',NOT_CONNECTED:'Source not connected',PROVIDER_CONFIGURATION_REQUIRED:'Source setup needed',EVIDENCE_UNAVAILABLE:'Evidence unavailable'};
  $('connection-text').textContent = labels[status?.engine_state] || 'Source not connected';
  $('connection-dot').classList.toggle('good',status?.engine_state === 'OBSERVING');
}
function empty(title, body, action = false) {
  $('signal-list').innerHTML = `<div class="empty-state"><div class="empty-icon" aria-hidden="true">⌁</div><h2>${safe(title)}</h2><p>${safe(body)}</p>${action ? '<a href="#subscription" class="secondary">View my subscription ↗</a>' : ''}</div>`;
  $('load-more').hidden = true;
}
function signalCard(row) {
  const now = Date.now()/1000 + serverOffset;
  const expired = row.expires_at && row.expires_at <= now;
  let timing = 'No execution duration at this stage';
  if (row.stage === 'CONFIRM' && row.execution_time_available) timing = `${number(row.confirm_expiry_min_minutes)}–${number(row.confirm_expiry_max_minutes)} min range`;
  if (row.stage === 'OPEN_NOW') timing = `${number(row.open_now_expiry_minutes)} min exact duration`;
  const stageClass = row.stage === 'OPEN_NOW' ? 'open' : row.stage.toLowerCase();
  const feedback = (session.role === 'OWNER' || session.access.tier === 'ELITE') && expired ? `<div class="feedback-row" aria-label="Personal result"><span class="small muted">My result</span>${['WIN','LOSE','MISSED'].map(result => `<button type="button" class="secondary" data-feedback="${result}" data-signal="${safe(row.signal_id)}">${result[0]+result.slice(1).toLowerCase()}</button>`).join('')}</div>` : '';
  return `<article class="signal-card ${row.stage === 'OPEN_NOW' ? 'open-card' : ''} ${expired ? 'expired' : ''}" data-event="${safe(row.event_id)}"><div class="signal-card-top"><span class="stage ${stageClass}">${safe(row.stage.replace('_',' '))}</span><time datetime="${new Date(row.created_ts*1000).toISOString()}">${dateTime(row.created_ts)}</time></div><div class="signal-main"><div><span class="market-name">${safe(row.symbol)}</span><span class="timeframe">${safe(row.timeframe)}</span></div><span class="direction ${row.direction === 'SELL' ? 'sell' : ''}">${row.direction === 'BUY' ? '↗' : '↘'} ${safe(row.direction)}</span></div><div class="signal-values"><div><span>Entry reference</span><b>${number(row.entry_price)}</b></div><div><span>Strategy score</span><b>${number(row.score_total)}</b></div><div><span>Buffer</span><b>${safe(row.buffer_mode)}</b></div></div><div class="signal-bottom"><span>${safe(timing)}${row.expires_at ? ' · <strong data-expires="'+row.expires_at+'">'+(expired ? 'Expired' : 'Timing…')+'</strong>' : ''}</span><span class="signal-id" title="${safe(row.signal_id)}">${safe(row.signal_id)}</span></div>${feedback}</article>`;
}
async function loadSignals(older = false) {
  if (polling || !session || !['signals','history'].includes(page)) return;
  if (!session.allowed_channels.includes(channel)) { empty('This channel belongs to another plan.','Your membership gives access to one channel. Connect your existing subscription to continue.',true); return; }
  polling = true;
  try {
    const before = older && currentRows.length ? '?before='+currentRows.at(-1).seq : '';
    const data = await api('/api/signals/'+encodeURIComponent(channel)+before);
    serverOffset = data.server_time - Date.now()/1000;
    renderStatus(data.status);
    const rows = data.signals;
    $('feed-label').textContent = channel+' channel';
    $('last-updated').textContent = data.status.last_signal_at ? 'Last publication '+localTime(data.status.last_signal_at) : 'No publication yet';
    if (older) currentRows.push(...rows.filter(row => !currentRows.some(old => old.seq === row.seq)));
    else currentRows = rows;
    const feedKey = page+':'+channel+':'+currentRows.map(row => row.seq).join(',');
    if (feedKey !== lastFeedKey) {
      if (!currentRows.length) empty('A little space before the next signal.',data.status.engine_state === 'NOT_CONNECTED' || data.status.engine_state === 'PROVIDER_CONFIGURATION_REQUIRED' ? 'The app is ready. Live signals will appear after its independent data source is connected.' : 'No published signals have arrived in this channel yet. The strategy determines when a setup is ready.');
      else $('signal-list').innerHTML = currentRows.map(signalCard).join('');
      lastFeedKey = feedKey;
    }
    $('load-more').hidden = rows.length < 40 || page !== 'history';
    countdowns();
  } catch (error) {
    if (error.status === 401) authScreen();
    else if (error.status === 403) { currentRows = []; lastFeedKey = ''; empty('Subscription access needs attention.',error.message,true); }
    else { $('connection-text').textContent = 'Connection interrupted'; $('connection-dot').classList.remove('good'); }
  } finally { polling = false; }
}
function countdowns() {
  const now = Date.now()/1000 + serverOffset;
  document.querySelectorAll('[data-expires]').forEach(el => {
    const remaining = Math.floor(Number(el.dataset.expires)-now);
    el.textContent = remaining > 0 ? `${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,'0')} remaining` : 'Expired';
    if (remaining <= 0) el.closest('.signal-card').classList.add('expired');
  });
}
async function loadAnalysis() {
  try {
    const data = await api('/api/admin'), m = data.metrics;
    const metrics = [['App members',m.members,'Registered application accounts'],['Entry signals',m.stages.OPEN_NOW || 0,'Unique published OPEN NOW signals'],['Market win rate',m.market_win_rate == null ? '—' : (m.market_win_rate*100).toFixed(1)+'%',m.settled_market_sample+' objective settled results'],['Personal reports',Object.values(m.community_reports).reduce((a,b)=>a+b,0),'Self-reports, separate from market evidence']];
    $('metrics').innerHTML = metrics.map(([title,value,note]) => `<div class="metric"><span class="eyebrow">${safe(title)}</span><b>${safe(value)}</b><small>${safe(note)}</small></div>`).join('');
    const max = Math.max(1,...Object.values(m.stages));
    $('stage-bars').innerHTML = ['PRE','CONFIRM','OPEN_NOW'].map(stage => `<div class="bar-row"><span>${stage.replace('_',' ')}</span><progress class="stage-progress" max="${max}" value="${m.stages[stage] || 0}" aria-label="${stage}"></progress><b>${m.stages[stage] || 0}</b></div>`).join('');
    $('canonical-info').innerHTML = `<dt>Canonical source files</dt><dd>${data.canonical.canonical_files}</dd><dt>Strategy source</dt><dd>Existing Binary Strategy V2 engine</dd><dt>Canonical fingerprint</dt><dd class="canonical-hash">${safe(data.canonical.canonical_sha256)}</dd><dt>Telegram command connection</dt><dd>Not connected</dd>`;
    renderStatus(data.status);
  } catch (error) { notice(error.message,true); }
}
async function claimSubscription(token) {
  await api('/api/claim',{method:'POST',body:JSON.stringify({token})});
  claimToken = ''; $('claim-token').value = '';
  await refreshSession(); lastFeedKey = ''; notice('Your existing subscription is connected. No additional payment was created.');
}
function urlCode(value) {
  value = value.trim();
  if (value.includes('#claim=')) return value.split('#claim=')[1].split('&')[0];
  return value;
}
async function install() {
  if (config?.android_download && /Android/i.test(navigator.userAgent)) { location.assign(config.android_download); return; }
  if (installPrompt) { await installPrompt.prompt(); await installPrompt.userChoice; installPrompt = null; }
  else $('install-dialog').showModal();
}
async function alerts() {
  try {
    if (!('Notification' in window) || !('serviceWorker' in navigator) || !('PushManager' in window)) throw new Error('This browser cannot enable app alerts. Install the app in a supported browser first.');
    if (await Notification.requestPermission() !== 'granted') throw new Error('Alerts are off. You can allow them in your browser’s settings.');
    const worker = await navigator.serviceWorker.ready;
    let subscription = await worker.pushManager.getSubscription();
    if (!subscription) {
      const encoded = config.push_public_key.replace(/-/g,'+').replace(/_/g,'/');
      const key = Uint8Array.from(atob(encoded+'='.repeat((4-encoded.length%4)%4)),ch => ch.charCodeAt(0));
      subscription = await worker.pushManager.subscribe({userVisibleOnly:true,applicationServerKey:key});
    }
    await api('/api/push',{method:'POST',body:JSON.stringify(subscription.toJSON())});
    notice('Alerts are enabled on this device. Delivery also depends on your browser and network.');
  } catch (error) { notice(error.message,true); }
}
$('mode-login').onclick = () => setMode('login'); $('mode-register').onclick = () => setMode('register');
$('auth-form').onsubmit = async event => {
  event.preventDefault(); $('auth-submit').disabled = true; $('auth-error').textContent = '';
  try {
    const endpoint = setupToken && config.setup_available ? 'setup' : mode;
    const data = await api('/api/'+endpoint,{method:'POST',body:JSON.stringify({email:$('email').value,password:$('password').value,...(endpoint === 'setup' ? {token:setupToken} : {})})});
    setupToken = ''; session = {csrf:data.csrf}; $('password').value = '';
    await refreshSession();
    if (claimToken) { try { await claimSubscription(claimToken); } catch (error) { notice(error.message,true); } }
    await navigate();
  } catch (error) { $('auth-error').textContent = error.message; }
  finally { $('auth-submit').disabled = false; }
};
$('channels').onclick = async event => { const button = event.target.closest('[data-channel]'); if (!button) return; channel = button.dataset.channel; lastFeedKey = ''; await refreshSessionForChannel(); };
async function refreshSessionForChannel() {
  document.querySelectorAll('.channel-button').forEach(button => { button.classList.toggle('selected',button.dataset.channel === channel); button.setAttribute('aria-pressed',String(button.dataset.channel === channel)); });
  currentRows = []; await loadSignals();
}
$('signal-list').onclick = async event => {
  const button = event.target.closest('[data-feedback]'); if (!button) return;
  try { await api('/api/feedback',{method:'POST',body:JSON.stringify({signal_id:button.dataset.signal,result:button.dataset.feedback})}); notice('Your personal result was saved separately from objective market results.'); }
  catch (error) { notice(error.message,true); }
};
$('load-more').onclick = () => loadSignals(true);
$('avatar').onclick = () => location.hash = 'account';
$('claim-form').onsubmit = async event => { event.preventDefault(); try { await claimSubscription(urlCode($('claim-token').value)); } catch (error) { notice(error.message,true); } };
$('invite-form').onsubmit = async event => {
  event.preventDefault();
  try { const data = await api('/api/admin/invites',{method:'POST',body:JSON.stringify({email:$('invite-email').value,subscriber_ref:$('invite-ref').value})}); $('invite-url').value = data.url; $('invite-result').hidden = false; notice('Personal link created. It expires in 15 minutes.'); }
  catch (error) { notice(error.message,true); }
};
$('copy-invite').onclick = async () => { try { await navigator.clipboard.writeText($('invite-url').value); notice('Connection link copied.'); } catch { $('invite-url').select(); notice('Select and copy the connection link.'); } };
$('logout').onclick = async () => {
  try {
    await api('/api/logout',{method:'POST',body:'{}'});
    const worker = await navigator.serviceWorker?.getRegistration(); worker?.active?.postMessage('SIGNED_OUT');
    const subscription = await worker?.pushManager.getSubscription(); if (subscription) await subscription.unsubscribe();
    location.hash = ''; authScreen();
  } catch (error) { notice(error.message,true); }
};
$('enable-alerts').onclick = alerts;
$('disable-alerts').onclick = async () => {
  try { await api('/api/push',{method:'DELETE',body:'{}'}); const worker = await navigator.serviceWorker?.getRegistration(); const subscription = await worker?.pushManager.getSubscription(); if (subscription) await subscription.unsubscribe(); notice('App alerts are off.'); }
  catch (error) { notice(error.message,true); }
};
['install-auth','install-side','install-account'].forEach(id => $(id).onclick = install);
window.addEventListener('beforeinstallprompt',event => { event.preventDefault(); installPrompt = event; });
window.addEventListener('hashchange',() => navigate().catch(error => notice(error.message,true)));
document.addEventListener('visibilitychange',() => { if (!document.hidden) loadSignals(); });
setInterval(() => { if (!document.hidden) loadSignals(); },2000);
setInterval(countdowns,1000);
setInterval(async () => { if (session && !document.hidden) { try { await refreshSession(); } catch (error) { if (error.status === 401) authScreen(); } } },30000);
async function boot() {
  if (location.hash.startsWith('#claim=')) { claimToken = urlCode(location.href); history.replaceState(null,'','/#subscription'); }
  if (location.hash.startsWith('#setup=')) { setupToken = location.hash.slice(7); history.replaceState(null,'','/'); }
  try {
    config = await api('/api/config');
    if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js').catch(() => {});
    try { await refreshSession(); if (claimToken) await claimSubscription(claimToken); await navigate(); }
    catch (error) { if (error.status === 401) authScreen(); else { authScreen(); $('auth-error').textContent = error.message; } }
  } catch { $('boot').textContent = 'The app could not connect. Please refresh when your connection is available.'; }
}
boot();
