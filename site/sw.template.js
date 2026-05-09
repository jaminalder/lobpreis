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

// Network-first: always try the network so deploys are visible on the next
// load. The cache is populated as a side effect and used only when offline.
self.addEventListener('fetch', function (event) {
  if (event.request.method !== 'GET') return;
  var url = new URL(event.request.url);
  if (url.origin !== location.origin) return;

  event.respondWith(
    fetch(event.request).then(function (resp) {
      if (resp && resp.ok && resp.type === 'basic') {
        var copy = resp.clone();
        caches.open(CACHE).then(function (c) { c.put(event.request, copy); });
      }
      return resp;
    }).catch(function () {
      return caches.match(event.request).then(function (hit) {
        if (hit) return hit;
        if (event.request.mode === 'navigate') return caches.match('/');
      });
    })
  );
});
