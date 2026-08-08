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
  freilaufAb: 3.0, freilaufBis: 30.0,
  kappeRechts: 36.0, stummelRechts: 44.0,
};

export const GEWINDE_LAENGE = 16.0;
export const GEWINDE_RADIUS = 13.0;
const TAILLE_SCHRITTE = 14;

/** `[Bund, Rohr, Taille]` in mm – bei „gross“ füllt die Schale fast den Flansch. */
function schale(art, radiusLinks, radiusRechts) {
  const kleinster = Math.max(Math.min(radiusLinks, radiusRechts), 1.0);
  // Eine Trommel, keine Taille: bei Dynamo und Getriebenabe füllt das
  // Innenleben die Schale bis kurz unter den Flansch aus – so zeigt es die
  // Werkszeichnung der SON 28.
  if (art === "gross") return [kleinster * 0.88, kleinster * 0.86, kleinster * 0.84];
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

/**
 * Die Form eines Nabendynamos, abgelesen an der Werkszeichnung der SON 28 –
 * als Verhältnis zum Lochkreisradius, damit sie auch für einen SONdelux passt.
 *
 * Der Körper ist **eine Kugel** zwischen den Flanschen: Scheitel in der Mitte,
 * zu beiden Seiten in eine Hohlkehle auslaufend. Daraus steigt je eine schmale
 * Rippe mit rundem Kopf zum Speichenloch – ihre Spitze ist der höchste Punkt.
 * Nach außen folgt ein flaches, breites Achsband mit zwei Stufen.
 */
export const DYNAMO = {
  scheitel: 1.045, kehle: 0.72, rippe: 1.081, fuss: 0.76,
  kugelEnde: 0.77, rippeHalb: 1.7, absatz: 0.49, band: 0.43, achse: 0.17,
};

/** Wie weit der Kugelabschnitt reicht, in Grad ab dem Scheitel. */
export const KUGEL_WINKEL = 78;

/** Die Kontur eines Nabendynamos – Kugel, Hohlkehle, Rippe, Achsband.
 *
 * Die Kugel ist ein Drehteil: um ihre eigene Mitte rund, nicht um die
 * Felgenmittelebene. Sonst wäre bei 37/19 mm die linke Hälfte doppelt so
 * lang wie die rechte – gleicher Scheitel, halbe Länge, kein Ball.
 */
export function dynamoStationen(aLinks, aRechts, rLinks, rRechts, schritte = 40) {
  const d = DYNAMO;
  const bezug = Math.max(Math.min(rLinks, rRechts), 1);
  const scheitel = bezug * d.scheitel;
  const kehle = bezug * d.kehle;
  const fuss = bezug * d.fuss;
  const breit = d.rippeHalb;

  // Mitte und halbe Länge des Körpers, gemessen zwischen den Flanschen.
  const kugelMitte = (aRechts - aLinks) / 2;
  const kugelHalb = ((aLinks + aRechts) / 2) * d.kugelEnde;

  // Ein echter Kugelabschnitt: über den Winkel abgetastet, nicht über x –
  // sonst wird der Scheitel eckig.
  const kugel = () => {
    const endwinkel = (KUGEL_WINKEL * Math.PI) / 180;
    const tiefe = 1 - Math.cos(endwinkel);
    const punkte = [];
    for (let n = -schritte; n <= schritte; n += 1) {
      const winkel = (endwinkel * n) / schritte;
      const x = kugelMitte + (kugelHalb * Math.sin(winkel)) / Math.sin(endwinkel);
      const hoehe = (Math.cos(winkel) - Math.cos(endwinkel)) / tiefe;
      punkte.push([x, kehle + (scheitel - kehle) * hoehe]);
    }
    return punkte;
  };

  const seite = (a, rLoch, vz) => {
    const rippe = rLoch + (d.rippe - 1) * bezug;
    const punkte = [];
    punkte.push([vz * (a - breit - 1.5), kehle + (fuss - kehle) * 0.35]);
    punkte.push([vz * (a - breit), fuss]);
    punkte.push([vz * (a - breit), rippe - 1], [vz * (a - breit * 0.4), rippe],
                [vz * (a + breit * 0.4), rippe], [vz * (a + breit), rippe - 1],
                [vz * (a + breit), fuss]);
    punkte.push([vz * (a + 5), bezug * d.absatz], [vz * (a + 10), bezug * d.absatz],
                [vz * (a + 10), bezug * d.band], [vz * (a + 22), bezug * d.band],
                [vz * (a + 22), bezug * d.achse], [vz * (a + 29), bezug * d.achse]);
    return punkte;
  };

  return [...seite(aLinks, rLinks, -1).reverse(), ...kugel(),
          ...seite(aRechts, rRechts, +1)];
}

/** Woran eine Rohloff im Namen zu erkennen ist – ihre Form gilt nur für sie. */
const ROHLOFF_KENNUNG = ["rohloff", "speedhub"];

/** Sonderform einer bestimmten Nabe, sonst leer. Bisher nur „rohloff“.
 *
 * Heißt nicht `bauform`: die Einzeldatei legt alle Module in einen Namensraum,
 * und dort gibt es in app.js schon eine Variable dieses Namens.
 */
export function nabenBauform(name = "") {
  const text = String(name).toLowerCase();
  return ROHLOFF_KENNUNG.some((k) => text.includes(k)) ? "rohloff" : "";
}

/** Viertelellipse zwischen zwei Punkten – siehe _viertelbogen in bauteile.py. */
function viertelbogen(x1, r1, x2, r2, schritte = 12, hohl = true) {
  const punkte = [];
  for (let n = 1; n <= schritte; n += 1) {
    const winkel = ((n / schritte) * Math.PI) / 2;
    if (hohl) {
      punkte.push([x1 + (x2 - x1) * Math.sin(winkel),
                   r1 + (r2 - r1) * (1 - Math.cos(winkel))]);
    } else {
      punkte.push([x1 + (x2 - x1) * (1 - Math.cos(winkel)),
                   r1 + (r2 - r1) * Math.sin(winkel)]);
    }
  }
  return punkte;
}

// Die Rohloff SPEEDHUB, abgegriffen an einer Umrisszeichnung – keine Formel,
// sondern Punkte. Pixel der Vorlage (Achsmitte y = 560, Flanschspitzen bei
// x = 447 und 1007, Flanschspitze r = 516), normiert auf Flanschabstand und
// Flanschaußenradius. Siehe ROHLOFF_KONTUR in bauteile.py.
const ROHLOFF_MITTE_X = 727;
const ROHLOFF_MITTE_Y = 560;
const ROHLOFF_HALB = 280;
const ROHLOFF_R = 516;

const ROHLOFF_PIXEL = [
  [40, 513], [95, 513], [95, 470], [122, 388], [180, 380], [208, 380],
  [208, 237], [228, 237], [228, 320], [240, 320],
  ...viertelbogen(240, 320, 432, 155, 12, true),
  [432, 45], [462, 45], [462, 152], [840, 152], [872, 140], [950, 138],
  [950, 42], [1065, 42],
  ...viertelbogen(1065, 42, 1195, 305, 12, false),
  [1210, 305], [1210, 392], [1310, 392], [1310, 505], [1385, 505],
];

export const ROHLOFF_KONTUR = ROHLOFF_PIXEL.map(([x, y]) => [
  (x - ROHLOFF_MITTE_X) / ROHLOFF_HALB,
  (ROHLOFF_MITTE_Y - y) / ROHLOFF_R,
]);

/** Die Umrisszeichnung, auf die eingegebenen Maße gestreckt. */
export function rohloffStationen(aLinks, aRechts, rLinks, rRechts) {
  const bezug = (rLinks + rRechts) / 2 + GESTALT.flanschrand;
  return ROHLOFF_KONTUR.map(([x, r]) => [x * (x < 0 ? aLinks : aRechts), r * bezug]);
}

/** Die Nabe als `[x, Radius]` in mm, ab der Nabenmitte. */
export function stationen(aLinks, aRechts, rLinks, rRechts,
                          antriebsart = "kassette", schalenArt = "normal", art = "",
                          form = "") {
  // Die SPEEDHUB ist nachgezeichnet, nicht gerechnet: siehe ROHLOFF_KONTUR.
  if (form === "rohloff") return rohloffStationen(aLinks, aRechts, rLinks, rRechts);
  // Ein Nabendynamo hat eine eigene Gestalt, siehe DYNAMO.
  if (art === "Dynamo") return dynamoStationen(aLinks, aRechts, rLinks, rRechts);
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
    [-aLinks - g.sitzAb, sitz],
  ];
  liste.push([-aLinks - g.bundAb, sitz], [-aLinks - g.bundAb, bund],
             [-aLinks - dicke, bund]);
  liste.push(
    [-aLinks - dicke, rFl], [-aLinks + dicke, rFl],
    [-aLinks + dicke, bund], [-aLinks + g.uebergang, rohr],
  );

  const von = -aLinks + g.uebergang;
  const bis = aRechts - g.uebergang;
  if (bis > von) {
    if (schalenArt === "gross") {
      // Getriebenabe: eine glatte Trommel. Das Getriebe füllt die Schale aus,
      // die Flansche sitzen als Ringe an ihren Enden – so sieht eine Rohloff
      // SPEEDHUB aus, und eine Shimano Nexus ebenso. Zwischen `von` und `bis`
      // liegt deshalb nichts: die Kontur läuft als Gerade durch.
      //
      // Hier standen einmal zwei tiefe Hohlkehlen mit einem Band dazwischen –
      // aus einer falsch gelesenen Zeichnung der SON 28. Der Nabendynamo hat
      // inzwischen seine eigene Kontur, siehe DYNAMO.
    } else {
      for (let n = 0; n <= TAILLE_SCHRITTE; n += 1) {
        const anteil = n / TAILLE_SCHRITTE;
        const hub = (Math.cos(anteil * 2 * Math.PI - Math.PI) + 1) / 2;
        liste.push([von + anteil * (bis - von), taille + (rohr - taille) * hub]);
      }
    }
  }

  liste.push(
    [aRechts - g.uebergang, rohr], [aRechts - dicke, bund],
    [aRechts - dicke, rFr], [aRechts + dicke, rFr],
  );
  liste.push([aRechts + dicke, bund], [aRechts + g.freilaufAb, bund]);

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
                          rLinks, rRechts, antriebsart, schalenArt, nabe.art,
                          nabenBauform(nabe.name));

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

  // Antriebsseite: Nuten des Freilaufkörpers oder Gewindestriche. Bei der
  // Rohloff steckt der Ritzelträger schon in der nachgezeichneten Kontur.
  const istRohloff = nabenBauform(nabe.name) === "rohloff";
  let antriebsdetail = "";
  if (istRohloff) {
    antriebsdetail = "";
  } else if (antriebsart === "kassette") {
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

  // Rändelung am Lagersitz links – das ist der Verschlussring einer
  // Scheibenbremsnabe. Ein Nabendynamo hat dort eine glatte Endkappe und
  // stattdessen rechts den Kabelanschluss.
  const [bund] = schale(schalenArt, rLinks, rRechts);
  const istDynamo = nabe.art === "Dynamo";
  const sitzHalb = Math.min(GESTALT.sitz, bund * 0.92) * skala * 0.94;
  let riffel = "";
  if (istRohloff) {
    riffel = "";          // ihr Umriss trägt seine Absätze selbst
  } else if (istDynamo) {
    const xk = xFr + GESTALT.bundAb * skala;
    const breite = Math.max(2 * skala, 3);
    for (const versatz of [-0.45, 0.45]) {
      const y = mitteY + versatz * bund * skala;
      riffel += `<rect x="${rund(xk)}" y="${rund(y - breite / 2)}" `
        + `width="${rund(breite * 1.6)}" height="${rund(breite)}" class="anschluss"/>`;
    }
  } else {
    const rx1 = xFl - GESTALT.sitzAb * skala;
    const rx2 = xFl - GESTALT.bundAb * skala;
    for (let x = rx1 + 1.5; x < rx2; x += Math.max(2, 0.9 * skala)) {
      riffel += `<line x1="${rund(x)}" y1="${rund(mitteY - sitzHalb)}" `
        + `x2="${rund(x)}" y2="${rund(mitteY + sitzHalb)}"/>`;
    }
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
