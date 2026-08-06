// Skizzen der Handy-Fassung: Nabe von der Seite, Felgenprofil im Schnitt.
//
// Übertragung von pc/speichenrechner/ui/bauteile.py. Dort wird mit Cairo
// gezeichnet, hier mit SVG – die Formen selbst sind in beiden Fassungen
// dieselben Zahlen:
//
//   * Die Nabe ist eine **Drehteil-Kontur**: eine Liste von (x, Radius) ab der
//     Nabenmitte, oben hin und unten zurück. Deshalb wirken die Flansche
//     angeformt und nicht angeklebt.
//   * Die Felge ist Blech: die Kontur wird als Strich in Wandstärke gezeichnet,
//     nicht als gefüllte Fläche.
//
// Farben kommen aus dem Stylesheet (currentColor und die CSS-Variablen), damit
// die Skizze der Hell/Dunkel-Einstellung des Geräts folgt.

// --------------------------------------------------------------- Nabenform

/** Radien der Nabe in mm, für die es keine Eingabe gibt. */
export const GESTALT = {
  achse: 5.0, kappe: 8.5, sitz: 12.0, bund: 13.5, rohr: 11.0, taille: 9.5,
  freilauf: 17.0, flanschdicke: 1.4, flanschrand: 2.5,
  stummel: 30.0, kappeAb: 22.0, sitzAb: 15.0, bundAb: 7.0, uebergang: 5.0,
  freilaufAb: 3.0, freilaufBis: 30.0, kappeRechts: 36.0, stummelRechts: 44.0,
};

export const GEWINDE_LAENGE = 16.0;
export const GEWINDE_RADIUS = 13.0;
const TAILLE_SCHRITTE = 14;

/** `[Bund, Rohr, Taille]` in mm – bei „gross“ füllt die Schale fast den Flansch. */
function schale(art, radiusLinks, radiusRechts) {
  const kleinster = Math.max(Math.min(radiusLinks, radiusRechts), 1.0);
  if (art === "gross") return [kleinster * 0.86, kleinster * 0.82, kleinster * 0.76];
  const deckel = kleinster * 0.80;
  return [
    Math.min(GESTALT.bund, deckel),
    Math.min(GESTALT.rohr, deckel * 0.88),
    Math.min(GESTALT.taille, deckel * 0.76),
  ];
}

/** Was rechts an der Nabe sitzt: „kassette“, „gewinde“ oder „keiner“. */
export function antrieb(art, aufnahme) {
  if (art === "Vorderrad" || art === "Dynamo") return "keiner";
  if (art === "Nabenschaltung") return "gewinde";
  if (["Schraubkranz", "Schraubritzel", "Singlespeed"].includes(aufnahme)) return "gewinde";
  return "kassette";
}

/** „gross“ bei Dynamo und Nabenschaltung, sonst „normal“. */
export const schalenart = (art) => (["Dynamo", "Nabenschaltung"].includes(art)
  ? "gross" : "normal");

/** Die Nabe als `[x, Radius]` in mm, ab der Nabenmitte. */
export function stationen(aLinks, aRechts, rLinks, rRechts,
                          antriebsart = "kassette", schalenArt = "normal") {
  const g = GESTALT;
  const rFl = rLinks + g.flanschrand;
  const rFr = rRechts + g.flanschrand;
  const dicke = g.flanschdicke;
  const [bund, rohr, taille] = schale(schalenArt, rLinks, rRechts);
  const sitz = Math.min(g.sitz, bund * 0.92);
  const kappe = Math.min(g.kappe, sitz * 0.75);
  const achse = Math.min(g.achse, kappe * 0.62);

  const liste = [
    [-aLinks - g.stummel, achse], [-aLinks - g.kappeAb, achse],
    [-aLinks - g.kappeAb, kappe], [-aLinks - g.sitzAb, kappe],
    [-aLinks - g.sitzAb, sitz], [-aLinks - g.bundAb, sitz],
    [-aLinks - g.bundAb, bund], [-aLinks - dicke, bund],
    [-aLinks - dicke, rFl], [-aLinks + dicke, rFl],
    [-aLinks + dicke, bund], [-aLinks + g.uebergang, rohr],
  ];

  // Taille als Kosinus abgetastet – ein weicher Bogen statt einer Kante.
  const von = -aLinks + g.uebergang;
  const bis = aRechts - g.uebergang;
  if (bis > von) {
    for (let n = 0; n <= TAILLE_SCHRITTE; n += 1) {
      const anteil = n / TAILLE_SCHRITTE;
      const hub = (Math.cos(anteil * 2 * Math.PI - Math.PI) + 1) / 2;
      liste.push([von + anteil * (bis - von), taille + (rohr - taille) * hub]);
    }
  }

  liste.push(
    [aRechts - g.uebergang, rohr], [aRechts - dicke, bund],
    [aRechts - dicke, rFr], [aRechts + dicke, rFr],
    [aRechts + dicke, bund], [aRechts + g.freilaufAb, bund],
  );

  if (antriebsart === "kassette") {
    liste.push(
      [aRechts + g.freilaufAb, g.freilauf], [aRechts + g.freilaufBis, g.freilauf],
      [aRechts + g.freilaufBis, kappe], [aRechts + g.kappeRechts, kappe],
      [aRechts + g.kappeRechts, achse], [aRechts + g.stummelRechts, achse],
    );
  } else if (antriebsart === "gewinde") {
    const ende = aRechts + g.freilaufAb + GEWINDE_LAENGE;
    liste.push(
      [aRechts + g.freilaufAb, GEWINDE_RADIUS], [ende, GEWINDE_RADIUS],
      [ende, kappe], [ende + 7, kappe],
      [ende + 7, achse], [ende + 15, achse],
    );
  } else {
    liste.push(
      [aRechts + g.bundAb, sitz], [aRechts + g.sitzAb, sitz],
      [aRechts + g.sitzAb, kappe], [aRechts + g.kappeAb, kappe],
      [aRechts + g.kappeAb, achse], [aRechts + g.stummel, achse],
    );
  }
  return liste;
}

// ------------------------------------------------------------ Felgenprofile

/** Umrisse der Profile in mm ab dem Nippelsitz: `[Tiefe, quer]`. */
export const PROFILE = {
  hohlkammer: {
    aussen: [[0, -7], [3, -10], [14, -11.5], [14, -13.5], [22, -13.5], [22, -9.5], [19, -8],
             [19, 8], [22, 9.5], [22, 13.5], [14, 13.5], [14, 11.5], [3, 10], [0, 7]],
    kammer: [[3.5, -8.5], [12, -9.5], [12, 9.5], [3.5, 8.5]],
  },
  haken: {
    aussen: [[0, -7], [3, -10], [14, -11.5], [14, -13.5], [22, -13.5], [22, -9], [18.5, -7.5],
             [18.5, 7.5], [22, 9], [22, 13.5], [14, 13.5], [14, 11.5], [3, 10], [0, 7]],
    kammer: [[3.5, -8.5], [12, -9.5], [12, 9.5], [3.5, 8.5]],
  },
  tubeless: {
    aussen: [[0, -7], [3, -10], [14, -11.5], [14, -13.5], [22, -13.5], [22, -9.5], [19, -8],
             [20, -5.5], [17.5, -2.5], [17.5, 2.5], [20, 5.5], [19, 8], [22, 9.5], [22, 13.5],
             [14, 13.5], [14, 11.5], [3, 10], [0, 7]],
    kammer: [[3.5, -8.5], [12, -9.5], [12, 9.5], [3.5, 8.5]],
  },
  hakenlos: {
    aussen: [[0, -7], [3, -10], [14, -11.5], [19, -12], [22, -11.5], [22, -8], [19, -8],
             [19, 8], [22, 8], [22, 11.5], [19, 12], [14, 11.5], [3, 10], [0, 7]],
    kammer: [[3.5, -8.5], [12, -9.5], [12, 9.5], [3.5, 8.5]],
  },
  "v-profil": {
    aussen: [[0, -6.5], [18, -12], [18, -13.5], [24, -13.5], [24, -9.5], [21, -8],
             [21, 8], [24, 9.5], [24, 13.5], [18, 13.5], [18, 12], [0, 6.5]],
    kammer: [[3, -7.5], [16.5, -10.5], [16.5, 10.5], [3, 7.5]],
  },
  aero: {
    aussen: [[0, -5], [30, -11.5], [30, -13.5], [38, -13.5], [38, -9.5], [35, -8],
             [35, 8], [38, 9.5], [38, 13.5], [30, 13.5], [30, 11.5], [0, 5]],
    kammer: [[3, -6], [28, -10.5], [28, 10.5], [3, 6]],
  },
  flachbett: {
    aussen: [[14, -13], [12, -12], [2, -10], [0, -6], [0, 6], [2, 10], [12, 12], [14, 13]],
    offen: true,
  },
  schlauch: {
    aussen: [[0, -9], [2, -11], [10, -12], [13, -11.5], [10, -7], [9, 0], [10, 7],
             [13, 11.5], [10, 12], [2, 11], [0, 9]],
  },
};

const PROFIL_STANDARD = "hohlkammer";

/** Bauform → Profil. Der erste Treffer im Namen gewinnt. */
const PROFILWOERTER = [
  ["flachbett", "flachbett"], ["hohlkammer", "hohlkammer"], ["box-section", "hohlkammer"],
  ["v-profil", "v-profil"], ["aero", "aero"], ["hakenlos", "hakenlos"], ["hookless", "hakenlos"],
  ["haken", "haken"], ["tubeless", "tubeless"], ["schlauchreifen", "schlauch"],
  ["tubular", "schlauch"],
];

export function profilName(felgentypName) {
  const text = (felgentypName || "").toLowerCase();
  for (const [wort, profil] of PROFILWOERTER) {
    if (text.includes(wort)) return profil;
  }
  return PROFIL_STANDARD;
}

// -------------------------------------------------------------------- SVG

const rund = (wert) => Math.round(wert * 100) / 100;
const pfad = (punkte, zu = true) =>
  `M ${punkte.map(([x, y]) => `${rund(x)} ${rund(y)}`).join(" L ")}${zu ? " Z" : ""}`;

/**
 * Nabe von der Seite als SVG.
 *
 * `nabe` trägt die Felder des Formulars; `art` und `aufnahme` bestimmen, ob
 * rechts ein Freilaufkörper, ein Gewindestummel oder nichts sitzt.
 */
export function nabeSvg(nabe, breite = 340, hoehe = 190) {
  const rLinks = nabe.flanschdurchmesser_links / 2;
  const rRechts = nabe.flanschdurchmesser_rechts / 2;
  const antriebsart = antrieb(nabe.art, nabe.aufnahme);
  const schalenArt = schalenart(nabe.art);
  const liste = stationen(nabe.flanschabstand_links, nabe.flanschabstand_rechts,
                          rLinks, rRechts, antriebsart, schalenArt);

  const spanneX = liste[liste.length - 1][0] - liste[0][0];
  const spanneR = Math.max(...liste.map(([, r]) => r));
  const skala = Math.min(breite / (spanneX * 1.08), (hoehe / 2) / (spanneR * 1.25));

  const mitteY = hoehe / 2;
  const mitteX = breite / 2 - ((liste[0][0] + liste[liste.length - 1][0]) / 2) * skala;
  const X = (x) => mitteX + x * skala;
  const Y = (r) => mitteY - r * skala;

  const oben = liste.map(([x, r]) => [X(x), Y(r)]);
  const unten = [...liste].reverse().map(([x, r]) => [X(x), mitteY + r * skala]);

  const xFl = X(-nabe.flanschabstand_links);
  const xFr = X(nabe.flanschabstand_rechts);
  const achse = Math.min(GESTALT.achse, spanneR * 0.2) * skala;

  // Antriebsseite: Nuten des Freilaufkörpers oder Gewindestriche
  let antriebsdetail = "";
  if (antriebsart === "kassette") {
    const x1 = xFr + GESTALT.freilaufAb * skala;
    const x2 = xFr + GESTALT.freilaufBis * skala;
    const halb = GESTALT.freilauf * skala * 0.96;
    for (let n = 1; n < 7; n += 1) {
      const x = x1 + ((x2 - x1) * n) / 7;
      antriebsdetail += `<line x1="${rund(x)}" y1="${rund(mitteY - halb)}" `
        + `x2="${rund(x)}" y2="${rund(mitteY + halb)}"/>`;
    }
  } else if (antriebsart === "gewinde") {
    const x1 = xFr + GESTALT.freilaufAb * skala;
    const x2 = x1 + GEWINDE_LAENGE * skala;
    const halb = GEWINDE_RADIUS * skala;
    const teilung = Math.max(3, 1.4 * skala);
    for (let x = x1 + teilung * 0.4; x < x2 - teilung * 0.7; x += teilung) {
      for (const richtung of [-1, 1]) {
        const y = mitteY + richtung * halb;
        antriebsdetail += `<line x1="${rund(x)}" y1="${rund(y)}" `
          + `x2="${rund(x + teilung * 0.7)}" y2="${rund(y - richtung * halb * 0.3)}"/>`;
      }
    }
  }

  // Rändelung am Lagersitz links
  const [bund] = schale(schalenArt, rLinks, rRechts);
  const sitzHalb = Math.min(GESTALT.sitz, bund * 0.92) * skala * 0.94;
  let riffel = "";
  const rx1 = xFl - GESTALT.sitzAb * skala;
  const rx2 = xFl - GESTALT.bundAb * skala;
  for (let x = rx1 + 1.5; x < rx2; x += Math.max(2, 0.9 * skala)) {
    riffel += `<line x1="${rund(x)}" y1="${rund(mitteY - sitzHalb)}" `
      + `x2="${rund(x)}" y2="${rund(mitteY + sitzHalb)}"/>`;
  }

  const loch = Math.max(1.9, 0.95 * skala);
  const loecher = [[xFl, rLinks], [xFr, rRechts]].flatMap(([x, r]) => [-1, 1].map(
    (richtung) => `<circle cx="${rund(x)}" cy="${rund(mitteY + richtung * r * skala)}" `
      + `r="${rund(loch)}" class="bohrung"/>`));

  return `<svg viewBox="0 0 ${breite} ${hoehe}" class="skizze" role="img"
   aria-label="Nabe von der Seite mit Flanschabstand und Flansch-Durchmesser">
  <rect x="${rund(X(liste[0][0]))}" y="${rund(mitteY - achse)}"
        width="${rund(X(liste[liste.length - 1][0]) - X(liste[0][0]))}"
        height="${rund(2 * achse)}" class="achse"/>
  <path d="${pfad([...oben, ...unten])}" class="bauteil"/>
  <g class="detail">${antriebsdetail}${riffel}</g>
  ${loecher.join("")}
  <line x1="${rund(mitteX)}" y1="6" x2="${rund(mitteX)}" y2="${hoehe - 6}" class="mittellinie"/>
  <g class="mass">
    <line x1="${rund(xFl)}" y1="12" x2="${rund(mitteX)}" y2="12"/>
    <line x1="${rund(mitteX)}" y1="24" x2="${rund(xFr)}" y2="24"/>
    <text x="${rund((xFl + mitteX) / 2)}" y="9">a ${rund(nabe.flanschabstand_links)}</text>
    <text x="${rund((mitteX + xFr) / 2)}" y="36">a ${rund(nabe.flanschabstand_rechts)}</text>
    <text x="${rund(xFl)}" y="${rund(Y(rLinks) - 5)}">d ${rund(nabe.flanschdurchmesser_links)}</text>
  </g>
</svg>`;
}

/** Zwei Felgenprofile im Schnitt mit dem ERD dazwischen. */
export function felgeSvg(felgentypName, oesen, erd, breite = 340, hoehe = 170) {
  const name = profilName(felgentypName);
  const profil = PROFILE[name] || PROFILE[PROFIL_STANDARD];
  const bezug = PROFILE[PROFIL_STANDARD];

  const tiefe = Math.max(...profil.aussen.map(([t]) => t));
  const halb = Math.max(...profil.aussen.map(([, q]) => Math.abs(q)));
  const bezugTiefe = Math.max(...bezug.aussen.map(([t]) => t));
  const bezugHalb = Math.max(...bezug.aussen.map(([, q]) => Math.abs(q)));
  // Maßstab am Hohlkammerprofil: die Bauformen bleiben untereinander
  // vergleichbar, nur ein größeres wird kleiner gezeichnet.
  const skala = Math.min(breite * 0.23 / Math.max(tiefe, bezugTiefe),
                         hoehe * 0.30 / Math.max(halb, bezugHalb));

  const mitteY = hoehe * 0.44;
  const abstand = breite * 0.19;
  const wand = Math.max(1.7 * skala, 2.6);

  const haelfte = (xNippel, nachAussen) => {
    const P = ([t, q]) => [xNippel + nachAussen * t * skala, mitteY + q * skala];
    let teile = `<path d="${pfad(profil.aussen.map(P), !profil.offen)}" `
      + `class="blech" stroke-width="${rund(wand)}"/>`;
    if (profil.kammer) {
      teile += `<path d="${pfad(profil.kammer.map(P))}" class="blech" `
        + `stroke-width="${rund(wand * 0.72)}"/>`;
    }
    if (oesen) {
      const [x1, y1] = P([-0.5, -3.4]);
      const [x2, y2] = P([1.4, 3.4]);
      teile += `<rect x="${rund(Math.min(x1, x2))}" y="${rund(Math.min(y1, y2))}" `
        + `width="${rund(Math.abs(x2 - x1))}" height="${rund(Math.abs(y2 - y1))}" class="oese"/>`;
    }
    teile += `<circle cx="${rund(xNippel)}" cy="${rund(mitteY)}" `
      + `r="${rund(Math.max(2.4, 0.9 * skala))}" class="bohrung"/>`;
    return teile;
  };

  const xLinks = breite / 2 - abstand;
  const xRechts = breite / 2 + abstand;
  const yMass = mitteY + (halb + 1) * skala + 18;

  return `<svg viewBox="0 0 ${breite} ${hoehe}" class="skizze" role="img"
   aria-label="Felgenprofil im Schnitt mit dem ERD">
  ${haelfte(xLinks, -1)}
  ${haelfte(xRechts, +1)}
  <g class="mass">
    <line x1="${rund(xLinks)}" y1="${rund(yMass)}" x2="${rund(xRechts)}" y2="${rund(yMass)}"/>
    <text x="${rund(breite / 2)}" y="${rund(yMass + 14)}">ERD ${rund(erd)}</text>
  </g>
  <text x="${rund(breite / 2)}" y="12" class="titel">${felgentypName || "Hohlkammerfelge"}</text>
</svg>`;
}
