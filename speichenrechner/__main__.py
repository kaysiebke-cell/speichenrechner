"""Start über ``python3 -m speichenrechner``.

``--pruefen`` startet keine Oberfläche, sondern meldet, ob alles vorhanden ist –
nützlich, wenn beim Klick auf das Icon scheinbar nichts passiert.
"""

from __future__ import annotations

import sys

HINWEIS_GTK = (
    "PyGObject fehlt. Unter Linux Mint installieren mit:\n"
    "  sudo apt install python3-gi gir1.2-gtk-3.0"
)


def pruefen() -> int:
    """Prüft Abhängigkeiten und Ablageorte und schreibt einen Bericht."""
    from . import APP_ID, APP_NAME, VERSION
    from .pfade import icon_pfad, konfig_verzeichnis

    print(f"{APP_NAME} {VERSION}")
    print(f"Python           {sys.version.split()[0]}")

    fehler = 0

    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        print(f"GTK              {Gtk.get_major_version()}.{Gtk.get_minor_version()} – vorhanden")
    except Exception as ausnahme:
        print(f"GTK              FEHLT ({ausnahme})")
        print(HINWEIS_GTK)
        fehler += 1

    try:
        import cairo

        print(f"pycairo          {cairo.version} – vorhanden")
    except ImportError:
        print("pycairo          FEHLT – nötig für die Skizzen")
        print("  sudo apt install python3-cairo")
        fehler += 1

    from .berechnung import berechne
    from .modelle import Einspeichung, Felge, Nabe

    probe = berechne(Nabe(), Felge(), Einspeichung())
    print(f"Testrechnung     {probe.links.laenge_gerundet:.1f} mm / "
          f"{probe.rechts.laenge_gerundet:.1f} mm – in Ordnung")

    print(f"Einstellungen    {konfig_verzeichnis()}")
    print(f"Icon             {icon_pfad()} "
          f"({'vorhanden' if icon_pfad().exists() else 'FEHLT'})")

    import os

    anzeige = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
    print(f"Bildschirm       {anzeige or 'KEINER – ohne Grafik kein Fenster'}")
    if not anzeige:
        fehler += 1

    print()
    print(f"Anwendungs-Kennung {APP_ID}")
    print("Läuft bereits eine Instanz, holt ein zweiter Start nur deren Fenster")
    print("nach vorn. Prüfen mit:  pgrep -af speichenrechner.py")

    print()
    print("Alles in Ordnung." if fehler == 0 else f"{fehler} Problem(e) gefunden.")
    return 0 if fehler == 0 else 1


def main() -> int:
    if "--pruefen" in sys.argv or "--check" in sys.argv:
        return pruefen()

    try:
        import gi  # noqa: F401
    except ImportError:
        print(HINWEIS_GTK, file=sys.stderr)
        return 1

    from .ui.anwendung import starte

    return starte()


if __name__ == "__main__":
    sys.exit(main())
