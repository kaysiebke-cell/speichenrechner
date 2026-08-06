// Mathematik des Speichenrechners – Handy-Fassung.
//
// Wortgetreue Übertragung von speichenrechner/berechnung.py. Die Namen sind
// absichtlich dieselben, damit man beide Fassungen nebeneinander lesen kann.
//
// Modell: Nabenmitte im Ursprung, Radebene = xy-Ebene, Achse entlang z.
//
//   Flanschloch:  (r, 0, w)                 r = Flanschradius, w = Flanschabstand
//   Felgenloch:   (R·cos a, R·sin a, 0)     R = ERD/2
//   L = sqrt(R² + r² + w² − 2·R·r·cos a) − d/2
//
// Dass diese Fassung dasselbe rechnet wie die Python-Fassung, prüft
// werkzeuge/pruefwerte_js.mjs gegen data/pruefwerte.json.

export const RUNDUNGSSCHRITTE = [1.0, 0.5, 2.0];

/** Sehnenwinkel in Grad aus der Speichenzahl **einer** Flanschseite. */
export function sehnenwinkelSeite(speichenSeite, kreuzungen) {
  if (speichenSeite <= 0) {
    throw new Error("Auf jeder Seite muss mindestens eine Speiche sitzen.");
  }
  return (kreuzungen * 360.0) / speichenSeite;
}

/** Speichenzahl der linken Seite – bei 2:1 trägt rechts doppelt so viele. */
export function speichenLinks(speichenzahl, verteilung) {
  return verteilung === "2:1"
    ? Math.floor(speichenzahl / 3)
    : Math.floor(speichenzahl / 2);
}

export function speichenRechts(speichenzahl, verteilung) {
  return speichenzahl - speichenLinks(speichenzahl, verteilung);
}

/** Exakte Speichenlänge in mm (ungerundet). */
export function speichenlaenge(erd, flanschdurchmesser, flanschabstand, speichenSeite,
                               kreuzungen, speichenloch = 2.6) {
  if (erd <= 0) throw new Error("Der ERD muss größer als 0 sein.");
  if (flanschdurchmesser <= 0) throw new Error("Der Flanschdurchmesser muss größer als 0 sein.");
  if (kreuzungen < 0) throw new Error("Die Kreuzungszahl darf nicht negativ sein.");

  const R = erd / 2.0;
  const r = flanschdurchmesser / 2.0;
  const w = Math.abs(flanschabstand);
  const a = (sehnenwinkelSeite(speichenSeite, kreuzungen) * Math.PI) / 180.0;

  const quadrat = R * R + r * r + w * w - 2.0 * R * r * Math.cos(a);
  return Math.sqrt(Math.max(quadrat, 0.0)) - speichenloch / 2.0;
}

/** Speichenwinkel gegen die Radebene, in Grad. Je größer, desto seitensteifer. */
export function speichenwinkel(erd, flanschdurchmesser, flanschabstand, speichenSeite,
                               kreuzungen) {
  const R = erd / 2.0;
  const r = flanschdurchmesser / 2.0;
  const w = Math.abs(flanschabstand);
  const a = (sehnenwinkelSeite(speichenSeite, kreuzungen) * Math.PI) / 180.0;

  const geometrisch = Math.sqrt(
    Math.max(R * R + r * r + w * w - 2.0 * R * r * Math.cos(a), 0.0),
  );
  if (geometrisch <= 0.0) return 0.0;
  return (Math.asin(Math.min(w / geometrisch, 1.0)) * 180.0) / Math.PI;
}

/** Winkel an der Felge zwischen Speiche und Felgenradius, in Grad. */
export function felgenwinkel(erd, flanschdurchmesser, kreuzungen, speichenSeite) {
  const R = erd / 2.0;
  const r = flanschdurchmesser / 2.0;
  const a = (sehnenwinkelSeite(speichenSeite, kreuzungen) * Math.PI) / 180.0;
  const projektion = Math.sqrt(Math.max(R * R + r * r - 2.0 * R * r * Math.cos(a), 0.0));
  if (projektion <= 0) return 0.0;
  return (Math.asin(Math.min((r * Math.sin(a)) / projektion, 1.0)) * 180.0) / Math.PI;
}

/** Bogenabstand benachbarter Speichenlöcher eines Flansches, in mm. */
export function lochabstand(flanschdurchmesser, speichenSeite) {
  if (speichenSeite <= 0) return 0.0;
  return (Math.PI * flanschdurchmesser) / speichenSeite;
}

/** Rundet auf den nächsten verfügbaren Speichenlängen-Schritt. */
export function runden(laenge, schritt = 1.0) {
  if (schritt <= 0) return laenge;
  // Python rundet zur geraden Zahl, JavaScript von der Null weg. Bei genau
  // 0,5 Schritten fällt das auf, deshalb hier ausdrücklich wie Python.
  const anteil = laenge / schritt;
  const abgerundet = Math.floor(anteil);
  const rest = anteil - abgerundet;
  let ganz;
  if (rest > 0.5) ganz = abgerundet + 1;
  else if (rest < 0.5) ganz = abgerundet;
  else ganz = abgerundet % 2 === 0 ? abgerundet : abgerundet + 1;
  return ganz * schritt;
}

/**
 * Spannungsanteile beider Seiten in Prozent.
 *
 * Axiales Kräftegleichgewicht: m_l · T_l · sin(a_l) = m_r · T_r · sin(a_r).
 * Die stärker gespannte Seite wird auf 100 % gesetzt.
 */
export function spannungsanteile(links, rechts) {
  const hebelLinks = links.speichen * Math.sin((links.speichenwinkel * Math.PI) / 180.0);
  const hebelRechts = rechts.speichen * Math.sin((rechts.speichenwinkel * Math.PI) / 180.0);
  if (hebelLinks <= 0 || hebelRechts <= 0) return [100.0, 100.0];
  if (hebelLinks <= hebelRechts) return [100.0, (100.0 * hebelLinks) / hebelRechts];
  return [(100.0 * hebelRechts) / hebelLinks, 100.0];
}

/** Übliche Kreuzungszahl für eine Flanschseite mit ``m`` Speichen. */
export function ueblicheKreuzungen(speichenSeite) {
  if (speichenSeite >= 12) return 3;
  if (speichenSeite >= 9) return 2;
  return 1;
}

/**
 * Rechnet beide Seiten eines Laufrads.
 *
 * ``eingabe`` trägt dieselben Feldnamen wie data/pruefwerte.json.
 */
export function berechne(eingabe) {
  const {
    flanschdurchmesser_links: dLinks,
    flanschdurchmesser_rechts: dRechts,
    flanschabstand_links: aLinks,
    flanschabstand_rechts: aRechts,
    speichenloch = 2.6,
    erd,
    versatz = 0.0,
    speichenzahl,
    kreuzungen_links: kLinks,
    kreuzungen_rechts: kRechts,
    verteilung = "1:1",
    schritt = 1.0,
  } = eingabe;

  // Asymmetrische Felge: das Speichenbett wandert nach rechts, damit
  // vergrößert sich der wirksame Abstand links und verkleinert sich rechts.
  const wirksamLinks = aLinks + versatz;
  const wirksamRechts = aRechts - versatz;

  const anzahlLinks = speichenLinks(speichenzahl, verteilung);
  const anzahlRechts = speichenRechts(speichenzahl, verteilung);

  const seite = (durchmesser, abstand, kreuzungen, anzahl) => {
    const laenge = speichenlaenge(erd, durchmesser, abstand, anzahl, kreuzungen, speichenloch);
    return {
      laenge,
      laenge_gerundet: runden(laenge, schritt),
      speichenwinkel: speichenwinkel(erd, durchmesser, abstand, anzahl, kreuzungen),
      felgenwinkel: felgenwinkel(erd, durchmesser, kreuzungen, anzahl),
      sehnenwinkel: sehnenwinkelSeite(anzahl, kreuzungen),
      lochabstand: lochabstand(durchmesser, anzahl),
      kreuzungen,
      speichen: anzahl,
    };
  };

  const links = seite(dLinks, wirksamLinks, kLinks, anzahlLinks);
  const rechts = seite(dRechts, wirksamRechts, kRechts, anzahlRechts);
  const [spannungLinks, spannungRechts] = spannungsanteile(links, rechts);

  return {
    links,
    rechts,
    spannung_links_prozent: spannungLinks,
    spannung_rechts_prozent: spannungRechts,
    gleicheBestelllaenge: links.laenge_gerundet === rechts.laenge_gerundet,
  };
}

/** Was zu bestellen ist – gleiche Bestelllängen werden zusammengefasst. */
export function einkaufsliste(ergebnis) {
  const { links, rechts } = ergebnis;
  if (ergebnis.gleicheBestelllaenge) {
    return [`${links.speichen + rechts.speichen} × ${zahl(links.laenge_gerundet)} mm`];
  }
  return [
    `${links.speichen} × ${zahl(links.laenge_gerundet)} mm (links)`,
    `${rechts.speichen} × ${zahl(rechts.laenge_gerundet)} mm (rechts)`,
  ];
}

/** Deutsche Schreibweise: Komma statt Punkt. */
export function zahl(wert, stellen = 1) {
  return wert.toFixed(stellen).replace(".", ",");
}

export function mm(wert, stellen = 1) {
  return `${zahl(wert, stellen)} mm`;
}

export function grad(wert, stellen = 1) {
  return `${zahl(wert, stellen)}°`;
}
