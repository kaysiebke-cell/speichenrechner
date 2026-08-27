// Die Speiche selbst: Bauart, Dehnung unter Spannung, Gewicht und Ton.
//
// Wortgetreue Übertragung von speichenrechner/speiche.py. Die Namen sind
// absichtlich dieselben, damit man beide Fassungen nebeneinander lesen kann.
//
// Die reine Geometrie sagt, wie lang die Speiche im **gespannten** Laufrad
// sein muss. Verkauft wird sie aber ungespannt, und unter Zug längt sie sich:
//
//     ΔL = F/E · Σ (lᵢ / Aᵢ)
//
// Eine konifizierte Speiche wird dafür in drei Abschnitte zerlegt – verdicktes
// Kopfteil, verdickter unterer Teil und dünnes Mittelteil. Im Mittelteil
// steckt der weitaus größte Anteil der Dehnung.
//
// E ist der Elastizitätsmodul. Für nichtrostenden Speichendraht (18/8) wird im
// Laufradbau mit rund 180 000 N/mm² gerechnet, spürbar weniger als bei
// gewöhnlichem Baustahl.
//
// Der Speichenton folgt der Saitenformel:
//
//     f = 1/(2·L) · √(F / µ)      mit  µ = ρ · A
//
// Er gilt für eine frei schwingende Saite. Am eingespeichten Rad schwingt nur
// der Abschnitt zwischen der letzten Kreuzung und dem Nippel – der klingt
// höher. Der Wert taugt zum Vergleich der Speichen untereinander, ein
// Tensiometer bleibt genauer.

/** Elastizitätsmodul nichtrostender Speichen in N/mm². */
export const E_MODUL = 180000.0;

/** Dichte Stahl in kg/m³ bzw. g/mm³. */
export const DICHTE = 7850.0;
export const DICHTE_G_MM3 = 7.85e-3;

/** Übliche Speichenspannung in N (Richtwert für die stärker gespannte Seite). */
export const SPANNUNG_STANDARD = 1000.0;

/** Übliche Weitung von Nabenflansch und Speichenbogen unter Last, in mm. */
export const WEITUNG_STANDARD = 0.1;

/** Name der frei einstellbaren Bauart. */
export const EIGENE_BAUART = "eigene Maße …";

/** Deutsche Notennamen – H statt B. */
const NOTEN = ["c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "h"];

const flaecheAusDurchmesser = (durchmesser) => Math.PI / 4.0 * durchmesser ** 2;

/**
 * Eine Speichenbauart, zerlegt in ihre drei Abschnitte.
 *
 * `laenge_kopf`/`laenge_unten` sind die verdickten Enden, der Rest der Speiche
 * hat den Mittelquerschnitt. `flaeche_mitte_direkt` überschreibt die Berechnung
 * aus dem Durchmesser – nötig bei flachen Messerspeichen.
 */
export function bauart(name, durchmesserKopf, durchmesserUnten, durchmesserMitte,
                       laengeKopf = 15.0, laengeUnten = 20.0, flaecheMitteDirekt = null) {
  return {
    name,
    durchmesser_kopf: durchmesserKopf,
    durchmesser_unten: durchmesserUnten,
    durchmesser_mitte: durchmesserMitte,
    laenge_kopf: laengeKopf,
    laenge_unten: laengeUnten,
    flaeche_mitte_direkt: flaecheMitteDirekt,
    flaeche_kopf: flaecheAusDurchmesser(durchmesserKopf),
    flaeche_unten: flaecheAusDurchmesser(durchmesserUnten),
    flaeche_mitte: flaecheMitteDirekt !== null
      ? flaecheMitteDirekt
      : flaecheAusDurchmesser(durchmesserMitte),
  };
}

/** Gängige Bauarten. Die Abschnittslängen sind Näherungen – Hersteller weichen ab. */
export const BAUARTEN = [
  bauart("2,0 mm durchgehend (14 G)", 2.0, 2.0, 2.0, 0.0, 0.0),
  bauart("2,0/1,8/2,0 doppelt konifiziert", 2.0, 2.0, 1.8),
  bauart("2,0/1,7/2,0 doppelt konifiziert", 2.0, 2.0, 1.7),
  bauart("2,0/1,7/1,8 dreifach konifiziert", 2.0, 1.8, 1.7),
  bauart("2,0/1,5/2,0 sehr leicht", 2.0, 2.0, 1.5),
  bauart("1,8/1,6/1,8 dünn", 1.8, 1.8, 1.6),
  bauart("Messerspeiche flach, ≈ 2,3 × 1,2 mm", 2.0, 2.0, 0.0, 15.0, 20.0, 2.2),
];

/** Startwerte der frei einstellbaren Bauart (entspricht 2,0/1,7/1,8). */
export const EIGENE_VORGABE = {
  durchmesser_kopf: 2.0,
  durchmesser_unten: 1.8,
  durchmesser_mitte: 1.7,
  laenge_kopf: 15.0,
  laenge_unten: 20.0,
};

/** Sucht eine Bauart; `eigene` liefert die frei eingestellten Maße. */
export function bauartNachName(name, eigene = null) {
  if (name === EIGENE_BAUART) {
    const w = { ...EIGENE_VORGABE, ...(eigene || {}) };
    return bauart(EIGENE_BAUART, w.durchmesser_kopf, w.durchmesser_unten,
                  w.durchmesser_mitte, w.laenge_kopf, w.laenge_unten);
  }
  for (const b of BAUARTEN) {
    if (b.name === name) return b;
  }
  return BAUARTEN[0];
}

/** Zerlegt die Speiche in `[Länge, Querschnitt]`-Abschnitte. */
export function abschnitte(b, laenge) {
  const enden = b.laenge_kopf + b.laenge_unten;
  let kopf;
  let unten;
  if (enden >= Math.max(laenge - 10.0, 0.0)) {
    // Sehr kurze Speiche: Enden anteilig kürzen, damit nichts negativ wird.
    const anteil = enden > 0 ? Math.max(laenge - 10.0, 0.0) / enden : 0.0;
    kopf = b.laenge_kopf * anteil;
    unten = b.laenge_unten * anteil;
  } else {
    kopf = b.laenge_kopf;
    unten = b.laenge_unten;
  }

  const mitte = Math.max(laenge - kopf - unten, 0.0);
  return [
    [kopf, b.flaeche_kopf],
    [unten, b.flaeche_unten],
    [mitte, b.flaeche_mitte],
  ];
}

/** Elastische Längung in mm bei `spannung` in Newton. */
export function dehnung(b, laenge, spannung, eModul = E_MODUL) {
  if (laenge <= 0 || spannung <= 0 || eModul <= 0) return 0.0;
  let nachgiebigkeit = 0.0;
  for (const [teillaenge, flaeche] of abschnitte(b, laenge)) {
    if (flaeche > 0) nachgiebigkeit += teillaenge / flaeche;
  }
  return spannung / eModul * nachgiebigkeit;
}

/**
 * Zugspannung im dünnsten Querschnitt in N/mm².
 *
 * Gängiger Speichendraht hält deutlich über 1000 N/mm² aus; der Wert dient dem
 * Vergleich, die Grenze steht im Datenblatt der Speiche.
 */
export function drahtspannung(b, spannung) {
  if (b.flaeche_mitte <= 0) return 0.0;
  return spannung / b.flaeche_mitte;
}

/**
 * Ungefähres Gewicht einer Speiche in Gramm.
 *
 * Gerechnet wird das reine Drahtvolumen – Kopf, Bogen und Gewinde sind nicht
 * enthalten, der wahre Wert liegt einige Zehntel Gramm darüber.
 *
 * Heißt in speiche.py schlicht `masse`. Hier braucht sie einen eigenen Namen:
 * katalog.js hat bereits eine Funktion `masse` (die Einbaubreiten aus einer
 * Textangabe liest), und die Einzeldatei wirft alle Module in einen Scope –
 * dort überschriebe die spätere die frühere. tests/test_einzeldatei.py wacht
 * darüber, dass sich so etwas nicht wieder einschleicht.
 */
export function speichenmasse(b, laenge) {
  if (laenge <= 0) return 0.0;
  let volumen = 0.0;
  for (const [teillaenge, flaeche] of abschnitte(b, laenge)) {
    volumen += teillaenge * flaeche;
  }
  return volumen * DICHTE_G_MM3;
}

/**
 * Grundfrequenz der frei schwingenden Speiche in Hz.
 *
 * Maßgeblich ist der dünnste Querschnitt, denn dort liegt der größte Teil der
 * schwingenden Länge.
 */
export function frequenz(b, freieLaenge, spannung) {
  if (freieLaenge <= 0 || spannung <= 0) return 0.0;
  const flaecheM2 = b.flaeche_mitte * 1e-6;
  if (flaecheM2 <= 0) return 0.0;
  const masseJeMeter = DICHTE * flaecheM2;
  const laengeM = freieLaenge / 1000.0;
  return 1.0 / (2.0 * laengeM) * Math.sqrt(spannung / masseJeMeter);
}

/** Nächstgelegener Notenname, z. B. `"g¹"` – leer bei ungültiger Frequenz. */
export function note(hertz) {
  if (hertz <= 0) return "";
  const halbtoene = Math.round(12.0 * Math.log2(hertz / 440.0)) + 69;  // MIDI-Nummer
  // In Python ist % bei negativen Zahlen positiv, in JS nicht – nachhelfen,
  // sonst greift der Index bei sehr tiefen Tönen ins Leere.
  const name = NOTEN[((halbtoene % 12) + 12) % 12];
  const oktave = Math.floor(halbtoene / 12) - 1;

  // Deutsche Schreibweise: große Oktave in Versalien, ab c¹ mit Strichen.
  if (oktave <= 3) {
    const striche = "͵".repeat(Math.max(3 - oktave, 0));
    return name.toUpperCase() + striche;
  }
  return name + "¹²³⁴⁵⁶"[Math.min(oktave - 4, 5)];
}
