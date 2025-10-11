self.addEventListener('install', (event) => {
  // Skip waiting to activate the new SW immediately on next load
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Claim clients so the SW controls pages right away
  event.waitUntil(self.clients.claim());
});

// Simple passthrough fetch (hook present for future caching if needed)
self.addEventListener('fetch', () => {});
