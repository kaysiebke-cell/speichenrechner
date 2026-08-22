// Das Gerüst der Handy-Fassung: Reiterleiste unten und die Kennwerte im Kopf.
//
// Beides gilt nur am schmalen Schirm. Ab 44 rem stehen alle Blätter zugleich
// zweispaltig da – dann wird hier alles wieder abgeräumt, samt der ARIA-Rollen:
// „tablist“ über einer unsichtbaren Leiste, deren Blätter ohnehin alle offen
// sind, wäre für die Sprachausgabe schlicht gelogen.

/** Ab hier gilt der Reiterbetrieb – ein Pixel unter dem Umbruch in stil.css. */
const SCHMAL = "(max-width: 43.9375rem)";

/** Welches Blatt zuletzt offen war. Getrennt von den Eingaben gespeichert. */
const BLATT_SPEICHER = "speichenrechner.blatt";

/**
 * Verdrahtet Reiterleiste und Kennwerte-Knopf.
 *
 * Erwartet im HTML: eine Leiste `#reiter` mit Knöpfen, deren `data-ziel` auf
 * die Kennung des zugehörigen `.blatt` zeigt.
 */
export function reiterAufbauen() {
  const leiste = document.getElementById("reiter");
  if (!leiste) return;

  const knoepfe = Array.from(leiste.querySelectorAll("button"));
  const blaetter = knoepfe.map((knopf) => document.getElementById(knopf.dataset.ziel));
  if (blaetter.some((blatt) => blatt === null)) return;

  const rollflaeche = document.querySelector("main");
  const einzelheiten = document.getElementById("einzelheiten");
  const kennwerte = document.getElementById("kennwerte");
  const schmal = window.matchMedia(SCHMAL);
  let offen = 0;

  function merken() {
    try {
      localStorage.setItem(BLATT_SPEICHER, String(offen));
    } catch (_fehler) {
      // Privater Modus o. Ä. – dann fängt die App eben wieder bei der Nabe an.
    }
  }

  function gemerktesBlatt() {
    let wert;
    try {
      wert = localStorage.getItem(BLATT_SPEICHER);
    } catch (_fehler) {
      return 0;
    }
    const nummer = Number(wert);
    return Number.isInteger(nummer) && nummer >= 0 && nummer < knoepfe.length ? nummer : 0;
  }

  /** Zeigt ein Blatt und versteckt die übrigen. */
  function zeigen(nummer, mitFokus = false) {
    offen = Math.min(Math.max(nummer, 0), knoepfe.length - 1);
    knoepfe.forEach((knopf, i) => {
      const an = i === offen;
      knopf.setAttribute("aria-selected", an ? "true" : "false");
      // Nur der offene Reiter liegt in der Tabulatorfolge; zwischen den
      // Reitern führen die Pfeiltasten. So will es das Reitermuster.
      knopf.tabIndex = an ? 0 : -1;
      blaetter[i].hidden = !an;
    });
    if (mitFokus) knoepfe[offen].focus();
    if (rollflaeche) rollflaeche.scrollTop = 0;
    merken();
  }

  function anschalten() {
    leiste.setAttribute("role", "tablist");
    knoepfe.forEach((knopf, i) => {
      knopf.setAttribute("role", "tab");
      knopf.setAttribute("aria-controls", blaetter[i].id);
      blaetter[i].setAttribute("role", "tabpanel");
      blaetter[i].setAttribute("aria-labelledby", knopf.id);
    });
    zeigen(gemerktesBlatt());
    zuklappen();
  }

  function abschalten() {
    leiste.removeAttribute("role");
    knoepfe.forEach((knopf, i) => {
      for (const merkmal of ["role", "aria-controls", "aria-selected"]) {
        knopf.removeAttribute(merkmal);
      }
      knopf.tabIndex = 0;
      // Wichtig: ohne das bliebe ein verstecktes Blatt auch breit versteckt.
      blaetter[i].hidden = false;
      blaetter[i].removeAttribute("role");
      blaetter[i].removeAttribute("aria-labelledby");
    });
    if (kennwerte) kennwerte.hidden = false;
    if (einzelheiten) einzelheiten.setAttribute("aria-expanded", "true");
  }

  function zuklappen() {
    if (!einzelheiten || !kennwerte) return;
    kennwerte.hidden = true;
    einzelheiten.setAttribute("aria-expanded", "false");
  }

  knoepfe.forEach((knopf, i) => {
    knopf.addEventListener("click", () => {
      if (schmal.matches) zeigen(i);
    });
    knopf.addEventListener("keydown", (ereignis) => {
      if (!schmal.matches) return;
      const schritte = { ArrowLeft: -1, ArrowRight: 1 };
      if (ereignis.key in schritte) {
        const anzahl = knoepfe.length;
        zeigen((offen + schritte[ereignis.key] + anzahl) % anzahl, true);
      } else if (ereignis.key === "Home") {
        zeigen(0, true);
      } else if (ereignis.key === "End") {
        zeigen(knoepfe.length - 1, true);
      } else {
        return;
      }
      ereignis.preventDefault();
    });
  });

  if (einzelheiten && kennwerte) {
    einzelheiten.addEventListener("click", () => {
      const zeigt = einzelheiten.getAttribute("aria-expanded") === "true";
      einzelheiten.setAttribute("aria-expanded", zeigt ? "false" : "true");
      kennwerte.hidden = zeigt;
    });
  }

  const umschalten = () => (schmal.matches ? anschalten() : abschalten());
  schmal.addEventListener("change", umschalten);
  umschalten();
}
