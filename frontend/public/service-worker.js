// FREE11 Service Worker v14
// Strategy: JS/CSS=network-first, API=network-only, Navigation=network-first
const CACHE_VERSION = 'free11-v14';
const STATIC_CACHE = `${CACHE_VERSION}-static`;

const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
];

// Install: purge everything and take over immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.map((name) => caches.delete(name)))
    ).then(() => caches.open(STATIC_CACHE))
      .then((cache) => cache.addAll(STATIC_ASSETS))
      .catch(() => {})
  );
  self.skipWaiting();
});

// Activate: purge ALL old caches, claim all clients, force reload
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.map((name) => caches.delete(name)))
    ).then(() => self.clients.claim())
     .then(() => self.clients.matchAll({ type: 'window' }))
     .then((clients) => clients.forEach((client) => client.navigate(client.url)))
  );
});

// Fetch handler
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Skip non-GET
  if (event.request.method !== 'GET') return;

  // Skip cross-origin
  if (url.origin !== self.location.origin) return;

  // RULE 1: API requests = NETWORK ONLY, never cache
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(JSON.stringify({ error: 'offline' }), {
          status: 503,
          headers: { 'Content-Type': 'application/json' },
        })
      )
    );
    return;
  }

  // RULE 2: /live endpoints = NETWORK ONLY
  if (url.pathname.includes('/live')) {
    event.respondWith(fetch(event.request));
    return;
  }

  // RULE 3: Navigation requests = network-first, fallback to cached index
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((c) => c.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match('/index.html').then((r) => r || caches.match('/')))
    );
    return;
  }

  // RULE 3.5: JS/CSS bundles = network-first to always get fresh code
  if (url.pathname.match(/\.(js|css)$/)) {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(STATIC_CACHE).then((c) => c.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // RULE 4: Static assets (images, fonts) = cache-first, network fallback
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(STATIC_CACHE).then((c) => c.put(event.request, clone));
        }
        return response;
      });
    })
  );
});

// Push notifications
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New update from FREE11',
    icon: '/icon-192x192.png',
    badge: '/icon-96x96.png',
    vibrate: [200, 100, 200],
    data: { url: '/' },
  };
  event.waitUntil(self.registration.showNotification('FREE11', options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((list) => {
      for (const client of list) {
        if (client.url.includes(self.location.origin) && 'focus' in client) return client.focus();
      }
      if (clients.openWindow) return clients.openWindow(event.notification.data?.url || '/');
    })
  );
});
