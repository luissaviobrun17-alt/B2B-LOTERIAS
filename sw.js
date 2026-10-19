// B2B Loterias - Service Worker Self-Cleanup v4.0
// Forces deletion of all caches and unregisters itself to bust cache for everyone

self.addEventListener('install', function(event) {
    console.log('[SW] Cleanup installed');
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('[SW] Cleanup activated - deleting caches');
    event.waitUntil(
        caches.keys().then(function(names) {
            return Promise.all(
                names.map(function(name) {
                    return caches.delete(name);
                })
            );
        }).then(function() {
            return self.registration.unregister();
        }).then(function() {
            return self.clients.matchAll();
        }).then(function(clients) {
            clients.forEach(function(client) {
                client.navigate(client.url);
            });
        })
    );
});
