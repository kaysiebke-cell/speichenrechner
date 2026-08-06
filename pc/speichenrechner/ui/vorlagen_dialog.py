"""Kleiner Dialog zum Abfragen eines Vorlagennamens."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from . import widgets


def name_abfragen(
    eltern: Gtk.Window, titel: str, beschriftung: str, vorschlag: str = ""
) -> str | None:
    """Fragt einen Namen ab. Gibt ``None`` zurück, wenn abgebrochen wurde."""
    dialog = Gtk.Dialog(title=titel, transient_for=eltern, modal=True)
    dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
    speichern = dialog.add_button("Speichern", Gtk.ResponseType.OK)
    speichern.get_style_context().add_class("suggested-action")
    dialog.set_default_response(Gtk.ResponseType.OK)

    inhalt = dialog.get_content_area()
    inhalt.set_spacing(widgets.ABSTAND)
    inhalt.set_border_width(widgets.RAND)

    inhalt.pack_start(Gtk.Label(label=beschriftung, xalign=0.0), False, False, 0)

    feld = Gtk.Entry()
    feld.set_text("" if vorschlag.startswith("Eigene ") else vorschlag)
    feld.set_activates_default(True)
    feld.set_width_chars(34)
    inhalt.pack_start(feld, False, False, 0)

    dialog.show_all()
    antwort = dialog.run()
    name = feld.get_text().strip()
    dialog.destroy()

    if antwort == Gtk.ResponseType.OK and name:
        return name
    return None
