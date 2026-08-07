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

import { berechne } from "../app/public/js/rechnen.js";
import * as kat from "../app/public/js/katalog.js";

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
  // Die Speichen-Ebene: Spannung je Seite, Dehnung, Korrektur, Ton, Gewicht.
  // Ohne Speichensatz müssen hier auf beiden Seiten Nullen stehen.
  ["spannung_links", (e) => e.links.spannung],
  ["spannung_rechts", (e) => e.rechts.spannung],
  ["dehnung_links", (e) => e.links.dehnung],
  ["dehnung_rechts", (e) => e.rechts.dehnung],
  ["korrektur_links", (e) => e.links.korrektur],
  ["korrektur_rechts", (e) => e.rechts.korrektur],
  ["drahtspannung_links", (e) => e.links.drahtspannung],
  ["drahtspannung_rechts", (e) => e.rechts.drahtspannung],
  ["frequenz_links", (e) => e.links.frequenz],
  ["frequenz_rechts", (e) => e.rechts.frequenz],
  ["gewicht_links", (e) => e.links.gewicht],
  ["gewicht_rechts", (e) => e.rechts.gewicht],
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

// ------------------------------------------------------- Katalog und Felgen
//
// Nicht nur ein paar Stichproben: jede Nabe und jeder Felgentyp. Die
// Schreibweisen der Herstellertabelle sind über Jahre gewachsen; liest die
// JavaScript-Fassung eine davon anders, steht auf dem Handy eine falsche Nabe.

const gleich = (a, b) => JSON.stringify(a ?? null) === JSON.stringify(b ?? null);

const k = daten.katalog ?? { naben: [], felgen: [], arten: [], hersteller: [] };
const nachSchluessel = new Map(
  kat.felgentypen ? [] : [],
);

// Naben aus daten.js über „Hersteller|Modell" auffindbar machen.
const jsNaben = new Map();
for (const nabe of (await import("../app/public/js/daten.js")).NABEN) {
  jsNaben.set(`${nabe.hersteller}|${nabe.modell}`, nabe);
}

for (const erwartet of k.naben) {
  const nabe = jsNaben.get(erwartet.schluessel);
  geprueft += 1;
  if (!nabe) {
    abweichungen.push(`  Nabe fehlt in daten.js: ${erwartet.schluessel}`);
    continue;
  }
  const bekommen = {
    flanschabstaende: kat.flanschabstaende(nabe),
    flanschdurchmesser_paar: kat.flanschdurchmesserPaar(nabe),
    speichenloch_mm: kat.speichenlochMm(nabe),
    lochzahlen: kat.lochzahlen(nabe),
    einbaubreiten: kat.einbaubreiten(nabe),
    aufnahme: kat.aufnahme(nabe),
    merkmale: kat.merkmale(nabe),
    hat_flanschmasse: kat.hatFlanschmasse(nabe),
    einspeichbar: kat.einspeichbar(nabe),
    bezeichnung: kat.bezeichnung(nabe),
  };
  for (const [feld, wert] of Object.entries(bekommen)) {
    geprueft += 1;
    if (!gleich(wert, erwartet[feld])) {
      abweichungen.push(
        `  ${erwartet.schluessel} · ${feld}: Python ${JSON.stringify(erwartet[feld])} `
        + `→ JavaScript ${JSON.stringify(wert)}`,
      );
    }
  }
}

for (const erwartet of k.felgen) {
  const typ = kat.felgentyp(erwartet.name);
  geprueft += 1;
  if (!typ) {
    abweichungen.push(`  Felgentyp fehlt in daten.js: ${erwartet.name}`);
    continue;
  }
  const bekommen = {
    materialien: kat.materialien(typ),
    oesen_stufe: kat.oesenStufe(typ),
    spannungsbereich: kat.spannungsbereich(typ),
    nur_ab_20_zoll: kat.nurAb20Zoll(typ),
  };
  for (const [feld, wert] of Object.entries(bekommen)) {
    geprueft += 1;
    if (!gleich(wert, erwartet[feld])) {
      abweichungen.push(
        `  ${erwartet.name} · ${feld}: Python ${JSON.stringify(erwartet[feld])} `
        + `→ JavaScript ${JSON.stringify(wert)}`,
      );
    }
  }
}

// Die Zähler der Filterlisten müssen auf beiden Seiten gleich herauskommen.
for (const [name, paare, holen] of [
  ["Arten", k.arten, kat.artenMitAnzahl()],
  ["Hersteller", k.hersteller, kat.herstellerMitAnzahl()],
]) {
  geprueft += 1;
  const jsPaare = holen.map(([a, b]) => [a, b]);
  if (!gleich(jsPaare, paare)) {
    abweichungen.push(`  ${name} mit Anzahl weichen ab:`);
    abweichungen.push(`    Python     ${JSON.stringify(paare)}`);
    abweichungen.push(`    JavaScript ${JSON.stringify(jsPaare)}`);
  }
}

console.log(
  `${daten.faelle.length} Rechenfälle, ${k.naben.length} Naben und ${k.felgen.length} `
  + `Felgentypen – ${geprueft} Werte gegen die Python-Fassung geprüft`,
);
if (abweichungen.length === 0) {
  console.log("Beide Fassungen rechnen gleich.");
  process.exit(0);
}
console.log(`\n${abweichungen.length} Abweichungen:`);
for (const zeile of abweichungen) console.log(zeile);
process.exit(1);
