/* Cache the public shell only. Signal, identity and subscription responses never enter a cache. */
const CACHE = 'signals-shell-v1';
const SHELL = ['/', '/assets/app.css', '/assets/fonts.css', '/assets/app.js', '/assets/icon-192.png', '/assets/icon-512.png', '/assets/manifest.webmanifest'];
self.addEventListener('install', event => { event.waitUntil(caches.open(CACHE).then(cache => cache.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener('activate', event => event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key)))).then(() => self.clients.claim())));
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.origin !== self.location.origin || event.request.method !== 'GET' || url.pathname.startsWith('/api/')) return;
  if (!SHELL.includes(url.pathname) && event.request.mode !== 'navigate') return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request.mode === 'navigate' ? '/' : event.request).then(response => response || new Response('You are offline.', {status:503}))));
});
self.addEventListener('push', event => {
  let data;
  try { data = event.data.json(); } catch { return; }
  event.waitUntil(self.registration.showNotification('Trading Signals', {body:'A new signal is available.',icon:'/assets/icon-192.png',badge:'/assets/icon-192.png',tag:data.event_id || 'signals',data:{url:'/#signals'}}));
});
self.addEventListener('notificationclick', event => {
  event.notification.close();
  event.waitUntil(self.clients.matchAll({type:'window',includeUncontrolled:true}).then(async windows => {
    const existing = windows.find(client => new URL(client.url).origin === self.location.origin);
    if (existing) { await existing.navigate('/#signals'); return existing.focus(); }
    return self.clients.openWindow('/#signals');
  }));
});
self.addEventListener('message', event => {
  if (event.data === 'SIGNED_OUT') self.registration.getNotifications().then(notes => notes.forEach(note => note.close()));
});
