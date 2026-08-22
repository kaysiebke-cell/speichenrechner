// Service Worker: macht die Seite ohne Netz benutzbar.
//
// In der Werkstatt ist kein Empfang. Deshalb liegt die ganze Anwendung im
// Cache: beim ersten Aufruf abgelegt, danach von dort geliefert.
//
// Zwei Dinge sind dabei über die Füße gestolpert und deshalb ausdrücklich
// geregelt:
//
// 1. **Der Cache-Name trägt eine Fassung.** Bleibt er gleich, während sich die
//    Dateien ändern, bekommt das Handy weiter die alte Seite – und wundert
//    sich, wo der Nabenkatalog geblieben ist. Bei jeder Änderung an public/
//    muss FASSUNG hochgezählt werden; ein Test hält das fest.
//
// 2. **Für die Seite selbst gilt Netz zuerst.** Sonst müsste man den Browser
//    überreden, eine neue Fassung zu holen. Ist kein Netz da, kommt sie aus
//    dem Cache – der Werkstattfall bleibt also gedeckt.

const FASSUNG = 18;
const CACHE = `speichenrechner-v${FASSUNG}`;

const DATEIEN = [
  ".",
  "index.html",
  "css/stil.css",
  "js/app.js",
  "js/reiter.js",
  "js/speiche.js",
  "js/rechnen.js",
  "js/katalog.js",
  "js/daten.js",
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

/** Ist das der Aufruf einer Seite (nicht einer Datei darin)? */
function istSeitenaufruf(anfrage) {
  return anfrage.mode === "navigate"
    || (anfrage.headers.get("accept") || "").includes("text/html");
}

self.addEventListener("fetch", (ereignis) => {
  const anfrage = ereignis.request;
  if (anfrage.method !== "GET") return;

  if (istSeitenaufruf(anfrage)) {
    // Netz zuerst: eine neue Fassung soll ohne Umwege ankommen.
    ereignis.respondWith(
      fetch(anfrage)
        .then((antwort) => {
          const kopie = antwort.clone();
          caches.open(CACHE).then((cache) => cache.put(anfrage, kopie)).catch(() => {});
          return antwort;
        })
        .catch(() => caches.match(anfrage).then((gefunden) => gefunden
          || caches.match("index.html"))),
    );
    return;
  }

  // Alles andere aus dem Cache, sonst aus dem Netz und dann hinein.
  ereignis.respondWith(
    caches.match(anfrage).then((gefunden) => {
      if (gefunden) return gefunden;
      return fetch(anfrage).then((antwort) => {
        const kopie = antwort.clone();
        caches.open(CACHE).then((cache) => cache.put(anfrage, kopie)).catch(() => {});
        return antwort;
      });
    }),
  );
});
