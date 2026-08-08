"""Reiter „Messen": Vereinfachte Textansicht der Messdaten.

Nur noch Text, keine grafischen Darstellungen mehr.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..formatierung import mm
from ..modelle import Felge, Nabe
from . import widgets


class MessAnsicht(Gtk.Box):
    """Vereinfachte Messdaten-Ansicht ohne Grafiken."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(widgets.RAND)

        self.text_bereich = Gtk.Label(xalign=0.0)
        self.text_bereich.set_line_wrap(True)
        self.text_bereich.set_width_chars(30)
        self.pack_start(self.text_bereich, False, False, 0)

    def setze_daten(self, nabe: Nabe, felge: Felge) -> None:
        text = (
            f"Flanschabstand links: {mm(nabe.flanschabstand_links)}\n"
            f"Flanschabstand rechts: {mm(nabe.flanschabstand_rechts)}\n"
            f"Flansch-Ø links: {mm(nabe.flanschdurchmesser_links)}\n"
            f"Flansch-Ø rechts: {mm(nabe.flanschdurchmesser_rechts)}\n"
            f"\n"
            f"ERD (Felgendurchmesser): {mm(felge.erd)}\n"
            f"Versatz: {mm(felge.versatz)}"
        )
        self.text_bereich.set_text(text)

    def zeige(self, schluessel: str) -> None:
        """Keine interaktive Ansichtsumschaltung mehr nötig."""
        pass

    def aktuelles_bild(self):
        """Gibt None zurück, da keine Skizze zum Exportieren vorhanden ist."""
        return None
