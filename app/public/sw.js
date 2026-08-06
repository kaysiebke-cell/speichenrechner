// Service Worker: macht die Seite ohne Netz benutzbar.
//
// In der Werkstatt ist kein Empfang. Deshalb liegt die ganze Anwendung im
// Cache: beim ersten Aufruf abgelegt, danach von dort geliefert. Die
// Versionsnummer im Cache-Namen erneuert den Bestand bei einer neuen Fassung –
// alte Caches werden bei der Aktivierung gelöscht.

const CACHE = "speichenrechner-v1";

const DATEIEN = [
  ".",
  "index.html",
  "css/stil.css",
  "js/app.js",
  "js/rechnen.js",
  "manifest.json",
  "icons/icon-192.png",
  "icons/icon-512.png",
];

self.addEventListener("install", (ereignis) => {
  ereignis.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(DATEIEN)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (ereignis) => {
  ereignis.waitUntil(
    caches.keys()
      .then((namen) => Promise.all(namen.filter((n) => n !== CACHE).map((n) => caches.delete(n))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (ereignis) => {
  if (ereignis.request.method !== "GET") return;
  ereignis.respondWith(
    caches.match(ereignis.request).then((gefunden) => {
      if (gefunden) return gefunden;
      return fetch(ereignis.request).then((antwort) => {
        // Nachladen still in den Cache legen, damit es beim nächsten Mal da ist.
        const kopie = antwort.clone();
        caches.open(CACHE).then((cache) => cache.put(ereignis.request, kopie)).catch(() => {});
        return antwort;
      }).catch(() => caches.match("index.html"));
    }),
  );
});
