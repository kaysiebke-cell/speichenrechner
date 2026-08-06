"""Fenster „Nabentabelle“ – die Herstellertabelle zum Nachtragen.

Zeigt den Katalog als Tabelle mit denselben Spalten wie die Excel-Vorlage.
Zellen lassen sich anklicken und ändern; gespeichert wird **nicht** in die
Tabellendatei, sondern als Nachtrag in
``~/.config/speichenrechner/naben_ergaenzungen.json``.

Damit bleibt die Tabelle die Quelle: wird sie erweitert und der Katalog neu
erzeugt, gehen die hier eingetragenen Werte nicht verloren. Über „Als CSV
sichern“ lassen sie sich in die Tabelle zurückholen.
"""

from __future__ import annotations

import csv

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango  # noqa: E402

from .. import katalog as nabenkatalog
from . import widgets
from .vorlagen_dialog import name_abfragen

#: Feste Spalten vorne, danach die änderbaren aus dem Katalog.
KOPFSPALTEN = ("Hersteller", "Art", "Modell")


class TabellenFenster(Gtk.Dialog):
    """Die Herstellertabelle als bearbeitbare Liste."""

    def __init__(self, eltern: Gtk.Window) -> None:
        super().__init__(title="Nabentabelle", transient_for=eltern, modal=True)
        self.add_button("Schließen", Gtk.ResponseType.CLOSE)
        self.set_default_size(1080, 620)

        self._ergaenzungen = nabenkatalog.lade_ergaenzungen()
        self._geaendert = False
        self._filter_art = ""
        self._filter_hersteller = ""

        inhalt = self.get_content_area()
        inhalt.set_spacing(widgets.ABSTAND)
        inhalt.set_border_width(widgets.RAND)

        inhalt.pack_start(self._baue_kopfzeile(), False, False, 0)
        inhalt.pack_start(self._baue_tabelle(), True, True, 0)
        inhalt.pack_start(self._baue_fuss(), False, False, 0)

        self._fuellen()
        self.show_all()

    # ------------------------------------------------------------------ Aufbau

    def _baue_kopfzeile(self) -> Gtk.Widget:
        zeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=widgets.ABSTAND)

        self.suche = Gtk.SearchEntry()
        self.suche.set_placeholder_text("Modell, Achstyp, Bremse … suchen")
        self.suche.connect("search-changed", lambda _w: self._fuellen())
        zeile.pack_start(self.suche, True, True, 0)

        katalog = nabenkatalog.lade()

        self.art = Gtk.ComboBoxText()
        self.art.append("", "alle Arten")
        for name in katalog.arten():
            self.art.append(name, name)
        self.art.set_active_id("")
        self.art.connect("changed", self._art_geaendert)
        zeile.pack_start(self.art, False, False, 0)

        self.hersteller = Gtk.ComboBoxText()
        self._hersteller_fuellen()
        self.hersteller.connect("changed", self._hersteller_geaendert)
        zeile.pack_start(self.hersteller, False, False, 0)

        self.nur_offene = Gtk.CheckButton(label="nur ohne Flanschmaße")
        self.nur_offene.set_tooltip_text(
            "Zeigt die Naben, bei denen zum Rechnen noch etwas fehlt."
        )
        self.nur_offene.connect("toggled", lambda _w: self._fuellen())
        zeile.pack_start(self.nur_offene, False, False, 0)

        return zeile

    def _baue_tabelle(self) -> Gtk.Widget:
        # Spalten: Hersteller, Art, Modell, dann die änderbaren Felder, zuletzt
        # der Schlüssel und die Kennzeichnung „nachgetragen“.
        typen = [str] * (len(KOPFSPALTEN) + len(nabenkatalog.SPALTEN)) + [str, bool]
        self.speicher = Gtk.ListStore(*typen)

        self.liste = Gtk.TreeView(model=self.speicher)
        self.liste.set_enable_search(False)

        for nummer, titel in enumerate(KOPFSPALTEN):
            zelle = Gtk.CellRendererText()
            zelle.set_property("ellipsize", Pango.EllipsizeMode.END)
            spalte = Gtk.TreeViewColumn(titel, zelle, text=nummer)
            spalte.set_resizable(True)
            spalte.set_sort_column_id(nummer)
            spalte.set_min_width(200 if titel == "Modell" else 105)
            if titel == "Modell":
                spalte.set_expand(True)
            self.liste.append_column(spalte)

        for versatz, (feld, titel) in enumerate(nabenkatalog.SPALTEN):
            nummer = len(KOPFSPALTEN) + versatz
            zelle = Gtk.CellRendererText()
            zelle.set_property("editable", True)
            zelle.set_property("ellipsize", Pango.EllipsizeMode.END)
            zelle.connect("edited", self._zelle_geaendert, nummer, feld)
            spalte = Gtk.TreeViewColumn(titel, zelle, text=nummer)
            spalte.set_resizable(True)
            spalte.set_min_width(110)
            self.liste.append_column(spalte)

        rollbar = Gtk.ScrolledWindow()
        rollbar.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rollbar.add(self.liste)
        return rollbar

    def _baue_fuss(self) -> Gtk.Widget:
        zeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=widgets.ABSTAND)

        self.stand = Gtk.Label(xalign=0.0)
        self.stand.set_line_wrap(True)
        self.stand.get_style_context().add_class("dim-label")
        self.stand.get_style_context().add_class("klein")
        zeile.pack_start(self.stand, True, True, 0)

        neu_knopf = widgets.knopf(
            "Nabe hinzufügen …", "list-add-symbolic",
            "Eine Nabe anlegen, die in der Herstellertabelle fehlt",
        )
        neu_knopf.connect("clicked", lambda _k: self._nabe_anlegen())
        zeile.pack_start(neu_knopf, False, False, 0)

        csv_knopf = widgets.knopf(
            "Als CSV sichern …", "document-save-as-symbolic",
            "Die Tabelle als CSV ablegen, um sie in die Excel-Datei zurückzuholen",
        )
        csv_knopf.connect("clicked", lambda _k: self._csv_sichern())
        zeile.pack_start(csv_knopf, False, False, 0)

        zurueck = widgets.knopf(
            "Nachträge verwerfen", "edit-undo-symbolic",
            "Setzt alle hier eingetragenen Werte zurück auf den Stand der Tabelle",
        )
        zurueck.connect("clicked", lambda _k: self._verwerfen())
        zeile.pack_start(zurueck, False, False, 0)

        return zeile

    # ------------------------------------------------------------- Reaktionen

    def _hersteller_fuellen(self) -> None:
        self.hersteller.remove_all()
        self.hersteller.append("", "alle Hersteller")
        namen = nabenkatalog.lade().hersteller(self._filter_art)
        for name in namen:
            self.hersteller.append(name, name)
        if self._filter_hersteller not in namen:
            self._filter_hersteller = ""
        self.hersteller.set_active_id(self._filter_hersteller)

    def _art_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        self._filter_art = combo.get_active_id() or ""
        self._hersteller_fuellen()
        self._fuellen()

    def _hersteller_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        self._filter_hersteller = combo.get_active_id() or ""
        self._fuellen()

    def _fuellen(self) -> None:
        katalog = nabenkatalog.lade()
        treffer = katalog.suche(
            self.suche.get_text(), self._filter_hersteller, self._filter_art
        )
        if self.nur_offene.get_active():
            treffer = [e for e in treffer if not e.hat_flanschmasse]

        self.speicher.clear()
        for eintrag in treffer:
            zeile = [eintrag.hersteller, eintrag.art, eintrag.modell]
            zeile += [getattr(eintrag, feld) for feld, _ in nabenkatalog.SPALTEN]
            zeile += [eintrag.schluessel, eintrag.ergaenzt]
            self.speicher.append(zeile)

        fertig = sum(1 for e in katalog.naben if e.hat_flanschmasse)
        selbst = sum(1 for e in katalog.naben if e.selbst_angelegt)
        self.stand.set_text(
            f"{len(treffer)} von {len(katalog.naben)} Naben angezeigt · "
            f"{fertig} rechenfertig · {len(self._ergaenzungen)} nachgetragen"
            + (f", davon {selbst} selbst angelegt" if selbst else "") + ". "
            "Änderungen wirken sofort und bleiben erhalten, auch wenn der Katalog "
            "aus der Tabelle neu erzeugt wird."
        )

    def _zelle_geaendert(self, _zelle, pfad, text, nummer: int, feld: str) -> None:
        """Übernimmt eine geänderte Zelle und merkt sie als Nachtrag."""
        zeiger = self.speicher.get_iter(pfad)
        text = text.strip()
        if self.speicher[zeiger][nummer] == text:
            return

        self.speicher[zeiger][nummer] = text
        schluessel = self.speicher[zeiger][len(KOPFSPALTEN) + len(nabenkatalog.SPALTEN)]
        self._ergaenzungen.setdefault(schluessel, {})[feld] = text

        nabenkatalog.speichere_ergaenzungen(self._ergaenzungen)
        self._geaendert = True
        self._fuellen()

    def _nabe_anlegen(self) -> None:
        """Legt eine Nabe an, die in der Tabelle fehlt – etwa eine ältere
        Shimano-Nabe mit Schraubkranz."""
        katalog = nabenkatalog.lade()

        dialog = Gtk.Dialog(title="Nabe hinzufügen", transient_for=self, modal=True)
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        knopf = dialog.add_button("Anlegen", Gtk.ResponseType.OK)
        knopf.get_style_context().add_class("suggested-action")
        dialog.set_default_response(Gtk.ResponseType.OK)

        inhalt = dialog.get_content_area()
        inhalt.set_spacing(widgets.ABSTAND)
        inhalt.set_border_width(widgets.RAND)

        raster = Gtk.Grid(column_spacing=widgets.ABSTAND, row_spacing=6)
        inhalt.pack_start(raster, False, False, 0)

        hersteller = Gtk.ComboBoxText.new_with_entry()
        for name in katalog.hersteller():
            hersteller.append_text(name)
        hersteller.get_child().set_text(self._filter_hersteller)
        hersteller.set_hexpand(True)

        modell = Gtk.Entry()
        modell.set_activates_default(True)
        modell.set_width_chars(30)

        art = Gtk.ComboBoxText()
        for name in katalog.arten():
            art.append(name, name)
        art.set_active_id(self._filter_art or "Hinterrad")

        for reihe, (titel, feld) in enumerate(
            (("Hersteller", hersteller), ("Modell", modell), ("Bauart", art))
        ):
            raster.attach(Gtk.Label(label=titel, xalign=0.0), 0, reihe, 1, 1)
            raster.attach(feld, 1, reihe, 1, 1)

        hinweis = Gtk.Label(xalign=0.0)
        hinweis.set_line_wrap(True)
        hinweis.set_max_width_chars(48)
        hinweis.set_text(
            "Die übrigen Angaben trägst du danach in der Tabelle nach. Die Nabe "
            "liegt bei deinen Nachträgen und bleibt erhalten, auch wenn der "
            "Katalog aus der Tabelle neu erzeugt wird."
        )
        hinweis.get_style_context().add_class("dim-label")
        hinweis.get_style_context().add_class("klein")
        inhalt.pack_start(hinweis, False, False, 0)

        dialog.show_all()
        antwort = dialog.run()
        name_hersteller = hersteller.get_child().get_text().strip()
        name_modell = modell.get_text().strip()
        name_art = art.get_active_id() or "Hinterrad"
        dialog.destroy()

        if antwort != Gtk.ResponseType.OK or not name_hersteller or not name_modell:
            return

        schluessel = f"{name_hersteller}|{name_modell}"
        if any(e.schluessel == schluessel for e in katalog.naben):
            meldung = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text=f"{name_hersteller} {name_modell} steht schon im Katalog.",
            )
            meldung.run()
            meldung.destroy()
            return

        self._ergaenzungen[schluessel] = {
            "hersteller": name_hersteller,
            "modell": name_modell,
            "art": name_art,
        }
        nabenkatalog.speichere_ergaenzungen(self._ergaenzungen)
        self._geaendert = True

        # Neu angelegte Nabe gleich zeigen und die Filter dafür lösen.
        self.suche.set_text(name_modell)
        self.art.set_active_id("")
        self.hersteller.set_active_id("")
        self._fuellen()

    def _verwerfen(self) -> None:
        if not self._ergaenzungen:
            return
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"{len(self._ergaenzungen)} Nachträge verwerfen?",
        )
        dialog.format_secondary_text(
            "Die Werte aus der Herstellertabelle bleiben erhalten – nur was hier "
            "eingetragen wurde, geht verloren."
        )
        antwort = dialog.run()
        dialog.destroy()
        if antwort != Gtk.ResponseType.OK:
            return

        self._ergaenzungen = {}
        nabenkatalog.speichere_ergaenzungen({})
        self._geaendert = True
        self._fuellen()

    def _csv_sichern(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Tabelle als CSV sichern", transient_for=self,
            action=Gtk.FileChooserAction.SAVE,
        )
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        knopf = dialog.add_button("Sichern", Gtk.ResponseType.OK)
        knopf.get_style_context().add_class("suggested-action")
        dialog.set_current_name("nabentabelle.csv")
        dialog.set_do_overwrite_confirmation(True)

        if dialog.run() != Gtk.ResponseType.OK:
            dialog.destroy()
            return
        pfad = dialog.get_filename()
        dialog.destroy()

        kopf = list(KOPFSPALTEN) + [titel for _, titel in nabenkatalog.SPALTEN]
        try:
            with open(pfad, "w", encoding="utf-8-sig", newline="") as datei:
                schreiber = csv.writer(datei, delimiter=";")
                schreiber.writerow(kopf)
                for eintrag in nabenkatalog.lade().suche():
                    schreiber.writerow(
                        [eintrag.hersteller, eintrag.art, eintrag.modell]
                        + [getattr(eintrag, feld) for feld, _ in nabenkatalog.SPALTEN]
                    )
        except OSError as fehler:
            meldung = Gtk.MessageDialog(
                transient_for=self, modal=True, message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK, text=f"Konnte nicht sichern: {fehler}",
            )
            meldung.run()
            meldung.destroy()

    def ausfuehren(self) -> bool:
        """Zeigt das Fenster; liefert True, wenn etwas geändert wurde."""
        self.run()
        return self._geaendert
