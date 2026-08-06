"""Vergleichstabelle: was ändert eine andere Kreuzungszahl?

Zeigt für 0- bis 4-fach gekreuzt die Speichenlängen und Speichenwinkel beider
Seiten. Die gerade eingestellte Zeile ist hervorgehoben, geometrisch unmögliche
Varianten sind ausgegraut.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..berechnung import kreuzungsvergleich, uebliche_kreuzungen
from ..formatierung import grad, zahl
from ..modelle import Einspeichung, Felge, Nabe, Speichensatz
from . import widgets

SPALTEN = ("Kreuzung", "links", "rechts", "Winkel l.", "Winkel r.")


class Kreuzungsvergleich(Gtk.Box):
    """Tabelle mit einer Zeile je Kreuzungszahl."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)
        self.set_border_width(widgets.RAND)

        self.raster = Gtk.Grid(column_spacing=widgets.ABSTAND, row_spacing=4)
        self.raster.set_column_homogeneous(True)
        self.pack_start(self.raster, False, False, 0)

        self.fussnote = Gtk.Label(xalign=0.0)
        self.fussnote.set_line_wrap(True)
        self.fussnote.set_width_chars(22)
        self.fussnote.set_max_width_chars(48)
        self.fussnote.get_style_context().add_class("dim-label")
        self.fussnote.get_style_context().add_class("klein")
        self.pack_start(self.fussnote, False, False, 0)

    def zeige(
        self,
        nabe: Nabe,
        felge: Felge,
        einspeichung: Einspeichung,
        schritt: float,
        speichen: Speichensatz | None = None,
    ) -> None:
        for kind in self.raster.get_children():
            kind.destroy()

        for spalte, titel in enumerate(SPALTEN):
            kopf = Gtk.Label(label=titel, xalign=0.5 if spalte else 0.0)
            kopf.get_style_context().add_class("dim-label")
            kopf.get_style_context().add_class("klein")
            self.raster.attach(kopf, spalte, 0, 1, 1)

        aktuell = einspeichung.kreuzungen_links
        gekoppelt = einspeichung.kreuzungen_links == einspeichung.kreuzungen_rechts

        for zeile, (kreuzungen, ergebnis) in enumerate(
            kreuzungsvergleich(nabe, felge, einspeichung, schritt, speichen=speichen), start=1
        ):
            moeglich = (
                ergebnis.links.sehnenwinkel < 180.0 and ergebnis.rechts.sehnenwinkel < 180.0
            )
            ist_aktuell = gekoppelt and kreuzungen == aktuell

            werte = (
                "radial" if kreuzungen == 0 else f"{kreuzungen}-fach",
                zahl(ergebnis.links.laenge_gerundet) if moeglich else "–",
                zahl(ergebnis.rechts.laenge_gerundet) if moeglich else "–",
                grad(ergebnis.links.speichenwinkel) if moeglich else "–",
                grad(ergebnis.rechts.speichenwinkel) if moeglich else "–",
            )

            for spalte, inhalt in enumerate(werte):
                label = Gtk.Label(xalign=0.5 if spalte else 0.0)
                if ist_aktuell:
                    label.set_markup(f"<b>{inhalt}</b>")
                else:
                    label.set_text(inhalt)
                if not moeglich:
                    label.get_style_context().add_class("dim-label")
                self.raster.attach(label, spalte, zeile, 1, 1)

        self.raster.show_all()

        empfohlen_links = uebliche_kreuzungen(einspeichung.speichen_links)
        empfohlen_rechts = uebliche_kreuzungen(einspeichung.speichen_rechts)
        empfehlung = (
            f"{empfohlen_links}-fach"
            if empfohlen_links == empfohlen_rechts
            else f"links {empfohlen_links}-fach, rechts {empfohlen_rechts}-fach"
        )
        self.fussnote.set_text(
            f"Längen in mm, gerundet. Gängig ist bei dieser Speichenzahl {empfehlung}. "
            "Mehr Kreuzungen heißt längere Speichen, flacherer Auslauf am Flansch und "
            "mehr Reserve gegen Antriebs- und Bremsmomente; weniger Kreuzungen heißt "
            "steiferes, aber empfindlicheres Laufrad."
        )
