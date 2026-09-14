// JARVIS PWA Service Worker
const CACHE_NAME = 'jarvis-mobile-v1';
const ASSETS_TO_CACHE = [
  '/app',
  '/mobile/index.html',
  '/mobile/style.css',
  '/mobile/app.js',
  '/mobile/manifest.json'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => console.log('Cache prefetch bypass:', err));
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  // Network first for API endpoints, Cache fallback for static assets
  if (event.request.url.includes('/api/') || event.request.url.includes('/ws/')) {
    return; // Pass through to network
  }

  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
