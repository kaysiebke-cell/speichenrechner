"""Gtk.Application – Einstiegspunkt der Oberfläche."""

from __future__ import annotations

import traceback

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gio, Gtk  # noqa: E402

from .. import APP_ID, APP_NAME
from .hauptfenster import Hauptfenster
from .stil import stylesheet_anwenden


class Speichenrechner(Gtk.Application):
    """Hält genau ein Fenster; das Theme kommt komplett vom System."""

    def __init__(self) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.fenster: Hauptfenster | None = None

    def do_startup(self) -> None:
        Gtk.Application.do_startup(self)
        Gtk.Window.set_default_icon_name(APP_ID)
        stylesheet_anwenden()

    def do_activate(self) -> None:
        if self.fenster is None:
            try:
                self.fenster = Hauptfenster(self)
            except Exception:
                self._startfehler(traceback.format_exc())
                return
            self.fenster.show_all()
            self.fenster.neu_berechnen()

        # Läuft schon eine Instanz, holt ein zweiter Aufruf nur dieses Fenster
        # nach vorn – auch wenn es minimiert oder auf einer anderen
        # Arbeitsfläche liegt.
        self.fenster.deiconify()
        self.fenster.present_with_time(Gdk.CURRENT_TIME)

    def _startfehler(self, meldung: str) -> None:
        """Zeigt einen Fehler beim Aufbau des Fensters, statt still zu enden."""
        print(meldung, flush=True)
        dialog = Gtk.MessageDialog(
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=f"{APP_NAME} konnte nicht starten.",
        )
        dialog.format_secondary_text(meldung.strip().splitlines()[-1])
        dialog.run()
        dialog.destroy()
        self.quit()


def starte() -> int:
    """Startet die Anwendung und liefert den Rückgabewert für ``sys.exit``."""
    import sys

    from gi.repository import GLib

    GLib.set_application_name(APP_NAME)
    GLib.set_prgname(APP_ID)
    return Speichenrechner().run(sys.argv)
