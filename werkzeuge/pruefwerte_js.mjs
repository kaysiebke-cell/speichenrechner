#!/usr/bin/env node
// Prüft die JavaScript-Rechnung gegen die Prüfwerte aus der Python-Rechnung.
//
// Aufruf:  node werkzeuge/pruefwerte_js.mjs
//
// Die Rechnung gibt es zweimal – Python für den PC, JavaScript fürs Handy.
// Diese Prüfung ist das Band dazwischen: sie lädt data/pruefwerte.json, das
// Python erzeugt hat, und verlangt von der JavaScript-Fassung dieselben Zahlen.
// Rückgabewert 1, wenn eine abweicht.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { berechne } from "../public/js/rechnen.js";

const hier = dirname(fileURLToPath(import.meta.url));
const datei = join(hier, "..", "data", "pruefwerte.json");
const daten = JSON.parse(readFileSync(datei, "utf-8"));

// Fließkomma über zwei Sprachen: bis auf diese Genauigkeit muss es stimmen.
const GRENZE = 1e-9;

const zuPruefen = [
  ["laenge_links", (e) => e.links.laenge],
  ["laenge_rechts", (e) => e.rechts.laenge],
  ["bestell_links", (e) => e.links.laenge_gerundet],
  ["bestell_rechts", (e) => e.rechts.laenge_gerundet],
  ["speichenwinkel_links", (e) => e.links.speichenwinkel],
  ["speichenwinkel_rechts", (e) => e.rechts.speichenwinkel],
  ["felgenwinkel_links", (e) => e.links.felgenwinkel],
  ["felgenwinkel_rechts", (e) => e.rechts.felgenwinkel],
  ["sehnenwinkel_links", (e) => e.links.sehnenwinkel],
  ["sehnenwinkel_rechts", (e) => e.rechts.sehnenwinkel],
  ["lochabstand_links", (e) => e.links.lochabstand],
  ["lochabstand_rechts", (e) => e.rechts.lochabstand],
  ["speichen_links", (e) => e.links.speichen],
  ["speichen_rechts", (e) => e.rechts.speichen],
  ["spannung_links_prozent", (e) => e.spannung_links_prozent],
  ["spannung_rechts_prozent", (e) => e.spannung_rechts_prozent],
];

let geprueft = 0;
const abweichungen = [];

for (const fall of daten.faelle) {
  const ergebnis = berechne(fall.eingabe);
  for (const [feld, holen] of zuPruefen) {
    const erwartet = fall.erwartet[feld];
    const bekommen = holen(ergebnis);
    geprueft += 1;
    if (Math.abs(bekommen - erwartet) > GRENZE) {
      abweichungen.push(
        `  ${fall.name} · ${feld}: Python ${erwartet} → JavaScript ${bekommen}`,
      );
    }
  }
}

console.log(
  `${daten.faelle.length} Prüffälle, ${geprueft} Werte gegen die Python-Rechnung geprüft`,
);
if (abweichungen.length === 0) {
  console.log("Beide Fassungen rechnen gleich.");
  process.exit(0);
}
console.log(`\n${abweichungen.length} Abweichungen:`);
for (const zeile of abweichungen) console.log(zeile);
process.exit(1);
