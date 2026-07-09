
const CACHE_NAME = "kagendo-v6-cache";

const urlsToCache = [
    "/",
    "/eggs",
    "/sales",
    "/add-eggs"
];

// INSTALL (CACHE CORE PAGES)
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(urlsToCache);
        })
    );
});

// ACTIVATE (CLEAR OLD CACHE)
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(keys => {
            return Promise.all(
                keys.map(key => {
                    if (key !== CACHE_NAME) {
                        return caches.delete(key);
                    }
                })
            );
        })
    );
});

// FETCH (OFFLINE-FIRST)
self.addEventListener("fetch", event => {
    event.respondWith(
        fetch(event.request).catch(() => {
            return caches.match(event.request)
                || new Response("📴 Offline - Kagendo System");
        })
    );
});