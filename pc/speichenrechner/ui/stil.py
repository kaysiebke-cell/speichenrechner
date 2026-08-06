"""Anbindung an das Linux-Theme.

Die Anwendung bringt bewusst **kein** eigenes Farbschema mit. GTK zieht
Schriftart, Farben, Icons und Hell/Dunkel-Variante aus den Cinnamon- bzw.
GTK-Einstellungen von Linux Mint. Hier stehen nur zwei Dinge:

1. ein winziges Stylesheet, das ausschließlich Größen und Abstände setzt,
2. Helfer, die die aktuellen Theme-Farben für die Cairo-Skizze liefern.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

# Nur Typografie und Abstände – keine festen Farben, damit jedes Theme passt.
CSS = b"""
.ergebnis-zahl {
    font-size: 26px;
    font-weight: bold;
}
.ergebnis-einheit {
    font-size: 13px;
}
.ergebnis-seite {
    font-weight: bold;
    letter-spacing: 1px;
}
.klein {
    font-size: 90%;
}
"""


def stylesheet_anwenden() -> None:
    """Hängt das Stylesheet an den Bildschirm – einmal beim Start."""
    anbieter = Gtk.CssProvider()
    anbieter.load_from_data(CSS)
    bildschirm = Gdk.Screen.get_default()
    if bildschirm is not None:
        Gtk.StyleContext.add_provider_for_screen(
            bildschirm, anbieter, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


def theme_farbe(widget: Gtk.Widget, name: str, ersatz: tuple[float, float, float, float]) -> tuple:
    """Liest eine benannte Theme-Farbe als ``(r, g, b, a)``.

    Fehlt die Farbe im aktiven Theme, kommt ``ersatz`` zurück.
    """
    gefunden, farbe = widget.get_style_context().lookup_color(name)
    if not gefunden:
        return ersatz
    return (farbe.red, farbe.green, farbe.blue, farbe.alpha)


def vordergrund(widget: Gtk.Widget) -> tuple:
    """Textfarbe des aktuellen Themes."""
    farbe = widget.get_style_context().get_color(widget.get_state_flags())
    return (farbe.red, farbe.green, farbe.blue, farbe.alpha)


def akzent(widget: Gtk.Widget) -> tuple:
    """Auswahlfarbe des Themes – in Mint z. B. das eingestellte Grün/Blau."""
    return theme_farbe(widget, "theme_selected_bg_color", (0.30, 0.62, 0.42, 1.0))


def hintergrund(widget: Gtk.Widget) -> tuple:
    """Grundfarbe der Fläche, auf der gezeichnet wird.

    Nötig, um Bauteile **deckend** zu füllen: sonst scheint die Achse durch
    den Nabenkörper hindurch. Fehlt die Themefarbe, wird aus der Textfarbe
    geschlossen, ob es ein helles oder ein dunkles Theme ist.
    """
    farbe = theme_farbe(widget, "theme_bg_color", (0.0, 0.0, 0.0, 0.0))
    if farbe[3] > 0.0:
        return (farbe[0], farbe[1], farbe[2], 1.0)
    text = vordergrund(widget)
    dunkles_theme = (text[0] + text[1] + text[2]) / 3.0 > 0.5
    return (0.16, 0.17, 0.18, 1.0) if dunkles_theme else (0.98, 0.98, 0.98, 1.0)
