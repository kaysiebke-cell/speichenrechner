"""Auswahlleiste für Vorlagen: Klappliste mit Suche, Speichern, Löschen.

Wird zweimal benutzt – einmal für Naben, einmal für Felgen. Die Leiste kennt
weder Nabe noch Felge, sie bekommt alles über Rückruffunktionen und meldet die
Auswahl über das Signal ``gewaehlt``.

Die Liste kann neben den Vorlagen weitere Einträge führen, etwa den
Nabenkatalog. Damit auch dreistellige Listen bedienbar bleiben, ist die
Klappliste eintippbar: die Eingabe filtert mit, ganz gleich an welcher Stelle
der Suchbegriff im Namen steht.
"""

from __future__ import annotations

from typing import Callable

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GObject, Gtk  # noqa: E402

from . import widgets
from .vorlagen_dialog import name_abfragen

EIGENE_WERTE = "— eigene Werte —"


class VorlagenLeiste(Gtk.Box):
    """Eintippbare Klappliste mit Vorlagen plus Speichern und Löschen."""

    __gsignals__ = {
        "gewaehlt": (GObject.SignalFlags.RUN_FIRST, None, (object,)),
    }

    def __init__(
        self,
        titel: str,
        laden: Callable[[], list],
        speichern: Callable[[object], None],
        loeschen: Callable[[str], bool],
        ist_eigene: Callable[[str], bool],
        aktuelle_werte: Callable[[], object],
        zusatz: Callable[[], list[tuple[str, object]]] | None = None,
    ) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self._titel = titel
        self._laden = laden
        self._speichern = speichern
        self._loeschen = loeschen
        self._ist_eigene = ist_eigene
        self._aktuelle_werte = aktuelle_werte
        self._zusatz = zusatz
        self._stumm = False

        # Spalten: Anzeigetext, Objekt, ist eigene Vorlage
        self.speicher = Gtk.ListStore(str, object, bool)
        self.liste = Gtk.ComboBox.new_with_model_and_entry(self.speicher)
        self.liste.set_entry_text_column(0)
        self.liste.set_hexpand(True)
        self.liste.connect("changed", self._auswahl_geaendert)
        self._vervollstaendigung_einrichten()
        self.pack_start(self.liste, True, True, 0)

        self.knopf_speichern = widgets.knopf(
            "", "document-save-symbolic", "Aktuelle Werte als eigene Vorlage speichern"
        )
        self.knopf_speichern.connect("clicked", self._speichern_geklickt)
        self.pack_start(self.knopf_speichern, False, False, 0)

        self.knopf_loeschen = widgets.knopf("", "user-trash-symbolic", "Eigene Vorlage löschen")
        self.knopf_loeschen.connect("clicked", self._loeschen_geklickt)
        self.pack_start(self.knopf_loeschen, False, False, 0)

        self.aktualisieren()

    # ---------------------------------------------------------------- Suche

    def _vervollstaendigung_einrichten(self) -> None:
        """Tippen filtert die Liste – auch mitten im Namen."""
        self.feld = self.liste.get_child()
        self.feld.set_placeholder_text("Vorlage wählen oder Namen eintippen …")

        vervollstaendigung = Gtk.EntryCompletion()
        vervollstaendigung.set_model(self.speicher)
        vervollstaendigung.set_text_column(0)
        vervollstaendigung.set_minimum_key_length(1)
        vervollstaendigung.set_popup_completion(True)
        vervollstaendigung.set_popup_set_width(False)
        vervollstaendigung.set_match_func(self._passt, None)
        vervollstaendigung.connect("match-selected", self._treffer_gewaehlt)
        self.feld.set_completion(vervollstaendigung)

    @staticmethod
    def _passt(vervollstaendigung, schluessel, zeiger, _daten) -> bool:
        text = (vervollstaendigung.get_model()[zeiger][0] or "").lower()
        return all(wort in text for wort in schluessel.lower().split())

    def _treffer_gewaehlt(self, _vervollstaendigung, modell, zeiger) -> bool:
        self.liste.set_active_iter(modell.get_iter(modell.get_path(zeiger)))
        return True

    # ---------------------------------------------------------------- Liste

    def aktualisieren(self) -> None:
        """Lädt Vorlagen und Zusatzeinträge neu und behält die Auswahl bei."""
        vorher = self.name()
        self._stumm = True

        self.speicher.clear()
        self.speicher.append([EIGENE_WERTE, None, False])
        for eintrag in self._laden():
            self.speicher.append([eintrag.name, eintrag, self._ist_eigene(eintrag.name)])
        if self._zusatz is not None:
            for anzeige, objekt in self._zusatz():
                self.speicher.append([anzeige, objekt, False])

        self.liste.set_active(self._zeile_von(vorher))
        self._stumm = False
        self._knoepfe_pruefen()

    def _zeile_von(self, name: str | None) -> int:
        if name:
            for nummer, zeile in enumerate(self.speicher):
                if zeile[0] == name:
                    return nummer
        return 0

    def name(self) -> str | None:
        """Name des gewählten Eintrags oder ``None`` bei eigenen Werten."""
        zeile = self.liste.get_active()
        if zeile <= 0:
            return None
        return self.speicher[zeile][0]

    def waehle(self, name: str) -> None:
        """Wählt einen Eintrag über den Namen, ohne ``gewaehlt`` auszulösen."""
        self._stumm = True
        self.liste.set_active(self._zeile_von(name))
        self._stumm = False
        self._knoepfe_pruefen()

    def auf_eigene_werte(self) -> None:
        """Setzt die Auswahl auf „eigene Werte“, ohne ``gewaehlt`` auszulösen."""
        if self.liste.get_active() == 0:
            return
        self._stumm = True
        self.liste.set_active(0)
        self._stumm = False
        self._knoepfe_pruefen()

    # ------------------------------------------------------------ Reaktionen

    def _knoepfe_pruefen(self) -> None:
        zeile = self.liste.get_active()
        eigene = zeile > 0 and self.speicher[zeile][2]
        self.knopf_loeschen.set_sensitive(bool(eigene))

    def _auswahl_geaendert(self, _combo) -> None:
        self._knoepfe_pruefen()
        if self._stumm:
            return
        zeile = self.liste.get_active()
        self.emit("gewaehlt", self.speicher[zeile][1] if zeile > 0 else None)

    def _speichern_geklickt(self, _knopf) -> None:
        werte = self._aktuelle_werte()
        name = name_abfragen(self.get_toplevel(), self._titel, "Name der Vorlage:", werte.name)
        if not name:
            return
        werte.name = name
        self._speichern(werte)
        self.aktualisieren()
        self.waehle(name)

    def _loeschen_geklickt(self, _knopf) -> None:
        name = self.name()
        if name and self._loeschen(name):
            self.aktualisieren()
            self.auf_eigene_werte()
