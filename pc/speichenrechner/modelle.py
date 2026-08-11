"""Datenklassen des Speichenrechners.

Hier stehen ausschließlich Daten – keine Berechnung, keine GUI.
Alle Längen sind in Millimetern, alle Winkel in Grad.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict

from .formatierung import zahl
from .speiche import BAUARTEN, E_MODUL, SPANNUNG_STANDARD, WEITUNG_STANDARD


#: Ritzelaufnahmen, die auf einem Freilaufkörper mit Verzahnung sitzen.
AUFNAHME_KASSETTE = ("Kassette", "Steckritzel", "Steckzahnkranz")

#: Ritzelaufnahmen, die auf ein Gewinde geschraubt werden.
AUFNAHME_GEWINDE = ("Schraubkranz", "Schraubritzel", "Singlespeed")

#: Bauarten ohne Antriebsseite – ein Vorderrad hat keine Ritzel.
OHNE_ANTRIEB = ("Vorderrad", "Dynamo")

#: Bauarten mit großer Nabenschale: im Dynamo steckt der Generator, in der
#: Nabenschaltung das Getriebe. Beide sind deutlich dicker als eine Kettennabe.
GROSSE_SCHALE = ("Dynamo", "Nabenschaltung")


@dataclass
class Nabe:
    """Geometrie einer Nabe.

    ``flanschabstand_*`` ist der Abstand von der Nabenmitte (Felgenmittelebene)
    bis zur Mitte des jeweiligen Flansches.

    ``art`` und ``aufnahme`` beschreiben die Bauart (Vorderrad, Dynamo,
    Nabenschaltung, Hinterrad) und die Ritzelaufnahme (Kassette, Schraubkranz
    …). Sie gehen **nicht** in die Rechnung ein – die Speichenlänge hängt nur
    an der Geometrie. Sie bestimmen, was gezeichnet wird.
    """

    name: str = "Eigene Nabe"
    flanschdurchmesser_links: float = 45.0
    flanschdurchmesser_rechts: float = 45.0
    flanschabstand_links: float = 35.0
    flanschabstand_rechts: float = 20.0
    speichenloch: float = 2.6
    flanschdicke: float = 3.2
    art: str = ""         # Vorderrad, Dynamo, Nabenschaltung, Hinterrad …
    aufnahme: str = ""    # Kassette, Schraubkranz, Schraubritzel …

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, daten: dict) -> "Nabe":
        gueltig = {f: daten[f] for f in cls.__dataclass_fields__ if f in daten}
        return cls(**gueltig)

    # ------------------------------------------------------- Für die Skizze

    @property
    def antrieb(self) -> str:
        """Was rechts an der Nabe sitzt: ``kassette``, ``gewinde`` oder ``keiner``.

        Die Bauart gewinnt vor der Aufnahme: ein Nabendynamo bleibt ohne
        Antriebsseite, auch wenn in der Tabelle etwas anderes stünde. Ist
        nichts bekannt, wird der häufigste Fall gezeichnet.
        """
        if self.art in OHNE_ANTRIEB:
            return "keiner"
        # Eine Nabenschaltung bekommt nie einen Kassettenkörper: das Ritzel
        # sitzt auf einem kurzen Stummel, aufgeschraubt oder aufgesteckt.
        # Auch wenn die Tabelle „Steckritzel“ sagt, ist das kein Kassettenkörper.
        if self.art == "Nabenschaltung":
            return "gewinde"
        if self.aufnahme in AUFNAHME_GEWINDE:
            return "gewinde"
        if self.aufnahme in AUFNAHME_KASSETTE:
            return "kassette"
        return "kassette"

    @property
    def schale(self) -> str:
        """``gross`` bei Dynamo und Nabenschaltung, sonst ``normal``."""
        return "gross" if self.art in GROSSE_SCHALE else "normal"

    @property
    def merkmale(self) -> tuple[str, ...]:
        """Alle Schubladen, in die diese Nabe gehört – wie im Nabenkatalog.

        Bauart **und** Ritzelaufnahme stehen nebeneinander: eine Rohloff ist
        eine Nabenschaltung *und* hat ein Schraubritzel. Ohne das fände man
        eine Vorlage nur unter ihrer Bauart, während dieselbe Nabe im Katalog
        unter beidem steht – der Filter wirkte dann willkürlich.
        """
        gefunden = []
        for merkmal in (self.art, self.aufnahme):
            if merkmal and merkmal not in gefunden:
                gefunden.append(merkmal)
        return tuple(gefunden)


@dataclass
class Felge:
    """Geometrie einer Felge.

    ``erd`` ist der effektive Felgendurchmesser (Effective Rim Diameter),
    gemessen von Nippelsitz zu Nippelsitz.

    ``versatz`` beschreibt eine asymmetrische Felge: positive Werte bedeuten,
    dass das Speichenbett zur rechten Seite (Antriebsseite) versetzt ist.

    ``typ`` ist der Name eines Felgentyps aus :mod:`~speichenrechner.felgenkunde`
    („Hohlkammerfelge (Box-Section)“, „Stahlfelge“ …). Er ändert die
    Speichenlänge nicht, wohl aber die Hinweise und das gezeichnete Profil.
    """

    name: str = "Eigene Felge"
    erd: float = 600.0
    versatz: float = 0.0
    typ: str = ""

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, daten: dict) -> "Felge":
        gueltig = {f: daten[f] for f in cls.__dataclass_fields__ if f in daten}
        return cls(**gueltig)


#: Länge eines gewöhnlichen Nippels in mm. Alles darüber nimmt mehr Gewinde
#: auf, die Speiche darf entsprechend kürzer sein.
NIPPEL_STANDARD = 12.0

#: Nippellängen, die es im Handel gibt.
NIPPEL_LAENGEN = (12.0, 14.0, 16.0)


def nippel_abzug(laenge: float) -> float:
    """Wie viel kürzer die Speiche bei dieser Nippellänge sein darf, in mm.

    Ein 14-mm-Nippel greift 2 mm tiefer als der übliche 12-mm-Nippel, ein
    16-mm-Nippel 4 mm. Anhaltswert – wer eine Herstellerangabe hat, trägt sie
    von Hand ein.
    """
    return max(0.0, laenge - NIPPEL_STANDARD)


#: Wo die Speichenköpfe am Flansch sitzen.
KOPFLAGEN = {
    "gemischt": "gemischt (Standard)",
    "innen": "alle Köpfe innen",
    "außen": "alle Köpfe außen",
}


#: Wie sich die Speichen auf die beiden Seiten verteilen.
VERTEILUNGEN = {
    "1:1": "gleich verteilt (1:1)",
    "2:1": "2:1 – rechts doppelt so viele",
}


@dataclass
class Einspeichung:
    """Speichenzahl, Verteilung auf die Seiten und Kreuzungen je Seite.

    ``verteilung`` ist ``"1:1"`` (der Normalfall, je Seite die Hälfte) oder
    ``"2:1"``: dann trägt die rechte Seite doppelt so viele Speichen wie die
    linke. Das gleicht beim Hinterrad die Spannung an und setzt eine Nabe
    voraus, deren Flansche dafür gebohrt sind.
    """

    speichenzahl: int = 32
    kreuzungen_links: int = 3
    kreuzungen_rechts: int = 3
    verteilung: str = "1:1"

    @property
    def speichen_links(self) -> int:
        if self.verteilung == "2:1":
            return self.speichenzahl // 3
        return self.speichenzahl // 2

    @property
    def speichen_rechts(self) -> int:
        return self.speichenzahl - self.speichen_links

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, daten: dict) -> "Einspeichung":
        gueltig = {f: daten[f] for f in cls.__dataclass_fields__ if f in daten}
        return cls(**gueltig)


@dataclass
class Speichensatz:
    """Welche Speichen verbaut werden und wie fest sie gespannt sind.

    ``spannung`` ist der Zielwert der stärker gespannten Seite in Newton; die
    andere Seite ergibt sich aus dem Spannungsverhältnis.

    ``korrektur_anwenden`` zieht drei Anteile von der Bestelllänge ab:
    die elastische Dehnung, die ``weitung`` von Nabenflansch und Speichenbogen
    unter Last und ``nippel_verkuerzung`` für längere Nippel.

    ``nippellaenge`` ist die Länge des Nippels in mm, wie sie auf der Packung
    steht. ``nippel_verkuerzung`` ist der daraus abgeleitete Abzug – die Größe,
    mit der gerechnet wird. Beides steht getrennt da, weil eine Herstellerangabe
    von der Faustregel abweichen darf; :func:`nippel_abzug` liefert die Regel.
    """

    bauart: str = BAUARTEN[1].name
    eigene_bauart: dict | None = None
    e_modul: float = E_MODUL
    spannung: float = SPANNUNG_STANDARD
    korrektur_anwenden: bool = False
    weitung: float = WEITUNG_STANDARD
    nippellaenge: float = NIPPEL_STANDARD
    nippel_verkuerzung: float = 0.0
    unterlegscheibe: float = 0.0
    straightpull: bool = False
    kopf: str = "gemischt"

    def as_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, daten: dict) -> "Speichensatz":
        gueltig = {f: daten[f] for f in cls.__dataclass_fields__ if f in daten}
        return cls(**gueltig)


@dataclass
class SeitenErgebnis:
    """Ergebnis für eine Radseite.

    ``laenge`` ist die geometrische Länge im gespannten Laufrad,
    ``laenge_gerundet`` die daraus abgeleitete Bestelllänge.
    """

    seite: str
    laenge: float
    laenge_gerundet: float
    speichenwinkel: float
    kreuzungen: int
    speichen: int
    sehnenwinkel: float
    felgenwinkel: float = 0.0
    lochabstand: float = 0.0
    spannung: float = 0.0
    dehnung: float = 0.0
    korrektur: float = 0.0
    drahtspannung: float = 0.0
    frequenz: float = 0.0
    gewicht: float = 0.0


@dataclass
class Ergebnis:
    """Gesamtergebnis einer Berechnung.

    ``hinweise`` sind Warnungen zur Eingabe, ``bewertungen`` sind fachliche
    Einordnungen des Ergebnisses (Speichenwinkel, Spannungsverhältnis).
    """

    links: SeitenErgebnis
    rechts: SeitenErgebnis
    spannung_links_prozent: float = 100.0
    spannung_rechts_prozent: float = 100.0
    hinweise: list[str] = field(default_factory=list)
    bewertungen: list[str] = field(default_factory=list)

    @property
    def symmetrisch(self) -> bool:
        """Beide Seiten sind rechnerisch gleich lang."""
        return abs(self.links.laenge - self.rechts.laenge) < 0.05

    @property
    def gleiche_bestelllaenge(self) -> bool:
        """Beide Seiten landen auf derselben Bestelllänge.

        Das ist der Fall, auf den es beim Bestellen ankommt: 157,18 und
        156,92 mm sind rechnerisch verschieden, gerundet aber dieselbe
        Speiche. Dann gibt es nur einen Posten und nichts zu vertauschen.
        """
        return self.links.laenge_gerundet == self.rechts.laenge_gerundet

    @property
    def einkaufsliste(self) -> list[str]:
        """Was zu bestellen ist – gleiche Bestelllängen werden zusammengefasst."""
        if self.gleiche_bestelllaenge:
            gesamt = self.links.speichen + self.rechts.speichen
            return [f"{gesamt} × {zahl(self.links.laenge_gerundet)} mm"]
        return [
            f"{seite.speichen} × {zahl(seite.laenge_gerundet)} mm ({bezeichnung})"
            for seite, bezeichnung in ((self.links, "links"), (self.rechts, "rechts"))
        ]
