"""Dialog für die Maße der Speiche und den Elastizitätsmodul.

Entspricht dem, was für die Dehnungsrechnung gebraucht wird: die drei
Abschnitte der Speiche und das Material. Der Querschnitt des Mittelteils wird
live mitgerechnet, weil er die Dehnung und den Ton bestimmt.
"""

from __future__ import annotations

import math

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..speiche import E_MODUL, EIGENE_VORGABE
from . import widgets


class BauartDialog(Gtk.Dialog):
    """Freie Eingabe der Speichenmaße plus E-Modul."""

    def __init__(self, eltern: Gtk.Window, werte: dict | None, e_modul: float) -> None:
        super().__init__(title="Speichenmaße", transient_for=eltern, modal=True)
        self.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        uebernehmen = self.add_button("Übernehmen", Gtk.ResponseType.OK)
        uebernehmen.get_style_context().add_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        start = dict(EIGENE_VORGABE)
        start.update(werte or {})

        inhalt = self.get_content_area()
        inhalt.set_spacing(widgets.ABSTAND)
        inhalt.set_border_width(widgets.RAND)

        erklaerung = Gtk.Label(xalign=0.0)
        erklaerung.set_line_wrap(True)
        erklaerung.set_max_width_chars(52)
        erklaerung.set_text(
            "Eine konifizierte Speiche besteht aus drei Abschnitten. Für die "
            "Dehnung zählt vor allem das dünne Mittelteil – dort steckt fast die "
            "ganze Längung."
        )
        erklaerung.get_style_context().add_class("dim-label")
        inhalt.pack_start(erklaerung, False, False, 0)

        raster = Gtk.Grid(column_spacing=widgets.ABSTAND, row_spacing=6)
        inhalt.pack_start(raster, False, False, 0)
        reihe = 0

        self.e_modul = widgets.zahlenfeld(50_000, 300_000, 5_000, 0, e_modul)
        reihe = widgets.zeile(
            raster, reihe, "E-Modul", self.e_modul, einheit="N/mm²",
            hilfe="Elastizitätsmodul des Speichendrahts. Für nichtrostenden "
                  "Speichenstahl wird mit rund 180 000 N/mm² gerechnet.",
        )

        self.laenge_kopf = widgets.zahlenfeld(0, 120, 1, 1, start["laenge_kopf"])
        self.durchmesser_kopf = widgets.zahlenfeld(0.5, 4.0, 0.1, 2, start["durchmesser_kopf"])
        reihe = widgets.doppelzeile(
            raster, reihe, "Kopfteil L / Ø",
            self.laenge_kopf, self.durchmesser_kopf,
            hilfe="Verdickter Abschnitt am Speichenkopf.",
        )

        self.laenge_unten = widgets.zahlenfeld(0, 120, 1, 1, start["laenge_unten"])
        self.durchmesser_unten = widgets.zahlenfeld(0.5, 4.0, 0.1, 2, start["durchmesser_unten"])
        reihe = widgets.doppelzeile(
            raster, reihe, "Gewindeteil L / Ø",
            self.laenge_unten, self.durchmesser_unten,
            hilfe="Verdickter Abschnitt am Gewindeende.",
        )

        self.durchmesser_mitte = widgets.zahlenfeld(0.5, 4.0, 0.1, 2, start["durchmesser_mitte"])
        reihe = widgets.zeile(
            raster, reihe, "Mittelteil Ø", self.durchmesser_mitte,
            hilfe="Dünnster Abschnitt – bestimmt Dehnung, Ton und Drahtspannung.",
        )

        self.querschnitt = Gtk.Label(xalign=0.0)
        self.querschnitt.get_style_context().add_class("dim-label")
        raster.attach(self.querschnitt, 0, reihe, 3, 1)

        self.durchmesser_mitte.connect("value-changed", lambda _f: self._vorschau())
        self._vorschau()

        self.show_all()

    def _vorschau(self) -> None:
        durchmesser = self.durchmesser_mitte.get_value()
        flaeche = math.pi / 4.0 * durchmesser**2
        self.querschnitt.set_text(
            f"Querschnittsfläche Mittelteil: {flaeche:.2f} mm²".replace(".", ",")
        )

    def werte(self) -> dict:
        return {
            "durchmesser_kopf": self.durchmesser_kopf.get_value(),
            "durchmesser_unten": self.durchmesser_unten.get_value(),
            "durchmesser_mitte": self.durchmesser_mitte.get_value(),
            "laenge_kopf": self.laenge_kopf.get_value(),
            "laenge_unten": self.laenge_unten.get_value(),
        }

    def ausfuehren(self) -> tuple[dict, float] | None:
        """Zeigt den Dialog und liefert ``(maße, e_modul)`` oder ``None``."""
        if self.run() == Gtk.ResponseType.OK:
            return self.werte(), self.e_modul.get_value()
        return None


def standard_e_modul() -> float:
    return E_MODUL
