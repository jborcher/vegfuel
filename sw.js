const CACHE = 'vegfuel-v38';
const ASSETS = [
  '/vegfuel/index.html',
  '/vegfuel/manifest.json',
  '/vegfuel/icon-192.png',
  '/vegfuel/icon-512.png',
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(cache => cache.addAll(ASSETS)).catch(() => {})
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  // For navigation requests (HTML pages), always fetch fresh
  // This prevents stale cached HTML for OAuth redirect URLs with ?state=...
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).catch(() => caches.match('/vegfuel/index.html'))
    );
    return;
  }
  // For other assets, cache-first
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request).catch(() => {}))
  );
});
