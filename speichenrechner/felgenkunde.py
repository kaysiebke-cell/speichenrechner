"""Felgentypen: was die Bauform für den Laufradbau bedeutet.

Die Angaben stammen aus ``data/felgen_katalog.json`` und stehen dort **im
Wortlaut der Tabelle** – „einfach genietet“, „nicht üblich“, „Aluminium/Stahl“.
Gedeutet wird hier, an einer Stelle:

* :attr:`Felgentyp.profil` sagt, welches Profil die Skizze zeichnet.
* :attr:`Felgentyp.wandung` unterscheidet ein- und doppelwandig – abgeleitet
  aus der Beschreibungsspalte, nicht geraten.
* :attr:`Felgentyp.spannungsbereich` gibt Anhaltswerte für die Speichenspannung.
* :meth:`Felgentyp.hinweise` liefert, was beim Einspeichen dieser Bauform zu
  beachten ist.

Anders als der Nabenkatalog kennt dieses Modul keine Nachträge: die Tabelle
beschreibt Bauformen, keine Einzelmodelle mit Maßen.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .pfade import projekt_verzeichnis

KATALOG_DATEI = "felgen_katalog.json"

#: Anhaltswerte für die Speichenspannung an der Felge, in Newton.
#:
#: Was der Felgenhersteller angibt, geht **immer** vor – diese Spannen sind
#: nur eine Einordnung, wenn nichts angegeben ist. Nennt ein Typ mehrere
#: Materialien („Aluminium/Stahl“), zählt das schwächere: es begrenzt.
SPANNUNG_JE_MATERIAL = {
    "Stahl": (500.0, 800.0),
    "Aluminium": (800.0, 1100.0),
    "Carbon": (900.0, 1200.0),
}

#: Reihenfolge von schwach nach fest – bestimmt, welches Material begrenzt.
MATERIAL_REIHENFOLGE = ("Stahl", "Aluminium", "Carbon", "Titan")

#: Erkennungswörter für das Material in der Spalte „Material“.
MATERIALWOERTER = (
    ("stahl", "Stahl"),
    ("alumini", "Aluminium"),
    ("carbon", "Carbon"),
    ("cfk", "Carbon"),
    ("titan", "Titan"),
)

#: Bauform → Profil für die Skizze. Der erste Treffer im Namen gewinnt.
PROFILWOERTER = (
    ("flachbett", "flachbett"),
    ("hohlkammer", "hohlkammer"),
    ("box-section", "hohlkammer"),
    ("v-profil", "v-profil"),
    ("aero", "aero"),
    ("hakenlos", "hakenlos"),
    ("hookless", "hakenlos"),
    ("haken", "haken"),
    ("tubeless", "tubeless"),
    ("schlauchreifen", "schlauch"),
    ("tubular", "schlauch"),
)

#: Profil, wenn der Name nichts hergibt – die Hohlkammer ist der Normalfall.
PROFIL_STANDARD = "hohlkammer"

#: Unter diesem ERD ist ein Laufrad kleiner als 20 Zoll. Genauer geht es
#: nicht: 16 und 18 Zoll liegen beim ERD dicht beieinander.
ERD_KINDERRAD = 360.0


@dataclass(frozen=True)
class Felgentyp:
    """Ein Felgentyp, wie ihn die Tabelle beschreibt."""

    name: str
    kategorie: str = ""        # Bauform, Material, Einsatzbereich
    material: str = ""
    beschreibung: str = ""
    einsatz: str = ""
    oesung: str = ""
    kindergroessen: str = ""

    # ---------------------------------------------------------- Ausgewertet

    @property
    def materialien(self) -> tuple[str, ...]:
        """Die genannten Werkstoffe, schwächster zuerst."""
        text = self.material.lower()
        gefunden = {name for wort, name in MATERIALWOERTER if wort in text}
        return tuple(m for m in MATERIAL_REIHENFOLGE if m in gefunden)

    @property
    def profil(self) -> str:
        """Welches Profil die Skizze zeichnet."""
        text = self.name.lower()
        for wort, profil in PROFILWOERTER:
            if wort in text:
                return profil
        return PROFIL_STANDARD

    @property
    def oesen_stufe(self) -> int:
        """0 = ohne Ösen, 1 = einfach genietet, 2 = doppelt genietet."""
        text = self.oesung.lower()
        if "doppelt" in text:
            return 2
        if "einfach" in text or "genietet" in text or "geöst" in text:
            return 1
        return 0

    @property
    def wandung(self) -> str:
        """``doppelwandig``, ``einwandig`` oder leer, wenn die Tabelle schweigt.

        Abgeleitet aus dem, was in der Beschreibung steht – „Doppelwandig,
        Hohlkammerprofil“, „Luftdichte Kammer“, „Flacher Boden“ –, nicht aus
        dem Namen geraten. Eine doppelte Nietung setzt zwei Wände voraus.
        """
        text = f"{self.beschreibung} {self.oesung}".lower()
        if any(wort in text for wort in ("doppelwandig", "hohlkammer", "kammer", "doppelt")):
            return "doppelwandig"
        if any(wort in text for wort in ("flacher boden", "flache felge", "einwandig")):
            return "einwandig"
        return ""

    @property
    def spannungsbereich(self) -> tuple[float, float] | None:
        """Anhaltswerte für die Speichenspannung in N, oder ``None``.

        Bei mehreren Materialien begrenzt das schwächere – eine Felge aus
        „Aluminium/Stahl“ wird nicht fester gespannt, nur weil es sie auch aus
        Aluminium gibt.
        """
        for werkstoff in self.materialien:
            bereich = SPANNUNG_JE_MATERIAL.get(werkstoff)
            if bereich:
                return bereich
        return None

    @property
    def kindergroessen_zoll(self) -> tuple[int, ...]:
        """Die Zollgrößen aus der letzten Spalte, ``()`` bei „nicht üblich“."""
        if self.nur_ab_20_zoll:
            return ()
        zahlen = []
        for teil in self.kindergroessen.replace("/", " ").split():
            if teil.isdigit():
                zahlen.append(int(teil))
        return tuple(zahlen)

    @property
    def nur_ab_20_zoll(self) -> bool:
        """True, wenn die Tabelle diesen Typ für Kinderräder ausschließt."""
        return "nicht üblich" in self.kindergroessen.lower()

    # -------------------------------------------------------------- Anzeige

    @property
    def kurzbeschreibung(self) -> str:
        """Eine Zeile mit dem Wichtigsten – für die Anzeige unter der Auswahl."""
        teile = [self.beschreibung] if self.beschreibung else []
        if self.material:
            teile.append(self.material)
        if self.oesung and self.oesen_stufe:
            teile.append(f"Ösen: {self.oesung}")
        elif self.oesung:
            teile.append("ohne Ösen")
        return "  ·  ".join(teile)

    @property
    def listentext(self) -> str:
        """Zeile für die Auswahlliste – nur der Name.

        Die Kategorie steht schon im Filter darüber und in der Beschreibung
        darunter. Sie hier zu wiederholen machte die Klappliste so breit, dass
        sie die Eingabespalte aufblähte.
        """
        return self.name

    def hinweise(self) -> list[str]:
        """Was diese Bauform für den Laufradbau bedeutet – fachliche Einordnung."""
        meldungen: list[str] = []
        werkstoffe = self.materialien

        if self.oesen_stufe == 0 and self.wandung == "einwandig":
            meldungen.append(
                f"{self.name}: einwandig und ohne Ösen – der Nippel drückt direkt "
                "aufs Felgenbett. Unterlegscheiben verteilen die Kraft; sie "
                "vergrößern den wirksamen ERD und stehen im Reiter „Speichen“."
            )
        elif self.oesen_stufe == 2:
            meldungen.append(
                f"{self.name}: doppelt genietet – die Öse stützt sich auf beiden "
                "Wänden ab. Diese Felgen vertragen die hohe Spannung am oberen "
                "Ende der Spanne."
            )

        if "Carbon" in werkstoffe:
            meldungen.append(
                "Carbon: die Höchstspannung des Felgenherstellers ist verbindlich, "
                "nicht die Faustregel. Viele Carbonfelgen verlangen zusätzlich "
                "Unterlegscheiben unter dem Nippel."
            )
        if "Stahl" in werkstoffe:
            meldungen.append(
                "Stahlfelge: weicher als Aluminium und weniger rund. Niedriger "
                "spannen und beim Zentrieren mehr Durchgänge einplanen."
            )
        if "Titan" in werkstoffe:
            meldungen.append(
                "Titanfelgen sind Einzelstücke – für die Spannung gibt es keine "
                "Faustregel, nur die Angabe dessen, der sie gebaut hat."
            )

        if self.profil == "schlauch":
            meldungen.append(
                "Schlauchreifenfelge: der Reifen wird aufgeklebt, das Felgenbett "
                "ist flach. Den ERD hier unbedingt messen – die Angaben der "
                "Hersteller beziehen sich oft auf etwas anderes."
            )
        if self.profil == "hakenlos":
            meldungen.append(
                "Hakenlos: für die Speichenlänge ändert sich nichts, für den "
                "Reifen schon – hakenlose Felgen sind meist auf etwa 5 bar "
                "begrenzt und nur für freigegebene Reifen zugelassen."
            )

        return meldungen

    def warnungen(self, erd: float = 0.0, spannung: float = 0.0) -> list[str]:
        """Was am gerechneten Laufrad nicht zu dieser Bauform passt.

        Ohne ``erd`` und ``spannung`` gibt es nichts zu vergleichen und die
        Liste bleibt leer.
        """
        meldungen: list[str] = []

        bereich = self.spannungsbereich
        if bereich and spannung > 0:
            unten, oben = bereich
            if spannung > oben:
                meldungen.append(
                    f"{spannung:.0f} N liegen über dem, was für "
                    f"{self._materialtext()} üblich ist ({unten:.0f}–{oben:.0f} N). "
                    "Ohne ausdrückliche Herstellerfreigabe ist das zu viel."
                )
            elif spannung < unten:
                meldungen.append(
                    f"{spannung:.0f} N sind für {self._materialtext()} wenig "
                    f"({unten:.0f}–{oben:.0f} N sind üblich) – zu locker gespannte "
                    "Speichen brechen am Bogen."
                )

        if 0 < erd < ERD_KINDERRAD and self.nur_ab_20_zoll:
            meldungen.append(
                f"Der ERD von {erd:.0f} mm gehört zu einem Laufrad unter 20 Zoll. "
                f"Für diese Größen führt die Tabelle „{self.name}“ als nicht üblich."
            )

        return meldungen

    def _materialtext(self) -> str:
        werkstoffe = self.materialien
        return werkstoffe[0] if werkstoffe else self.material or "diese Felge"


@dataclass(frozen=True)
class Felgenkunde:
    """Alle Felgentypen samt Fußnoten der Tabelle."""

    quelle: str = ""
    typen: tuple[Felgentyp, ...] = field(default_factory=tuple)
    fussnoten: tuple[str, ...] = field(default_factory=tuple)

    def kategorien(self) -> list[str]:
        """Die vorkommenden Kategorien in der Reihenfolge der Tabelle."""
        gefunden: list[str] = []
        for typ in self.typen:
            if typ.kategorie and typ.kategorie not in gefunden:
                gefunden.append(typ.kategorie)
        return gefunden

    def nach_kategorie(self, kategorie: str = "") -> list[Felgentyp]:
        """Alle Typen, wahlweise nur die einer Kategorie."""
        if not kategorie:
            return list(self.typen)
        return [typ for typ in self.typen if typ.kategorie == kategorie]

    def finde(self, name: str) -> Felgentyp | None:
        """Sucht über den Namen – so, wie er in der Felge gespeichert ist."""
        if not name:
            return None
        for typ in self.typen:
            if typ.name == name:
                return typ
        return None


# --------------------------------------------------------------------- Laden

_zwischenspeicher: Felgenkunde | None = None


def _katalogdatei():
    return projekt_verzeichnis() / "data" / KATALOG_DATEI


def neu_laden() -> None:
    """Verwirft den Zwischenspeicher – nach einer Änderung nötig."""
    global _zwischenspeicher
    _zwischenspeicher = None


def lade() -> Felgenkunde:
    """Liest die Felgentypen; fehlt die Datei, bleibt die Kunde leer."""
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

    felder = set(Felgentyp.__dataclass_fields__)
    typen = tuple(
        Felgentyp(**{f: satz.get(f, "") for f in felder})
        for satz in daten.get("felgen", [])
        if isinstance(satz, dict) and satz.get("name")
    )
    fussnoten = tuple(t for t in daten.get("fussnoten", []) if isinstance(t, str))

    _zwischenspeicher = Felgenkunde(
        quelle=daten.get("quelle", ""), typen=typen, fussnoten=fussnoten
    )
    return _zwischenspeicher


def finde(name: str) -> Felgentyp | None:
    """Kurzer Weg zu einem Typ – der Name steht in :class:`~.modelle.Felge`."""
    return lade().finde(name)


def als_listeneintraege(kategorie: str = "") -> list[tuple[str, Felgentyp]]:
    """Felgentypen als ``(Anzeigetext, Typ)`` für die Auswahlliste."""
    return [(typ.listentext, typ) for typ in lade().nach_kategorie(kategorie)]
