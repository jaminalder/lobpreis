// Lobpreis service worker — generated; cache name is content-hashed.
const CACHE = '__CACHE_NAME__';
const FILES = __FILES_JSON__;

self.addEventListener('install', function (event) {
  event.waitUntil(
    caches.open(CACHE)
      .then(function (c) { return c.addAll(FILES); })
      .then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys()
      .then(function (keys) {
        return Promise.all(keys.filter(function (k) { return k !== CACHE; })
          .map(function (k) { return caches.delete(k); }));
      })
      .then(function () { return self.clients.claim(); })
  );
});

// Cache-first: instant paint from cache. New deploys land in a freshly-named
// cache during the SW install/activate cycle and become visible on the user's
// next visit (one-extra-load lag, accepted tradeoff for offline-first speed).
self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  var url = new URL(event.request.url);
  if (url.origin !== location.origin) return;

  event.respondWith(
    caches.match(event.request).then(function (hit) {
      if (hit) return hit;
      return fetch(event.request).then(function (resp) {
        if (resp && resp.ok && resp.type === 'basic') {
          var copy = resp.clone();
          caches.open(CACHE).then(function (c) { c.put(event.request, copy); });
        }
        return resp;
      }).catch(function () {
        if (event.request.mode === 'navigate') return caches.match('/');
      });
    })
  );
});
