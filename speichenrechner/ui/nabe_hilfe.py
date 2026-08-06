"""Dialog: Flanschabstände aus Einbaubreite und Messung ab Kontermutter.

An der Nabe lässt sich der Abstand ab Nabenmitte schlecht messen. Einfacher
ist der Weg von außen: Einbaubreite (Achsmaß zwischen den Ausfallenden) und
je Seite der Abstand von der Außenkante bis zur Flanschmitte.

Derselbe Weg führt Werte aus fremden Nabendatenbanken herein. Was dort
„flange offset“ heißt, ist meist **ab Kontermutter** gemessen, nicht ab der
Nabenmitte – spokelengthcalculator.com nennt es „the distance from the lock
nut to the centre of the flange“ und rechnet ``flange offset = OLD/2 - Wl``.
Solche Werte gehören in diesen Dialog. Trägt man sie direkt als
Flanschabstand ein, kommt eine falsche Speichenlänge heraus, ohne dass etwas
auffällt: bei einer Hope Pro 4 (135 mm) stünde dann 34,5/48,5 statt 33,0/19,0.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..berechnung import flanschabstand_aus_einbaubreite
from . import widgets


class NabenmassDialog(Gtk.Dialog):
    """Rechnet Messungen ab Kontermutter in Abstände ab Nabenmitte um."""

    def __init__(self, eltern: Gtk.Window, einbaubreite: float | None = None) -> None:
        super().__init__(title="Flanschabstand aus Einbaubreite", transient_for=eltern, modal=True)
        self.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        uebernehmen = self.add_button("Übernehmen", Gtk.ResponseType.OK)
        uebernehmen.get_style_context().add_class("suggested-action")
        self.set_default_response(Gtk.ResponseType.OK)

        inhalt = self.get_content_area()
        inhalt.set_spacing(widgets.ABSTAND)
        inhalt.set_border_width(widgets.RAND)

        erklaerung = Gtk.Label(xalign=0.0)
        erklaerung.set_line_wrap(True)
        erklaerung.set_max_width_chars(46)
        erklaerung.set_text(
            "Einbaubreite ist das Achsmaß zwischen den Ausfallenden. "
            "Die Flanschmaße werden jeweils von der Außenkante der "
            "Kontermutter bzw. Endkappe bis zur Mitte des Flansches gemessen.\n\n"
            "Hier gehören auch Werte aus fremden Nabendatenbanken hinein: was "
            "dort „flange offset“ heißt, ist meist ab Kontermutter gemessen, "
            "nicht ab der Nabenmitte."
        )
        erklaerung.get_style_context().add_class("dim-label")
        inhalt.pack_start(erklaerung, False, False, 0)

        raster = Gtk.Grid(column_spacing=widgets.ABSTAND, row_spacing=6)
        inhalt.pack_start(raster, False, False, 0)
        reihe = 0

        self.einbaubreite = widgets.zahlenfeld(50, 250, 0.5, 1, einbaubreite or 135.0)
        reihe = widgets.zeile(raster, reihe, "Einbaubreite", self.einbaubreite)

        reihe = widgets.spaltenkoepfe(raster, reihe)

        self.aussen_links = widgets.zahlenfeld(0, 150, 0.5, 1, 30.5)
        self.aussen_rechts = widgets.zahlenfeld(0, 150, 0.5, 1, 48.5)
        reihe = widgets.doppelzeile(
            raster, reihe, "Außen bis Flansch", self.aussen_links, self.aussen_rechts
        )

        self.vorschau = Gtk.Label(xalign=0.0)
        inhalt.pack_start(self.vorschau, False, False, 0)

        for feld in (self.einbaubreite, self.aussen_links, self.aussen_rechts):
            feld.connect("value-changed", lambda _f: self._vorschau_aktualisieren())
        self._vorschau_aktualisieren()

        self.show_all()

    def _werte(self) -> tuple[float, float]:
        return flanschabstand_aus_einbaubreite(
            self.einbaubreite.get_value(),
            self.aussen_links.get_value(),
            self.aussen_rechts.get_value(),
        )

    def _vorschau_aktualisieren(self) -> None:
        links, rechts = self._werte()
        self.vorschau.set_markup(
            f"Ab Nabenmitte:  <b>links {links:.1f} mm</b>   ·   <b>rechts {rechts:.1f} mm</b>"
        )

    def ausfuehren(self) -> tuple[float, float] | None:
        """Zeigt den Dialog und liefert ``(links, rechts)`` oder ``None``."""
        if self.run() == Gtk.ResponseType.OK:
            return self._werte()
        return None
