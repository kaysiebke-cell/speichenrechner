"""Kleine Bau-Helfer, damit die Formulare kurz und einheitlich bleiben."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

RAND = 12
ABSTAND = 8


def rahmen(titel: str, aktion: Gtk.Widget | None = None) -> Gtk.Frame:
    """Leerer Rahmen mit fetter Überschrift und optionaler Schaltfläche.

    Die Schaltfläche sitzt direkt neben der Überschrift – dort, wo sie zum
    Abschnitt gehört, statt in einem Menü.
    """
    kasten = Gtk.Frame()
    beschriftung = Gtk.Label()
    beschriftung.set_markup(f"<b>{titel}</b>")

    if aktion is None:
        kasten.set_label_widget(beschriftung)
    else:
        kopf = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        kopf.pack_start(beschriftung, False, False, 0)
        kopf.pack_start(aktion, False, False, 0)
        kasten.set_label_widget(kopf)

    kasten.set_label_align(0.02, 0.5)
    return kasten


def abschnitt(titel: str, aktion: Gtk.Widget | None = None) -> tuple[Gtk.Frame, Gtk.Grid]:
    """Rahmen mit fetter Überschrift und darin ein vorbereitetes Raster."""
    rahmen_ = rahmen(titel, aktion)

    raster = Gtk.Grid(column_spacing=ABSTAND, row_spacing=6)
    raster.set_border_width(RAND)
    rahmen_.add(raster)
    return rahmen_, raster


def zahlenfeld(
    minimum: float,
    maximum: float,
    schritt: float = 0.5,
    stellen: int = 1,
    wert: float = 0.0,
) -> Gtk.SpinButton:
    """Zahleneingabe mit Pfeiltasten; übernimmt das Theme automatisch."""
    feld = Gtk.SpinButton()
    feld.set_adjustment(Gtk.Adjustment(value=wert, lower=minimum, upper=maximum,
                                       step_increment=schritt, page_increment=schritt * 10))
    feld.set_digits(stellen)
    feld.set_numeric(True)
    feld.set_width_chars(5)
    feld.set_halign(Gtk.Align.START)
    return feld


def zeile(
    raster: Gtk.Grid,
    reihe: int,
    beschriftung: str,
    steuerelement: Gtk.Widget,
    einheit: str | None = "mm",
    hilfe: str | None = None,
) -> int:
    """Setzt ``Label | Feld | Einheit`` in eine Rasterzeile und zählt weiter."""
    label = Gtk.Label(label=beschriftung, xalign=0.0)
    if hilfe:
        label.set_tooltip_text(hilfe)
        steuerelement.set_tooltip_text(hilfe)
    raster.attach(label, 0, reihe, 1, 1)
    raster.attach(steuerelement, 1, reihe, 1, 1)
    if einheit:
        einheit_label = Gtk.Label(label=einheit, xalign=0.0)
        einheit_label.get_style_context().add_class("dim-label")
        raster.attach(einheit_label, 2, reihe, 1, 1)
    return reihe + 1


def doppelzeile(
    raster: Gtk.Grid,
    reihe: int,
    beschriftung: str,
    links: Gtk.Widget,
    rechts: Gtk.Widget,
    einheit: str | None = "mm",
    hilfe: str | None = None,
) -> int:
    """Wie :func:`zeile`, aber mit je einem Feld für links und rechts."""
    label = Gtk.Label(label=beschriftung, xalign=0.0)
    if hilfe:
        label.set_tooltip_text(hilfe)
    raster.attach(label, 0, reihe, 1, 1)

    kasten = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    kasten.pack_start(links, False, False, 0)
    kasten.pack_start(rechts, False, False, 0)
    raster.attach(kasten, 1, reihe, 1, 1)

    if einheit:
        einheit_label = Gtk.Label(label=einheit, xalign=0.0)
        einheit_label.get_style_context().add_class("dim-label")
        raster.attach(einheit_label, 2, reihe, 1, 1)
    return reihe + 1


def spaltenkoepfe(raster: Gtk.Grid, reihe: int) -> int:
    """Ueberschriften ``links | rechts`` ueber den Doppelzeilen."""
    kasten = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    for text in ("links", "rechts"):
        label = Gtk.Label(label=text, xalign=0.0)
        label.get_style_context().add_class("dim-label")
        label.set_width_chars(7)
        kasten.pack_start(label, False, False, 0)
    raster.attach(kasten, 1, reihe, 1, 1)
    return reihe + 1


def flachknopf(icon: str, tooltip: str) -> Gtk.Button:
    """Kleine, randlose Schaltfläche – für Überschriften-Zeilen."""
    schalter = Gtk.Button()
    schalter.set_relief(Gtk.ReliefStyle.NONE)
    schalter.set_focus_on_click(False)
    schalter.add(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.MENU))
    schalter.set_tooltip_text(tooltip)
    return schalter


def knopf(beschriftung: str, icon: str | None = None, tooltip: str | None = None) -> Gtk.Button:
    """Schaltfläche mit optionalem Theme-Icon."""
    schalter = Gtk.Button()
    inhalt = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    if icon:
        inhalt.pack_start(Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON), False, False, 0)
    if beschriftung:
        inhalt.pack_start(Gtk.Label(label=beschriftung), False, False, 0)
    schalter.add(inhalt)
    if tooltip:
        schalter.set_tooltip_text(tooltip)
    return schalter
