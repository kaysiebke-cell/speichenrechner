// Verdrahtung der Handy-Fassung: Formular lesen, rechnen, anzeigen.
//
// Die Rechnung selbst steht in rechnen.js und wird gegen die Prüfwerte der
// Python-Fassung geprüft. Hier passiert nur Oberfläche.

import { berechne, einkaufsliste, grad, mm, ueblicheKreuzungen, zahl } from "./rechnen.js";
import {
  artenMitAnzahl, bezeichnung, felgenbeschreibung, felgenFussnoten, felgenkategorien,
  felgentyp, felgentypen, felgenwarnungen, flanschabstaende, flanschdurchmesserPaar,
  herstellerMitAnzahl, listentext, lochzahlen, speichenlochMm, suche,
} from "./katalog.js";
import { FELGEN_VORLAGEN, NABEN_VORLAGEN } from "./daten.js";

const SPEICHER = "speichenrechner.eingaben";

const felder = {
  flanschdurchmesser_links: "flansch-d-links",
  flanschdurchmesser_rechts: "flansch-d-rechts",
  flanschabstand_links: "flansch-a-links",
  flanschabstand_rechts: "flansch-a-rechts",
  speichenloch: "speichenloch",
  erd: "erd",
  versatz: "versatz",
  speichenzahl: "speichenzahl",
  kreuzungen_links: "kreuzungen-links",
  kreuzungen_rechts: "kreuzungen-rechts",
  verteilung: "verteilung",
  schritt: "rundung",
};

const $ = (id) => document.getElementById(id);
const anzeige = {
  laengeLinks: $("laenge-links"),
  laengeRechts: $("laenge-rechts"),
  genauLinks: $("genau-links"),
  genauRechts: $("genau-rechts"),
  bestellen: $("bestellen"),
  kennwerte: $("kennwerte"),
  hinweis: $("hinweis"),
};

/** Liest das Formular in die Feldnamen, die rechnen.js erwartet. */
function eingabeLesen() {
  const werte = {};
  for (const [name, id] of Object.entries(felder)) {
    const feld = $(id);
    werte[name] = feld.tagName === "SELECT" && name === "verteilung"
      ? feld.value
      : Number(feld.value.replace(",", "."));
  }
  werte.verteilung = $("verteilung").value;
  werte.speichenzahl = Math.round(werte.speichenzahl);
  werte.kreuzungen_links = Math.round(werte.kreuzungen_links);
  werte.kreuzungen_rechts = Math.round(werte.kreuzungen_rechts);
  return werte;
}

/**
 * Plausibilitätsprüfung – die gleichen Fälle wie am PC, nur die dringendsten.
 * Der Rest (Bewertung, Felgentypen) kommt mit den späteren Stufen.
 */
function hinweise(eingabe, ergebnis) {
  const meldungen = [];
  const { speichenzahl, verteilung } = eingabe;

  if (verteilung === "2:1") {
    if (speichenzahl % 3 !== 0) {
      meldungen.push(`Für eine 2:1-Einspeichung muss die Speichenzahl durch 3 teilbar sein – `
        + `${speichenzahl} ist es nicht.`);
    }
  } else if (speichenzahl % 4 !== 0) {
    meldungen.push("Die Speichenzahl ist nicht durch 4 teilbar – die Seiten lassen sich "
      + "nicht gleichmäßig aufteilen.");
  }

  for (const [name, seite] of [["Links", ergebnis.links], ["Rechts", ergebnis.rechts]]) {
    if (seite.sehnenwinkel >= 180.0) {
      meldungen.push(`${name}: ${seite.kreuzungen}-fach gekreuzt ist bei ${seite.speichen} `
        + "Speichen auf dieser Seite geometrisch nicht möglich.");
    } else if (seite.kreuzungen > seite.speichen / 4) {
      meldungen.push(`${name}: ${seite.kreuzungen}-fach ist bei ${seite.speichen} Speichen `
        + "auf dieser Seite sehr hoch – die Speichen laufen flach am Flansch aus.");
    }
    if (seite.kreuzungen === 0) {
      meldungen.push(`${name}: radial eingespeicht – nur bei dafür freigegebenen Naben.`);
    }
  }

  if (eingabe.erd < 150 || eingabe.erd > 700) {
    meldungen.push(`Der ERD von ${zahl(eingabe.erd, 0)} mm liegt außerhalb des üblichen `
      + "Bereichs (etwa 170–640 mm). Bitte nachmessen.");
  }

  const unterschied = Math.abs(ergebnis.links.laenge - ergebnis.rechts.laenge);
  if (unterschied >= 0.05 && !ergebnis.gleicheBestelllaenge) {
    meldungen.push(`Links und rechts unterscheiden sich um ${zahl(unterschied)} mm – `
      + "die Speichen nicht vertauschen.");
  }

  // Was am gerechneten Laufrad nicht zur gewählten Felgenbauform passt.
  const typ = felgentyp($("felgentyp").value);
  if (typ) meldungen.push(...felgenwarnungen(typ, eingabe.erd, 0));

  return meldungen;
}

function anzeigen() {
  const eingabe = eingabeLesen();
  let ergebnis;
  try {
    ergebnis = berechne(eingabe);
  } catch (fehler) {
    anzeige.laengeLinks.textContent = "–";
    anzeige.laengeRechts.textContent = "–";
    anzeige.bestellen.textContent = "";
    anzeige.kennwerte.textContent = "";
    anzeige.hinweis.textContent = fehler.message;
    anzeige.hinweis.hidden = false;
    return;
  }

  const { links, rechts } = ergebnis;
  anzeige.laengeLinks.textContent = zahl(links.laenge_gerundet);
  anzeige.laengeRechts.textContent = zahl(rechts.laenge_gerundet);
  anzeige.genauLinks.textContent = `exakt ${mm(links.laenge, 2)}`;
  anzeige.genauRechts.textContent = `exakt ${mm(rechts.laenge, 2)}`;
  anzeige.bestellen.textContent = `Zu bestellen: ${einkaufsliste(ergebnis).join("   ·   ")}`;

  anzeige.kennwerte.textContent = [
    `Speichenwinkel ${grad(links.speichenwinkel)} / ${grad(rechts.speichenwinkel)}`,
    `Winkel an der Felge ${grad(links.felgenwinkel)} / ${grad(rechts.felgenwinkel)}`,
    `Spannung ${Math.round(ergebnis.spannung_links_prozent)} / `
      + `${Math.round(ergebnis.spannung_rechts_prozent)} %`,
    `${links.speichen} + ${rechts.speichen} Speichen, `
      + `${links.kreuzungen}- und ${rechts.kreuzungen}-fach`
      + ` (üblich: ${ueblicheKreuzungen(links.speichen)}-fach)`,
  ].join("  ·  ");

  const meldungen = hinweise(eingabe, ergebnis);
  anzeige.hinweis.textContent = meldungen.join("  ");
  anzeige.hinweis.hidden = meldungen.length === 0;

  sichern(eingabe);
}

/** Zuletzt eingegebene Werte behalten – wie am PC. */
function sichern(eingabe) {
  try {
    localStorage.setItem(SPEICHER, JSON.stringify(eingabe));
  } catch (_fehler) {
    // Privater Modus o. Ä. – dann eben ohne Gedächtnis.
  }
}

function laden() {
  let gespeichert;
  try {
    gespeichert = JSON.parse(localStorage.getItem(SPEICHER) || "null");
  } catch (_fehler) {
    return;
  }
  if (!gespeichert) return;
  for (const [name, id] of Object.entries(felder)) {
    if (gespeichert[name] === undefined) continue;
    $(id).value = gespeichert[name];
  }
  $("gekoppelt").checked =
    gespeichert.kreuzungen_links === gespeichert.kreuzungen_rechts;
  $("kreuzungen-rechts").disabled = $("gekoppelt").checked;
}

// ----------------------------------------------------------------- Katalog

/** Füllt eine Liste mit `[wert, beschriftung]`-Paaren. */
function listeFuellen(liste, paare, vorher = "") {
  liste.innerHTML = "";
  for (const [wert, text] of paare) {
    const eintrag = document.createElement("option");
    eintrag.value = wert;
    eintrag.textContent = text;
    liste.append(eintrag);
  }
  liste.value = paare.some(([w]) => w === vorher) ? vorher : (paare[0]?.[0] ?? "");
}

/** Die Nabenliste zu Filter und Suchtext neu aufbauen. */
function nabenlisteFuellen() {
  const art = $("nabenart").value;
  const hersteller = $("nabenhersteller").value;
  const text = $("nabensuche").value.trim();
  const treffer = suche({ art, hersteller, text });

  const vorlagen = art || hersteller || text
    ? NABEN_VORLAGEN.filter((v) => !hersteller
        && (!art || v.art === art || v.aufnahme === art)
        && (!text || v.name.toLowerCase().includes(text.toLowerCase())))
    : NABEN_VORLAGEN;

  const paare = [["", `— eigene Werte —  (${treffer.length + vorlagen.length} zur Wahl)`]];
  for (const [nummer, v] of vorlagen.entries()) paare.push([`v${nummer}`, v.name]);
  for (const nabe of treffer) paare.push([`k${nabe.hersteller}|${nabe.modell}`, listentext(nabe)]);
  listeFuellen($("nabenliste"), paare);
  $("nabeninfo").textContent = "";
}

/** Eine gewählte Nabe in die Felder übernehmen. */
function nabeUebernehmen() {
  const wahl = $("nabenliste").value;
  if (!wahl) return;

  if (wahl.startsWith("v")) {
    const v = NABEN_VORLAGEN[Number(wahl.slice(1))];
    $("flansch-d-links").value = v.flanschdurchmesser_links;
    $("flansch-d-rechts").value = v.flanschdurchmesser_rechts;
    $("flansch-a-links").value = v.flanschabstand_links;
    $("flansch-a-rechts").value = v.flanschabstand_rechts;
    $("speichenloch").value = v.speichenloch;
    $("nabeninfo").textContent = `${v.name} übernommen.`;
    anzeigen();
    return;
  }

  const schluessel = wahl.slice(1);
  const nabe = suche().find((n) => `${n.hersteller}|${n.modell}` === schluessel);
  if (!nabe) return;

  const abstand = flanschabstaende(nabe);
  const durchmesser = flanschdurchmesserPaar(nabe);
  const loch = speichenlochMm(nabe);
  const zahlenDerLoecher = lochzahlen(nabe);

  if (abstand && durchmesser) {
    $("flansch-a-links").value = abstand[0];
    $("flansch-a-rechts").value = abstand[1];
    $("flansch-d-links").value = durchmesser[0];
    $("flansch-d-rechts").value = durchmesser[1];
  }
  if (loch) $("speichenloch").value = loch;
  if (zahlenDerLoecher.length) {
    const jetzt = Number($("speichenzahl").value);
    if (!zahlenDerLoecher.includes(jetzt)) {
      $("speichenzahl").value = Math.max(...zahlenDerLoecher);
    }
  }

  $("nabeninfo").textContent = abstand && durchmesser
    ? `${bezeichnung(nabe)} übernommen – einschließlich der Flanschmaße. `
      + "Vor dem Bestellen trotzdem gegenprüfen."
    : `${bezeichnung(nabe)} übernommen. Flanschabstand und Flansch-Ø stehen in der `
      + "Tabelle nicht – die bitte nachmessen.";
  anzeigen();
}

/** Die Felgentypen zur gewählten Kategorie neu aufbauen. */
function felgentypenFuellen() {
  const kategorie = $("felgenkategorie").value;
  const vorher = $("felgentyp").value;
  const paare = [["", "kein bestimmter Typ"]];
  for (const typ of felgentypen()) {
    if (!kategorie || typ.kategorie === kategorie) paare.push([typ.name, typ.name]);
  }
  listeFuellen($("felgentyp"), paare, vorher);
}

function felgeninfoSetzen() {
  const typ = felgentyp($("felgentyp").value);
  const fussnoten = felgenFussnoten();
  $("felgeninfo").textContent = typ
    ? felgenbeschreibung(typ)
    : (fussnoten[0] || "");
}

function katalogAufbauen() {
  const gesamt = suche().length;
  listeFuellen($("nabenart"),
    [["", `alle Arten (${gesamt})`], ...artenMitAnzahl().map(([a, n]) => [a, `${a} (${n})`])]);
  herstellerFuellen();
  nabenlisteFuellen();

  listeFuellen($("felgenvorlage"),
    [["", "— eigene Werte —"],
     ...FELGEN_VORLAGEN.map((f, i) => [String(i), f.name])]);

  listeFuellen($("felgenkategorie"),
    [["", "alle Kategorien"], ...felgenkategorien().map((k) => [k, k])]);
  felgentypenFuellen();
  felgeninfoSetzen();
}

function herstellerFuellen() {
  const art = $("nabenart").value;
  const mitAnzahl = herstellerMitAnzahl(art);
  const gesamt = mitAnzahl.reduce((summe, [, n]) => summe + n, 0);
  const vorher = $("nabenhersteller").value;
  listeFuellen($("nabenhersteller"),
    [["", `alle Hersteller (${gesamt})`],
     ...mitAnzahl.map(([name, n]) => [name, `${name.split(" (")[0]} (${n})`])],
    vorher);
}

$("nabenart").addEventListener("change", () => { herstellerFuellen(); nabenlisteFuellen(); });
$("nabenhersteller").addEventListener("change", nabenlisteFuellen);
$("nabensuche").addEventListener("input", nabenlisteFuellen);
$("nabenliste").addEventListener("change", nabeUebernehmen);

$("felgenvorlage").addEventListener("change", () => {
  const wahl = $("felgenvorlage").value;
  if (wahl === "") return;
  const felge = FELGEN_VORLAGEN[Number(wahl)];
  $("erd").value = felge.erd;
  $("versatz").value = felge.versatz;
  anzeigen();
});
$("felgenkategorie").addEventListener("change", () => {
  felgentypenFuellen();
  felgeninfoSetzen();
  anzeigen();
});
$("felgentyp").addEventListener("change", () => { felgeninfoSetzen(); anzeigen(); });

// ------------------------------------------------------------- Verdrahtung

for (const id of Object.values(felder)) {
  $(id).addEventListener("input", anzeigen);
  $(id).addEventListener("change", anzeigen);
}

$("kreuzungen-links").addEventListener("input", () => {
  if ($("gekoppelt").checked) $("kreuzungen-rechts").value = $("kreuzungen-links").value;
});

$("gekoppelt").addEventListener("change", () => {
  const gekoppelt = $("gekoppelt").checked;
  $("kreuzungen-rechts").disabled = gekoppelt;
  if (gekoppelt) $("kreuzungen-rechts").value = $("kreuzungen-links").value;
  anzeigen();
});

$("zuruecksetzen").addEventListener("click", () => {
  try {
    localStorage.removeItem(SPEICHER);
  } catch (_fehler) { /* nichts zu tun */ }
  location.reload();
});

katalogAufbauen();
laden();
$("kreuzungen-rechts").disabled = $("gekoppelt").checked;
anzeigen();

// Ohne Netz nutzbar: der Service Worker legt die Seite in den Cache.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => {
      // Ohne Service Worker läuft die Seite auch, nur nicht offline.
    });
  });
}
