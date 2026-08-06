// Nabenkatalog und Felgentypen – Handy-Fassung.
//
// Übertragung von speichenrechner/tabelle.py, katalog.py und felgenkunde.py.
// Die Daten kommen aus daten.js, das aus data/*.json erzeugt wird.
//
// Die Schreibweisen der Herstellertabelle sind von Hand gepflegt und
// entsprechend vielfältig – „47,5 (22,5/25)“, „58 (symmetrisch)“, „Ø100“,
// „33/20“, „k. A.“. Diese Regeln sind über Jahre gewachsen und hier
// wortgetreu übernommen; dass sie dasselbe ergeben wie in Python, prüft
// werkzeuge/pruefwerte_js.mjs für **jede** Nabe und jeden Felgentyp.

import { FELGENTYPEN, FELGEN_FUSSNOTEN, NABEN } from "./daten.js";

// ------------------------------------------------- Schreibweisen der Tabelle

/** Werte, die „nichts bekannt“ bedeuten. */
const LEER = new Set(["", "k. a.", "k.a.", "—", "-", "n/a", "entfällt", "entfaellt"]);

/** Angaben, die von der Lochzahl abhängen und deshalb offen bleiben. */
const MEHRDEUTIG = ["bzw", "je nach", "abhängig"];

export function istLeer(text) {
  const schlicht = (text || "").trim().toLowerCase();
  return LEER.has(schlicht) || schlicht.startsWith("k. a.") || schlicht.startsWith("k.a.");
}

/** Alle Zahlen aus einer Angabe, Komma wie Punkt als Dezimaltrennzeichen. */
export function zahlen(text) {
  if (istLeer(text)) return [];
  const treffer = (text || "").match(/\d+(?:[.,]\d+)?/g) || [];
  return treffer.map((t) => Number.parseFloat(t.replace(",", ".")));
}

/** Lochzahlen aus „20/24/28/32/36“ – nur plausible Werte. */
export function ganzeZahlen(text, von = 8, bis = 64) {
  return zahlen(text).filter((z) => z >= von && z <= bis && Number.isInteger(z));
}

/** Einbaubreiten aus „135/145 (OLD)“ – nur plausible Werte. */
export function masse(text, von = 50.0, bis = 250.0) {
  return zahlen(text).filter((z) => z >= von && z <= bis);
}

export function ersteZahl(text) {
  const werte = zahlen(text);
  return werte.length ? werte[0] : null;
}

function aufteilen(wert, istAbstand) {
  return istAbstand ? [wert / 2, wert / 2] : [wert, wert];
}

/**
 * Liest Angaben wie „47,5 (22,5/25)“, „33/20“, „58 (symmetrisch)“.
 *
 * Bei `istAbstand` gilt eine **einzelne** Zahl als Maß über beide Flansche und
 * wird halbiert; beim Durchmesser gilt sie für beide Seiten. Angaben, die von
 * der Lochzahl abhängen, bleiben absichtlich offen (null).
 */
export function seitenwerte(text, istAbstand) {
  if (istLeer(text)) return null;
  const klein = (text || "").toLowerCase();
  if (MEHRDEUTIG.some((wort) => klein.includes(wort))) return null;

  const sauber = (text || "").replaceAll("*", "").replaceAll("Ø", " ").trim();

  // Das Paar in Klammern ist die genauere Angabe: „50 (25/25)“
  const klammer = sauber.match(/\(([^)]*)\)/);
  if (klammer) {
    const paar = zahlen(klammer[1]);
    if (paar.length >= 2) return [paar[0], paar[1]];
    const davor = zahlen(sauber.slice(0, klammer.index));
    if (davor.length) return aufteilen(davor[0], istAbstand);
    return null;
  }

  const werte = zahlen(sauber);
  if (werte.length >= 2) return [werte[0], werte[1]];
  if (werte.length === 1) return aufteilen(werte[0], istAbstand);
  return null;
}

// ---------------------------------------------------------- Ritzelaufnahmen

/** Bauart für Systeme, die keine Laufradnabe sind (Tretlager-Getriebe). */
export const KEIN_LAUFRAD = "Tretlagergetriebe";

/** Herkunftsangabe für Modelle ohne belegte Maße. */
export const UNGEPRUEFT = "ungeprüft";

/** Reihenfolge zählt: der erste Treffer gewinnt. */
const AUFNAHMEN = [
  ["schraubritzel", "Schraubritzel"],
  ["schraubkranz", "Schraubkranz"],
  ["gewindekranz", "Schraubkranz"],
  ["steckzahnkranz", "Steckzahnkranz"],
  ["push-on", "Steckzahnkranz"],
  ["steckritzel", "Steckritzel"],
  ["micro spline", "Kassette"],
  ["freilaufkörper", "Kassette"],
  ["kassette", "Kassette"],
  ["hg", "Kassette"],
  ["xd", "Kassette"],
];

/**
 * Wie die Ritzel sitzen – unabhängig von der Bauart.
 *
 * Nur ein führendes „entfällt“ verneint. Auf „kein Freilauf“ zu prüfen wäre
 * falsch: „Schraubkranz (klassisches Gewinde, kein Freilaufkörper)“ nennt sehr
 * wohl eine Aufnahme.
 */
export function aufnahme(nabe) {
  const text = (nabe.freilauf || "").toLowerCase();
  if (!text || text.startsWith("k. a.")) return "";
  if (text.startsWith("entfällt")) {
    return text.includes("singlespeed") ? "Singlespeed" : "";
  }
  for (const [stichwort, name] of AUFNAHMEN) {
    if (text.includes(stichwort)) return name;
  }
  return "";
}

/** Alle Schubladen, in die diese Nabe gehört – Bauart und Aufnahme nebeneinander. */
export function merkmale(nabe) {
  const gefunden = [];
  if (nabe.art) gefunden.push(nabe.art);
  if ((nabe.freilauf || "").toLowerCase().includes("vorderrad")
      && !gefunden.includes("Vorderrad")) {
    gefunden.push("Vorderrad");
  }
  const auf = aufnahme(nabe);
  if (auf && !gefunden.includes(auf)) gefunden.push(auf);
  return gefunden;
}

export const flanschabstaende = (nabe) => seitenwerte(nabe.flanschabstand, true);
export const flanschdurchmesserPaar = (nabe) => seitenwerte(nabe.flanschdurchmesser, false);
export const speichenlochMm = (nabe) => ersteZahl(nabe.speichenloch);
export const lochzahlen = (nabe) => ganzeZahlen(nabe.lochzahl);
export const einbaubreiten = (nabe) => masse(nabe.einbaubreite);

/** True, wenn sich mit dieser Nabe sofort rechnen lässt. */
export function hatFlanschmasse(nabe) {
  return flanschabstaende(nabe) !== null && flanschdurchmesserPaar(nabe) !== null;
}

/** False bei Tretlager-Getrieben – die haben kein Speichenloch. */
export const einspeichbar = (nabe) => nabe.art !== KEIN_LAUFRAD;

/** „Hersteller Modell“ – ohne Dopplung, wenn beides gleich anfängt. */
export function bezeichnung(nabe) {
  const hersteller = nabe.hersteller || "";
  const modell = nabe.modell || "";
  if (modell.toLowerCase().startsWith(hersteller.toLowerCase())) return modell;
  return `${hersteller} ${modell}`.trim();
}

/** Zeile für die Auswahlliste – Name plus die wichtigsten Kennwerte. */
export function listentext(nabe) {
  const teile = [bezeichnung(nabe)];
  if (hatFlanschmasse(nabe)) teile.push("✓ mit Flanschmaßen");
  if (!istLeer(nabe.einbaubreite)) teile.push(`${nabe.einbaubreite} mm`);
  if (!istLeer(nabe.lochzahl)) teile.push(`${nabe.lochzahl} Loch`);
  if (nabe.quelle) teile.push(nabe.quelle === UNGEPRUEFT ? "ungeprüft" : "nachgetragen");
  return teile.join("  ·  ");
}

// ------------------------------------------------------------------- Suchen

/**
 * Vergleich wie Pythons `sorted()`: nach Zeichencode, nicht nach deutschen
 * Regeln. Dadurch steht „KT" vor „Kindernay" und „SON" vor „Shimano" – etwas
 * ungewohnt, aber beide Fassungen zeigen dieselbe Reihenfolge, und das prüft
 * werkzeuge/pruefwerte_js.mjs. `localeCompare` würde hier abweichen.
 */
const wieInPython = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

/** Alle einspeichbaren Naben. */
export const alleNaben = () => NABEN.filter(einspeichbar);

/** Die vorkommenden Merkmale mit ihrer Anzahl, häufigste zuerst. */
export function artenMitAnzahl() {
  const zaehler = new Map();
  for (const nabe of alleNaben()) {
    for (const merkmal of merkmale(nabe)) {
      zaehler.set(merkmal, (zaehler.get(merkmal) || 0) + 1);
    }
  }
  return [...zaehler.entries()].sort((a, b) => b[1] - a[1] || wieInPython(a[0], b[0]));
}

/** Hersteller mit der Zahl ihrer Naben, wahlweise nur zu einem Merkmal. */
export function herstellerMitAnzahl(art = "") {
  const zaehler = new Map();
  for (const nabe of alleNaben()) {
    if (!nabe.hersteller) continue;
    if (art && !merkmale(nabe).includes(art)) continue;
    zaehler.set(nabe.hersteller, (zaehler.get(nabe.hersteller) || 0) + 1);
  }
  return [...zaehler.entries()].sort((a, b) => wieInPython(a[0], b[0]));
}

/**
 * Naben zu Merkmal, Hersteller und Suchtext.
 *
 * Naben mit vollständigen Flanschmaßen stehen zuerst – mit ihnen lässt sich
 * ohne Nachmessen rechnen.
 */
export function suche({ art = "", hersteller = "", text = "" } = {}) {
  const begriffe = text.toLowerCase().split(/\s+/).filter(Boolean);
  const treffer = alleNaben().filter((nabe) => {
    if (hersteller && nabe.hersteller !== hersteller) return false;
    if (art && !merkmale(nabe).includes(art)) return false;
    if (begriffe.length) {
      const suchtext = [
        nabe.hersteller, nabe.modell, nabe.art, nabe.bremse,
        nabe.lochzahl, nabe.einbaubreite, nabe.freilauf, nabe.quelle,
      ].join(" ").toLowerCase();
      if (!begriffe.every((b) => suchtext.includes(b))) return false;
    }
    return true;
  });
  return treffer.sort((a, b) => {
    const fertig = Number(hatFlanschmasse(b)) - Number(hatFlanschmasse(a));
    if (fertig) return fertig;
    return wieInPython(bezeichnung(a).toLowerCase(), bezeichnung(b).toLowerCase());
  });
}

// -------------------------------------------------------------- Felgentypen

/** Anhaltswerte für die Speichenspannung an der Felge, in Newton. */
export const SPANNUNG_JE_MATERIAL = {
  Stahl: [500.0, 800.0],
  Aluminium: [800.0, 1100.0],
  Carbon: [900.0, 1200.0],
};

const MATERIAL_REIHENFOLGE = ["Stahl", "Aluminium", "Carbon", "Titan"];

const MATERIALWOERTER = [
  ["stahl", "Stahl"],
  ["alumini", "Aluminium"],
  ["carbon", "Carbon"],
  ["cfk", "Carbon"],
  ["titan", "Titan"],
];

/** Unter diesem ERD ist ein Laufrad kleiner als 20 Zoll. */
export const ERD_KINDERRAD = 360.0;

export const felgentypen = () => FELGENTYPEN;
export const felgenFussnoten = () => FELGEN_FUSSNOTEN;

export function felgentyp(name) {
  if (!name) return null;
  return FELGENTYPEN.find((typ) => typ.name === name) || null;
}

export function felgenkategorien() {
  const gefunden = [];
  for (const typ of FELGENTYPEN) {
    if (typ.kategorie && !gefunden.includes(typ.kategorie)) gefunden.push(typ.kategorie);
  }
  return gefunden;
}

/** Die genannten Werkstoffe, schwächster zuerst. */
export function materialien(typ) {
  const text = (typ.material || "").toLowerCase();
  const gefunden = new Set();
  for (const [wort, name] of MATERIALWOERTER) {
    if (text.includes(wort)) gefunden.add(name);
  }
  return MATERIAL_REIHENFOLGE.filter((m) => gefunden.has(m));
}

/** 0 = ohne Ösen, 1 = einfach genietet, 2 = doppelt genietet. */
export function oesenStufe(typ) {
  const text = (typ.oesung || "").toLowerCase();
  if (text.includes("doppelt")) return 2;
  if (text.includes("einfach") || text.includes("genietet") || text.includes("geöst")) return 1;
  return 0;
}

/** Bei mehreren Materialien begrenzt das schwächere – es gibt nach. */
export function spannungsbereich(typ) {
  for (const werkstoff of materialien(typ)) {
    const bereich = SPANNUNG_JE_MATERIAL[werkstoff];
    if (bereich) return bereich;
  }
  return null;
}

/** True, wenn die Tabelle diesen Typ für Kinderräder ausschließt. */
export function nurAb20Zoll(typ) {
  return (typ.kindergroessen || "").toLowerCase().includes("nicht üblich");
}

/** Was am gerechneten Laufrad nicht zu dieser Bauform passt. */
export function felgenwarnungen(typ, erd = 0, spannung = 0) {
  const meldungen = [];
  if (!typ) return meldungen;

  const bereich = spannungsbereich(typ);
  const werkstoffe = materialien(typ);
  const materialtext = werkstoffe.length ? werkstoffe[0] : (typ.material || "diese Felge");

  if (bereich && spannung > 0) {
    const [unten, oben] = bereich;
    if (spannung > oben) {
      meldungen.push(`${Math.round(spannung)} N liegen über dem, was für ${materialtext} `
        + `üblich ist (${unten}–${oben} N). Ohne Herstellerfreigabe ist das zu viel.`);
    } else if (spannung < unten) {
      meldungen.push(`${Math.round(spannung)} N sind für ${materialtext} wenig `
        + `(${unten}–${oben} N sind üblich) – zu locker gespannte Speichen brechen am Bogen.`);
    }
  }

  if (erd > 0 && erd < ERD_KINDERRAD && nurAb20Zoll(typ)) {
    meldungen.push(`Der ERD von ${Math.round(erd)} mm gehört zu einem Laufrad unter 20 Zoll. `
      + `Für diese Größen führt die Tabelle „${typ.name}“ als nicht üblich.`);
  }
  return meldungen;
}

/** Eine Zeile mit dem Wichtigsten – für die Anzeige unter der Auswahl. */
export function felgenbeschreibung(typ) {
  if (!typ) return "";
  const zeilen = [typ.kategorie ? `${typ.name} · ${typ.kategorie}` : typ.name];

  const zweite = [typ.beschreibung, typ.material];
  zweite.push(oesenStufe(typ) ? `Ösen: ${typ.oesung}` : "ohne Ösen");
  zeilen.push(zweite.filter(Boolean).join("  ·  "));

  const dritte = [];
  if (typ.einsatz) dritte.push(typ.einsatz);
  if (typ.kindergroessen) dritte.push(`Kinder: ${typ.kindergroessen}`);
  const bereich = spannungsbereich(typ);
  if (bereich) dritte.push(`${bereich[0]}–${bereich[1]} N üblich`);
  if (dritte.length) zeilen.push(dritte.join("  ·  "));

  return zeilen.join("\n");
}
