"""Nabenkatalog: Modelle vieler Hersteller zum Nachschlagen.

Der Katalog hält die Angaben **so, wie sie in der Herstellertabelle stehen** –
mit allen Schreibweisen wie ``47,5 (22,5/25)`` oder ``k. A.``. Ausgewertet wird
beim Laden über :mod:`speichenrechner.tabelle`.

Zwei Quellen fließen zusammen:

* ``data/naben_katalog.json`` – aus der Tabelle erzeugt, wird bei jedem Lauf
  von ``werkzeuge/katalog_erzeugen.py`` überschrieben.
* ``~/.config/speichenrechner/naben_ergaenzungen.json`` – was im Fenster
  „Nabentabelle“ nachgetragen wurde. Diese Datei bleibt erhalten, auch wenn
  der Katalog neu erzeugt wird.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from . import tabelle
from .pfade import konfig_verzeichnis, projekt_verzeichnis

KATALOG_DATEI = "naben_katalog.json"
ERGAENZUNGEN_DATEI = "naben_ergaenzungen.json"

#: Mitgelieferte Naben, die **nicht** aus der Herstellertabelle stammen –
#: nachgetragene Modelle mit Quellenangabe. Eine eigene Datei, damit die
#: Tabelle die Tabelle bleibt und ``katalog_erzeugen.py`` sie nicht überschreibt.
ZUSATZ_DATEI = "naben_zusatz.json"

#: Herkunftsangabe für Modelle ohne belegte Maße.
UNGEPRUEFT = "ungeprüft"

#: Bauart für Systeme, die keine Laufradnabe sind – Tretlager-Getriebe wie
#: Pinion oder Effigear. Sie stehen in der Tabelle, lassen sich aber nicht
#: einspeichen und gehören deshalb nicht in die Nabenauswahl.
KEIN_LAUFRAD = "Tretlagergetriebe"

#: Ritzelaufnahmen, erkannt an der Freilaufspalte. Reihenfolge zählt: der
#: erste Treffer gewinnt, „Schraubritzel“ steckt in keinem anderen Wort.
AUFNAHMEN = (
    ("schraubritzel", "Schraubritzel"),
    ("schraubkranz", "Schraubkranz"),
    ("gewindekranz", "Schraubkranz"),
    ("steckzahnkranz", "Steckzahnkranz"),
    ("push-on", "Steckzahnkranz"),
    ("steckritzel", "Steckritzel"),
    ("micro spline", "Kassette"),
    ("freilaufkörper", "Kassette"),
    ("kassette", "Kassette"),
    ("hg", "Kassette"),
    ("xd", "Kassette"),
)

#: Felder, die sich nachtragen lassen – Reihenfolge wie in der Tabelle.
SPALTEN = (
    ("lochzahl", "Lochzahl"),
    ("einbaubreite", "Einbaubreite / OLD"),
    ("achstyp", "Achstyp"),
    ("bremse", "Bremsaufnahme"),
    ("speichenloch", "Speichenloch-Ø"),
    ("flanschabstand", "Flanschabstand L/R"),
    ("flanschdurchmesser", "Flansch-Ø L/R"),
    ("freilauf", "Freilauf / Ritzeltyp"),
)


@dataclass(frozen=True)
class Katalogeintrag:
    """Eine Nabe aus dem Katalog – Texte wie in der Tabelle, dazu die Zahlen."""

    hersteller: str
    art: str
    modell: str
    lochzahl: str = ""
    einbaubreite: str = ""
    achstyp: str = ""
    bremse: str = ""
    speichenloch: str = ""
    flanschabstand: str = ""
    flanschdurchmesser: str = ""
    freilauf: str = ""
    aufnahme_blatt: str = ""   # aus Querlisten wie „Nabe mit Kassette“
    ergaenzt: bool = False
    selbst_angelegt: bool = False
    quelle: str = ""           # gesetzt bei Naben aus data/naben_zusatz.json

    # ---------------------------------------------------------- Ausgewertet

    @property
    def lochzahlen(self) -> list[int]:
        return tabelle.ganze_zahlen(self.lochzahl)

    @property
    def einbaubreiten(self) -> list[float]:
        return tabelle.masse(self.einbaubreite)

    @property
    def speichenloch_mm(self) -> float | None:
        return tabelle.erste_zahl(self.speichenloch)

    @property
    def flanschabstaende(self) -> tuple[float, float] | None:
        return tabelle.seitenwerte(self.flanschabstand, ist_abstand=True)

    @property
    def flanschdurchmesser_paar(self) -> tuple[float, float] | None:
        return tabelle.seitenwerte(self.flanschdurchmesser, ist_abstand=False)

    @property
    def aufnahme(self) -> str:
        """Wie die Ritzel sitzen: Kassette, Schraubkranz, Steckritzel …

        Das ist **unabhängig von der Bauart** – eine Rohloff ist eine
        Nabenschaltung *und* hat ein Schraubritzel, eine Sturmey-Archer AW ist
        eine Nabenschaltung *und* hat einen Schraubkranz.
        """
        text = self.freilauf.lower()
        if not text or text.startswith("k. a."):
            return self.aufnahme_blatt

        # Nur ein führendes „entfällt“ verneint. Auf „kein Freilauf“ zu prüfen
        # wäre falsch: „Schraubkranz (klassisches Gewinde, kein Freilaufkörper)“
        # nennt sehr wohl eine Aufnahme.
        if text.startswith("entfällt"):
            return "Singlespeed" if "singlespeed" in text else ""

        for stichwort, name in AUFNAHMEN:
            if stichwort in text:
                return name

        # Sagt die Freilaufspalte nichts, zählt das Blatt, in dem die Nabe
        # gelistet ist – „Nabe mit Kassette“ ist selbst eine Aussage.
        return self.aufnahme_blatt

    @property
    def merkmale(self) -> tuple[str, ...]:
        """Alle Schubladen, in die diese Nabe gehört.

        Eine Nabe kann in mehreren stehen – ein SON-Dynamo ist Dynamo *und*
        Vorderrad, eine Rohloff ist Nabenschaltung *und* Schraubritzel. Genau
        deshalb ist der Filter eine Liste von Merkmalen und keine Einteilung
        in sich ausschließende Klassen.
        """
        gefunden = []
        if self.art:
            gefunden.append(self.art)
        if "vorderrad" in self.freilauf.lower() and "Vorderrad" not in gefunden:
            gefunden.append("Vorderrad")
        aufnahme = self.aufnahme
        if aufnahme and aufnahme not in gefunden:
            gefunden.append(aufnahme)
        return tuple(gefunden)

    @property
    def hat_flanschmasse(self) -> bool:
        """True, wenn sich mit dieser Nabe sofort rechnen lässt."""
        return self.flanschabstaende is not None and self.flanschdurchmesser_paar is not None

    # -------------------------------------------------------------- Anzeige

    @property
    def einspeichbar(self) -> bool:
        """False bei Tretlager-Getrieben – die haben kein Speichenloch."""
        return self.art != KEIN_LAUFRAD

    @property
    def schluessel(self) -> str:
        """Eindeutig über Hersteller und Modell – daran hängen Ergänzungen."""
        return f"{self.hersteller}|{self.modell}"

    @property
    def bezeichnung(self) -> str:
        """``Hersteller Modell`` – ohne Dopplung, wenn beides gleich anfängt."""
        if self.modell.lower().startswith(self.hersteller.lower()):
            return self.modell
        return f"{self.hersteller} {self.modell}"

    @property
    def listentext(self) -> str:
        """Zeile für die Auswahlliste – Name plus die wichtigsten Kennwerte."""
        teile = [self.bezeichnung]
        if self.hat_flanschmasse:
            # Diese Nabe lässt sich sofort durchrechnen – das gehört nach vorn.
            teile.append("✓ mit Flanschmaßen")
        if not tabelle.ist_leer(self.einbaubreite):
            teile.append(f"{self.einbaubreite} mm")
        if not tabelle.ist_leer(self.lochzahl):
            teile.append(f"{self.lochzahl} Loch")
        if not tabelle.ist_leer(self.bremse):
            teile.append(self.bremse)
        if self.freilauf_kurz:
            teile.append(self.freilauf_kurz)
        # Nachgetragene Naben nennen ihre Herkunft – man soll sehen, was aus der
        # eigenen Tabelle kommt und was nicht belegt ist.
        if self.quelle:
            teile.append("ungeprüft" if self.quelle == UNGEPRUEFT else "nachgetragen")
        return "  ·  ".join(teile)

    @property
    def aus_tabelle(self) -> bool:
        """False bei Naben aus ``naben_zusatz.json`` und selbst angelegten."""
        return not self.quelle and not self.selbst_angelegt

    @property
    def freilauf_kurz(self) -> str:
        """Der Freilauftyp in Kurzform – die Volltexte sind lang.

        „Shimano HG (9–11-fach) und SRAM XD (11/12-fach) als Wechsel…“ wird zu
        „HG · XD“. Was der Katalog als „entfällt“ führt, bleibt weg.
        """
        text = self.freilauf.lower()
        if not text or text.startswith("entfällt") or text.startswith("k. a."):
            return ""

        # „xd“ steckt auch in „xdr“ – deshalb getrennt prüfen.
        hat_xdr = "xdr" in text
        hat_xd = "xd" in text.replace("xdr", "")

        gefunden = []
        for treffer, kurz in (
            ("hg" in text, "HG"),
            ("micro spline" in text, "Micro Spline"),
            (hat_xd, "XD"),
            (hat_xdr, "XDR"),
            ("schraubkranz" in text, "Schraubkranz"),
            ("schraubritzel" in text, "Schraubritzel"),
            ("steckzahnkranz" in text, "Steckzahnkranz"),
            ("steckritzel" in text, "Steckritzel"),
        ):
            if treffer:
                gefunden.append(kurz)
        return " · ".join(gefunden[:3])

    @property
    def suchtext(self) -> str:
        return " ".join((
            self.hersteller, self.modell, self.art, self.achstyp, self.bremse,
            self.lochzahl, self.einbaubreite, self.freilauf, self.quelle,
        )).lower()

    def passt_zu(self, begriffe: list[str]) -> bool:
        text = self.suchtext
        return all(begriff in text for begriff in begriffe)

    def mit(self, **felder) -> "Katalogeintrag":
        """Kopie mit geänderten Feldern – Einträge selbst bleiben unveränderlich."""
        werte = {f: getattr(self, f) for f in self.__dataclass_fields__}
        werte.update(felder)
        return Katalogeintrag(**werte)


@dataclass(frozen=True)
class Katalog:
    """Alle Einträge samt Herkunftsangabe."""

    quelle: str = ""
    naben: tuple[Katalogeintrag, ...] = field(default_factory=tuple)

    def hersteller(self, art: str = "") -> list[str]:
        """Herstellernamen, wahlweise nur zu einem Merkmal."""
        return sorted({
            eintrag.hersteller for eintrag in self.naben
            if eintrag.hersteller and (not art or art in eintrag.merkmale)
        })

    def arten_mit_anzahl(self) -> list[tuple[str, int]]:
        """Die vorkommenden Merkmale mit ihrer Anzahl, häufigste zuerst.

        Bauart und Ritzelaufnahme stehen nebeneinander in einer Liste – eine
        Nabe taucht unter jedem ihrer Merkmale auf. Was sich nicht einspeichen
        lässt, taucht gar nicht auf.

        Die Anzahl gehört in die Auswahlliste: sonst sieht ein Merkmal mit nur
        sechs Naben wie ein Fehler des Filters aus, obwohl die Tabelle einfach
        nicht mehr hergibt.
        """
        zaehler: dict[str, int] = {}
        for eintrag in self.naben:
            if not eintrag.einspeichbar:
                continue
            for merkmal in eintrag.merkmale:
                zaehler[merkmal] = zaehler.get(merkmal, 0) + 1
        return [(name, zaehler[name])
                for name in sorted(zaehler, key=lambda name: (-zaehler[name], name))]

    def arten(self) -> list[str]:
        """Nur die Namen der Merkmale – Reihenfolge wie in :meth:`arten_mit_anzahl`."""
        return [name for name, _ in self.arten_mit_anzahl()]

    def hersteller_mit_anzahl(self, art: str = "") -> list[tuple[str, int]]:
        """Hersteller mit der Zahl ihrer Naben, wahlweise nur zu einem Merkmal."""
        zaehler: dict[str, int] = {}
        for eintrag in self.naben:
            if not eintrag.einspeichbar or not eintrag.hersteller:
                continue
            if art and art not in eintrag.merkmale:
                continue
            zaehler[eintrag.hersteller] = zaehler.get(eintrag.hersteller, 0) + 1
        return [(name, zaehler[name]) for name in sorted(zaehler)]

    def suche(self, text: str = "", hersteller: str = "", art: str = "") -> list[Katalogeintrag]:
        """Sucht über alle Felder; mehrere Wörter müssen alle vorkommen."""
        begriffe = [wort for wort in text.lower().split() if wort]
        treffer = [
            eintrag for eintrag in self.naben
            if (not hersteller or eintrag.hersteller == hersteller)
            and (not art or art in eintrag.merkmale)
            and (not begriffe or eintrag.passt_zu(begriffe))
        ]
        return sorted(treffer, key=lambda e: (e.hersteller.lower(), e.modell.lower()))


# --------------------------------------------------------------------- Laden

_zwischenspeicher: Katalog | None = None


def _katalogdatei():
    return projekt_verzeichnis() / "data" / KATALOG_DATEI


def _zusatzdatei():
    return projekt_verzeichnis() / "data" / ZUSATZ_DATEI


def lade_zusatz() -> list[dict]:
    """Nachgetragene Naben, die nicht aus der Herstellertabelle stammen."""
    pfad = _zusatzdatei()
    if not pfad.exists():
        return []
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(daten, dict):
        return []
    return [satz for satz in daten.get("naben", []) if isinstance(satz, dict)]


def _ergaenzungsdatei():
    return konfig_verzeichnis() / ERGAENZUNGEN_DATEI


def lade_ergaenzungen() -> dict[str, dict]:
    """Was im Bearbeitungsfenster nachgetragen wurde."""
    pfad = _ergaenzungsdatei()
    if not pfad.exists():
        return {}
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return daten if isinstance(daten, dict) else {}


def speichere_ergaenzungen(ergaenzungen: dict[str, dict]) -> None:
    """Schreibt die Nachträge und verwirft den Zwischenspeicher."""
    pfad = _ergaenzungsdatei()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(
        json.dumps(ergaenzungen, indent=1, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    neu_laden()


def neu_laden() -> None:
    """Verwirft den Zwischenspeicher – nach einer Änderung nötig."""
    global _zwischenspeicher
    _zwischenspeicher = None


def lade() -> Katalog:
    """Liest Katalog und Ergänzungen; fehlt der Katalog, bleibt er leer."""
    global _zwischenspeicher
    if _zwischenspeicher is not None:
        return _zwischenspeicher

    pfad = _katalogdatei()
    daten: dict = {}
    if pfad.exists():
        try:
            geladen = json.loads(pfad.read_text(encoding="utf-8"))
            if isinstance(geladen, dict):
                daten = geladen
        except (OSError, json.JSONDecodeError):
            daten = {}

    ergaenzungen = lade_ergaenzungen()
    felder = set(Katalogeintrag.__dataclass_fields__) - {"ergaenzt", "selbst_angelegt"}

    eintraege = []
    benutzt = set()
    # Erst die Tabelle, dann die nachgetragenen Naben – die aus der Tabelle
    # gewinnen, falls ein Modell doppelt auftaucht.
    bekannt: set[str] = set()
    for satz in list(daten.get("naben", [])) + lade_zusatz():
        if not isinstance(satz, dict) or not satz.get("modell"):
            continue
        eintrag = Katalogeintrag(**{f: satz.get(f, "") for f in felder})
        if eintrag.schluessel in bekannt:
            continue
        bekannt.add(eintrag.schluessel)

        nachtrag = ergaenzungen.get(eintrag.schluessel)
        if nachtrag:
            benutzt.add(eintrag.schluessel)
            gueltig = {f: w for f, w in nachtrag.items() if f in felder}
            eintrag = eintrag.mit(ergaenzt=True, **gueltig)
        eintraege.append(eintrag)

    # Nachträge ohne Gegenstück in der Tabelle sind selbst angelegte Naben.
    for schluessel, satz in ergaenzungen.items():
        if schluessel in benutzt or not isinstance(satz, dict):
            continue
        hersteller, _, modell = schluessel.partition("|")
        if not modell:
            continue
        werte = {f: satz.get(f, "") for f in felder}
        werte["hersteller"] = werte.get("hersteller") or hersteller
        werte["modell"] = werte.get("modell") or modell
        werte["art"] = werte.get("art") or "Hinterrad"
        eintraege.append(Katalogeintrag(**werte, ergaenzt=True, selbst_angelegt=True))

    _zwischenspeicher = Katalog(quelle=daten.get("quelle", ""), naben=tuple(eintraege))
    return _zwischenspeicher


def als_listeneintraege(art: str = "", hersteller: str = "") -> list[tuple[str, Katalogeintrag]]:
    """Katalognaben als ``(Anzeigetext, Eintrag)`` für die Auswahlliste.

    ``art`` schränkt auf eine Nabenart ein (Dynamo, Nabenschaltung, Kassette …),
    ``hersteller`` auf einen Hersteller. Naben mit vollständigen Flanschmaßen
    stehen zuerst – mit ihnen lässt sich ohne Nachmessen rechnen.
    """
    naben = [e for e in lade().suche(art=art, hersteller=hersteller) if e.einspeichbar]
    return [
        (eintrag.listentext, eintrag)
        for eintrag in sorted(naben, key=lambda e: (not e.hat_flanschmasse,
                                                    e.hersteller.lower(), e.modell.lower()))
    ]
