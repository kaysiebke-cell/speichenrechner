"""Zeichen-Werkzeugkasten für alle Skizzen.

Enthält die Theme-Farben, Text- und Bemaßungshilfen sowie die Basisklasse
:class:`ZeichenFlaeche`. Weil jede Skizze ihre Zeichenarbeit in einer eigenen
Methode ``zeichne`` erledigt, lässt sich dieselbe Zeichnung sowohl im Fenster
darstellen als auch in eine PNG-, PDF- oder SVG-Datei exportieren.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cairo
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
from gi.repository import Gtk, Pango, PangoCairo  # noqa: E402

from . import stil  # noqa: E402

Farbe = tuple[float, float, float, float]


@dataclass(frozen=True)
class Farben:
    """Farbsatz einer Skizze.

    Die Bauteilfarben sind **keine festen Werte**, sondern vom Akzent und von
    der Textfarbe des Themes abgeleitet: der Nabenkörper trägt den Akzent des
    Themes, Freilauf und Achse bleiben neutral. Damit wird die Zeichnung
    farbig, ohne dass die Anwendung ein eigenes Farbschema mitbringt.
    """

    text: Farbe
    akzent: Farbe
    linie: Farbe
    schwach: Farbe
    grund: Farbe | None = None

    @classmethod
    def vom_widget(cls, widget: Gtk.Widget) -> "Farben":
        """Farben aus dem aktiven GTK-Theme."""
        text = stil.vordergrund(widget)
        return cls(
            text=text,
            akzent=stil.akzent(widget),
            linie=(text[0], text[1], text[2], 0.75),
            schwach=(text[0], text[1], text[2], 0.35),
            grund=stil.hintergrund(widget),
        )

    @classmethod
    def fuer_export(cls) -> "Farben":
        """Dunkel auf Weiß – unabhängig vom Theme gut druckbar."""
        return cls(
            text=(0.12, 0.12, 0.12, 1.0),
            akzent=(0.16, 0.45, 0.72, 1.0),
            linie=(0.25, 0.25, 0.25, 1.0),
            schwach=(0.45, 0.45, 0.45, 0.6),
            grund=(1.0, 1.0, 1.0, 1.0),
        )

    # ------------------------------------------------------- Bauteilfarben

    @property
    def flaeche(self) -> Farbe:
        """Grundfarbe, auf der gezeichnet wird – zum deckenden Füllen."""
        return self.grund or (0.5, 0.5, 0.5, 1.0)

    @property
    def bauteil(self) -> Farbe:
        """Farbton für Nabenkörper, Flansche und Felgenprofil."""
        return self.akzent

    @property
    def metall(self) -> Farbe:
        """Neutraler Ton für Freilaufkörper, Endkappen und Stahlteile."""
        return self.text

    def getoent(self, farbe: Farbe, deckung: float) -> Farbe:
        """Dieselbe Farbe mit anderer Deckung."""
        return (farbe[0], farbe[1], farbe[2], deckung)

    def verlauf(self, farbe: Farbe, mitte_y: float, halbe_hoehe: float,
                staerke: float = 1.0):
        """Senkrechter Verlauf, der ein rundes Bauteil vortäuscht.

        Oben hell, in der Mitte dunkel, unten wieder etwas heller – so liest
        das Auge einen Zylinder statt eines flachen Kastens.
        """
        halbe_hoehe = max(halbe_hoehe, 1.0)
        strich = cairo.LinearGradient(0, mitte_y - halbe_hoehe, 0, mitte_y + halbe_hoehe)
        for stelle, deckung in ((0.0, 0.16), (0.26, 0.52), (0.55, 0.14), (1.0, 0.38)):
            strich.add_color_stop_rgba(stelle, farbe[0], farbe[1], farbe[2],
                                       deckung * staerke)
        return strich


# --------------------------------------------------------------------- Striche


def setze(ctx, farbe: Farbe, breite: float = 1.0) -> None:
    ctx.set_source_rgba(*farbe)
    ctx.set_line_width(breite)
    ctx.set_dash([])


def gestrichelt(ctx, farbe: Farbe, breite: float = 1.0, muster=(4.0, 4.0)) -> None:
    ctx.set_source_rgba(*farbe)
    ctx.set_line_width(breite)
    ctx.set_dash(list(muster))


def linie(ctx, x1: float, y1: float, x2: float, y2: float) -> None:
    ctx.move_to(x1, y1)
    ctx.line_to(x2, y2)
    ctx.stroke()


def spitze(ctx, x: float, y: float, winkel: float, groesse: float = 5.0) -> None:
    """Gefüllte Pfeilspitze bei ``(x, y)``, zeigt in Richtung ``winkel``."""
    ctx.save()
    ctx.translate(x, y)
    ctx.rotate(winkel)
    ctx.move_to(0, 0)
    ctx.line_to(-groesse, groesse * 0.4)
    ctx.line_to(-groesse, -groesse * 0.4)
    ctx.close_path()
    ctx.fill()
    ctx.restore()


# ------------------------------------------------------------------- Schrift


def text(
    ctx,
    x: float,
    y: float,
    inhalt: str,
    farbe: Farbe,
    groesse: float = 9.0,
    anker: str = "mitte",
    fett: bool = False,
    freistellen: Farbe | None = None,
) -> tuple[float, float]:
    """Zeichnet Text und liefert dessen Größe zurück.

    ``anker`` bestimmt den Bezugspunkt: ``mitte``, ``links``, ``rechts``,
    ``oben`` oder ``unten`` (jeweils waagerecht zentriert).

    ``freistellen`` legt diese Farbe hinter den Text. Nötig für Beschriftungen,
    die auf einer Mittel- oder Maßlinie liegen – sonst laufen Strich und
    Ziffern ineinander.
    """
    layout = PangoCairo.create_layout(ctx)
    beschreibung = Pango.FontDescription(f"Sans {'Bold ' if fett else ''}{groesse:g}")
    layout.set_font_description(beschreibung)
    layout.set_text(inhalt, -1)
    breite, hoehe = layout.get_pixel_size()

    versatz = {
        "mitte": (-breite / 2, -hoehe / 2),
        "links": (0.0, -hoehe / 2),
        "rechts": (-breite, -hoehe / 2),
        "oben": (-breite / 2, -hoehe),
        "unten": (-breite / 2, 0.0),
    }[anker]

    if freistellen is not None:
        luft = 2.0
        ctx.rectangle(x + versatz[0] - luft, y + versatz[1] - luft / 2,
                      breite + 2 * luft, hoehe + luft)
        ctx.set_source_rgba(*freistellen)
        ctx.fill()

    ctx.set_source_rgba(*farbe)
    ctx.move_to(x + versatz[0], y + versatz[1])
    PangoCairo.show_layout(ctx, layout)
    return breite, hoehe


# ----------------------------------------------------------------- Bemaßung


def masslinie_waagerecht(
    ctx, farben: Farben, x1: float, x2: float, y: float, beschriftung: str, oben: bool = True
) -> None:
    """Waagerechte Maßlinie mit Pfeilen an beiden Enden."""
    setze(ctx, farben.schwach, 1.0)
    linie(ctx, x1, y, x2, y)
    ctx.set_source_rgba(*farben.schwach)
    if abs(x2 - x1) > 12:
        spitze(ctx, x1, y, math.pi)
        spitze(ctx, x2, y, 0.0)
    text(ctx, (x1 + x2) / 2, y + (-6 if oben else 6), beschriftung, farben.text,
         anker="oben" if oben else "unten", freistellen=farben.grund)


def masslinie_senkrecht(
    ctx,
    farben: Farben,
    y1: float,
    y2: float,
    x: float,
    beschriftung: str,
    links: bool = False,
    beschriftung_versatz: float = 0.0,
) -> None:
    """Senkrechte Maßlinie mit Pfeilen an beiden Enden."""
    setze(ctx, farben.schwach, 1.0)
    linie(ctx, x, y1, x, y2)
    ctx.set_source_rgba(*farben.schwach)
    if abs(y2 - y1) > 12:
        spitze(ctx, x, y1, -math.pi / 2)
        spitze(ctx, x, y2, math.pi / 2)
    text(ctx, x + (-5 if links else 5), (y1 + y2) / 2 + beschriftung_versatz, beschriftung,
         farben.text, anker="rechts" if links else "links", freistellen=farben.grund)


def hilfslinie(ctx, farben: Farben, x1: float, y1: float, x2: float, y2: float) -> None:
    gestrichelt(ctx, farben.schwach, 1.0, (3.0, 3.0))
    linie(ctx, x1, y1, x2, y2)
    ctx.set_dash([])


# ------------------------------------------------------------------- Flächen


class ZeichenFlaeche(Gtk.DrawingArea):
    """Basisklasse: kümmert sich um Theme-Farben, Neuzeichnen und Export."""

    def __init__(self, mindestbreite: int = 200, mindesthoehe: int = 180) -> None:
        super().__init__()
        self.set_size_request(mindestbreite, mindesthoehe)
        self.connect("draw", self._beim_zeichnen)
        # Beim Theme-Wechsel (z. B. Umschalten auf Dunkel) neu zeichnen.
        self.connect("style-updated", lambda _w: self.queue_draw())

    def zeichne(self, ctx, breite: float, hoehe: float, farben: Farben) -> None:
        """Von den Unterklassen zu füllen."""
        raise NotImplementedError

    def _beim_zeichnen(self, _widget, ctx) -> bool:
        breite = self.get_allocated_width()
        hoehe = self.get_allocated_height()
        if breite > 4 and hoehe > 4:
            self.zeichne(ctx, breite, hoehe, Farben.vom_widget(self))
        return False

    # ------------------------------------------------------------- Export

    def exportiere(self, pfad: str | Path, breite: int = 1200, hoehe: int = 900) -> None:
        """Schreibt die Skizze als PNG, PDF oder SVG – Format nach Endung."""
        pfad = Path(pfad)
        endung = pfad.suffix.lower()
        farben = Farben.fuer_export()

        if endung == ".pdf":
            flaeche = cairo.PDFSurface(str(pfad), breite, hoehe)
        elif endung == ".svg":
            flaeche = cairo.SVGSurface(str(pfad), breite, hoehe)
        else:
            flaeche = cairo.ImageSurface(cairo.FORMAT_ARGB32, breite, hoehe)

        ctx = cairo.Context(flaeche)
        if farben.grund:
            ctx.set_source_rgba(*farben.grund)
            ctx.paint()
        self.zeichne(ctx, breite, hoehe, farben)

        if endung in (".pdf", ".svg"):
            flaeche.finish()
        else:
            flaeche.write_to_png(str(pfad))
        flaeche.flush()
