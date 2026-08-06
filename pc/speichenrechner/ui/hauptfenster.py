"""Hauptfenster: verbindet Eingabe, Berechnung und Ergebnisanzeige."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from .. import APP_NAME, VERSION, bericht, berechnung, einstellungen
from ..pfade import icon_pfad
from . import widgets
from .eingabe import EingabeBereich
from .ergebnis import ErgebnisBereich
from .tabellen_fenster import TabellenFenster


class Hauptfenster(Gtk.ApplicationWindow):
    """Fenster mit Kopfleiste, Eingabespalte und Ergebnisspalte."""

    def __init__(self, anwendung: Gtk.Application) -> None:
        super().__init__(application=anwendung, title=APP_NAME)
        # Maße so, dass beim Start beide Spalten vollständig zu sehen sind:
        # links der Reiter „Laufrad“ bis zur Rundung, rechts die Ergebnisse
        # ohne abgeschnittene Zahlen. Die Kopfleiste kommt oben dazu.
        self.set_default_size(1008, 752)
        self.set_icon_von_datei()

        self._baue_kopfleiste()

        self.eingabe = EingabeBereich()
        self.ergebnis = ErgebnisBereich()
        self.eingabe.connect("geaendert", lambda _w: self.neu_berechnen())
        self.eingabe.connect("messfeld", lambda _w, name: self.ergebnis.zeige_messskizze(name))
        self.eingabe.connect("messen-zeigen", lambda _w, name: self.zeige_messen(name))
        self.eingabe.connect("katalog-gewaehlt", lambda _w, name: self.katalog_uebernommen(name))

        self.add(self._baue_koerper())

        self.eingabe.setze_werte(*einstellungen.lade())

        self.connect("delete-event", self._beim_schliessen)

    # ------------------------------------------------------------------ Aufbau

    def set_icon_von_datei(self) -> None:
        pfad = icon_pfad()
        if pfad.exists():
            try:
                self.set_icon_from_file(str(pfad))
            except Exception:  # pragma: no cover – Icon ist nicht kritisch
                pass

    def _baue_kopfleiste(self) -> None:
        leiste = Gtk.HeaderBar()
        leiste.set_show_close_button(True)
        leiste.set_title(APP_NAME)
        leiste.set_subtitle("Speichenlängen für Fahrradlaufräder")
        self.set_titlebar(leiste)

        kopieren = widgets.knopf("", "edit-copy-symbolic", "Ergebnis in die Zwischenablage kopieren")
        kopieren.connect("clicked", lambda _k: self.ergebnis_kopieren())
        leiste.pack_start(kopieren)

        speichern = widgets.knopf("", "document-save-as-symbolic", "Ergebnis als Textdatei sichern")
        speichern.connect("clicked", lambda _k: self.ergebnis_speichern())
        leiste.pack_start(speichern)

        menue = Gtk.MenuButton()
        menue.add(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menue.set_popup(self._baue_menue())
        leiste.pack_end(menue)

    def _baue_menue(self) -> Gtk.Menu:
        menue = Gtk.Menu()

        eintraege = (
            ("Nabentabelle bearbeiten …", self.zeige_nabentabelle),
            ("Skizze exportieren …", self.skizze_exportieren),
            (None, None),
            ("Eingaben zurücksetzen", self.eingabe_zuruecksetzen),
            (None, None),
            (f"Über {APP_NAME}", self.zeige_ueber),
        )
        for beschriftung, aktion in eintraege:
            if beschriftung is None:
                menue.append(Gtk.SeparatorMenuItem())
                continue
            eintrag = Gtk.MenuItem(label=beschriftung)
            eintrag.connect("activate", lambda _m, ziel=aktion: ziel())
            menue.append(eintrag)

        menue.show_all()
        return menue

    def eingabe_zuruecksetzen(self) -> None:
        self.eingabe.zuruecksetzen()

    def _baue_koerper(self) -> Gtk.Widget:
        """Beide Spalten dürfen schrumpfen und rollen, statt abgeschnitten zu werden."""
        self.eingabe.set_border_width(6)
        self.ergebnis.set_border_width(6)

        rechts = Gtk.ScrolledWindow()
        rechts.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rechts.set_propagate_natural_width(False)
        rechts.set_min_content_width(260)
        rechts.add(self.ergebnis)

        self.geteilt = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.geteilt.pack1(self.eingabe, True, True)
        self.geteilt.pack2(rechts, True, True)
        # Die Trennung sitzt anteilig, damit sie auch im kleinen Fenster passt.
        self._teiler_gesetzt = False
        self.geteilt.connect("size-allocate", self._teiler_setzen)
        return self.geteilt

    def _teiler_setzen(self, widget, zuteilung) -> None:
        """Legt die Trennlinie einmalig auf den Platzbedarf der Eingabespalte.

        So bekommen die Eingabefelder genau so viel Breite, wie sie brauchen,
        und der Rest bleibt für die Ergebnisse – statt eines festen Anteils,
        der je nach Theme mal passt und mal nicht.
        """
        if self._teiler_gesetzt or zuteilung.width < 100:
            return
        self._teiler_gesetzt = True

        _, gewuenscht = self.eingabe.get_preferred_width()
        gewuenscht += 10  # etwas Luft, sonst rutscht der Rahmen an den Rand

        # Die Ergebnisspalte bekommt, was sie mindestens braucht – sie trägt
        # die Zahlen. Reicht der Platz nicht für beide, rollt die Eingabe.
        noetig_rechts, _ = self.ergebnis.get_preferred_width()
        obergrenze = min(zuteilung.width - noetig_rechts - 12, zuteilung.width * 0.62)
        widget.set_position(int(max(min(gewuenscht, obergrenze), 240)))

    # ------------------------------------------------------------- Berechnung

    def neu_berechnen(self) -> None:
        """Liest das Formular, rechnet und aktualisiert die Anzeige."""
        nabe, felge, einspeichung, speichen, schritt = self.eingabe.werte()
        try:
            ergebnis = berechnung.berechne(nabe, felge, einspeichung, schritt, speichen)
        except ValueError as fehler:
            self.ergebnis.zeige_fehler(str(fehler))
            return
        self.ergebnis.zeige(nabe, felge, einspeichung, ergebnis, schritt, speichen)

    def _aktueller_bericht(self) -> str:
        nabe, felge, einspeichung, speichen, schritt = self.eingabe.werte()
        ergebnis = berechnung.berechne(nabe, felge, einspeichung, schritt, speichen)
        return bericht.als_text(nabe, felge, einspeichung, ergebnis, speichen)

    # ----------------------------------------------------------------- Aktionen

    def ergebnis_kopieren(self) -> None:
        try:
            text = self._aktueller_bericht()
        except ValueError as fehler:
            self._meldung(str(fehler), Gtk.MessageType.ERROR)
            return
        zwischenablage = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        zwischenablage.set_text(text, -1)
        self._meldung("Das Ergebnis liegt in der Zwischenablage.", Gtk.MessageType.INFO)

    def ergebnis_speichern(self) -> None:
        try:
            text = self._aktueller_bericht()
        except ValueError as fehler:
            self._meldung(str(fehler), Gtk.MessageType.ERROR)
            return

        dialog = Gtk.FileChooserDialog(
            title="Ergebnis speichern", transient_for=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        knopf = dialog.add_button("Speichern", Gtk.ResponseType.OK)
        knopf.get_style_context().add_class("suggested-action")
        dialog.set_current_name("speichenlaengen.txt")
        dialog.set_do_overwrite_confirmation(True)

        if dialog.run() == Gtk.ResponseType.OK:
            pfad = dialog.get_filename()
            dialog.destroy()
            try:
                with open(pfad, "w", encoding="utf-8") as datei:
                    datei.write(text)
            except OSError as fehler:
                self._meldung(f"Konnte nicht speichern: {fehler}", Gtk.MessageType.ERROR)
            else:
                self._meldung(f"Gespeichert: {pfad}", Gtk.MessageType.INFO)
        else:
            dialog.destroy()

    def katalog_uebernommen(self, bezeichnung: str) -> None:
        """Sagt, was aus dem Katalog kam – und was noch fehlt."""
        if getattr(self.eingabe, "_vollstaendig", False):
            text = (f"{bezeichnung} übernommen – einschließlich der Flanschmaße. "
                    "Vor dem Bestellen trotzdem gegenprüfen.")
        else:
            text = (f"{bezeichnung} übernommen.\n\n"
                    "Speichenloch-Ø, Lochzahl und Einbaubreite sind gesetzt. "
                    "Flanschabstand und Flansch-Ø stehen in dieser Liste nicht – "
                    "die bitte nachmessen oder dem Datenblatt entnehmen. Über "
                    "„Flanschabstand aus Einbaubreite …“ ist die Einbaubreite "
                    "schon eingetragen.")
        self._meldung(text, Gtk.MessageType.INFO)

    def zeige_nabentabelle(self) -> None:
        """Die Herstellertabelle zum Nachtragen fehlender Angaben."""
        fenster = TabellenFenster(self)
        geaendert = fenster.ausfuehren()
        fenster.destroy()
        if geaendert:
            # Die Nabenliste im Formular muss die Nachträge mitbekommen.
            self.eingabe.aktualisiere_vorlagen()

    def zeige_messen(self, schluessel: str) -> None:
        """Holt die passende Messskizze nach vorn – aus dem Abschnitt heraus."""
        self.ergebnis.zeige_messskizze(schluessel)
        self.ergebnis.zeige_messen()

    def skizze_exportieren(self) -> None:
        """Speichert die gerade sichtbare Zeichnung als PNG, PDF oder SVG."""
        skizze = self.ergebnis.aktuelle_skizze()
        if skizze is None:
            self._meldung(
                "Der Reiter „Vergleich“ ist eine Tabelle – bitte erst „Speichenbild“ "
                "oder „Querschnitt“ auswählen.",
                Gtk.MessageType.INFO,
            )
            return

        dialog = Gtk.FileChooserDialog(
            title="Skizze exportieren", transient_for=self, action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_button("Abbrechen", Gtk.ResponseType.CANCEL)
        knopf = dialog.add_button("Exportieren", Gtk.ResponseType.OK)
        knopf.get_style_context().add_class("suggested-action")
        dialog.set_current_name("speichenbild.png")
        dialog.set_do_overwrite_confirmation(True)

        for name, muster in (("Bild (*.png)", "*.png"), ("PDF (*.pdf)", "*.pdf"),
                             ("SVG (*.svg)", "*.svg")):
            filter_ = Gtk.FileFilter()
            filter_.set_name(name)
            filter_.add_pattern(muster)
            dialog.add_filter(filter_)

        if dialog.run() == Gtk.ResponseType.OK:
            pfad = dialog.get_filename()
            dialog.destroy()
            try:
                skizze.exportiere(pfad)
            except Exception as fehler:  # Cairo meldet je nach Format anders
                self._meldung(f"Export fehlgeschlagen: {fehler}", Gtk.MessageType.ERROR)
            else:
                self._meldung(f"Skizze gespeichert: {pfad}", Gtk.MessageType.INFO)
        else:
            dialog.destroy()

    def zeige_ueber(self) -> None:
        dialog = Gtk.AboutDialog(transient_for=self, modal=True)
        dialog.set_program_name(APP_NAME)
        dialog.set_version(VERSION)
        dialog.set_comments(
            "Berechnet Speichenlängen für Fahrradlaufräder aus Nabengeometrie, "
            "ERD und Kreuzungszahl.\n\n"
            "Die Ergebnisse sind so genau wie die Eingaben: ERD und Nabenmaße "
            "vor dem Bestellen nachmessen."
        )
        pfad = icon_pfad()
        if pfad.exists():
            dialog.set_logo(None)
            try:
                gi.require_version("GdkPixbuf", "2.0")
                from gi.repository import GdkPixbuf

                dialog.set_logo(GdkPixbuf.Pixbuf.new_from_file_at_size(str(pfad), 96, 96))
            except Exception:  # pragma: no cover
                pass
        dialog.run()
        dialog.destroy()

    def _meldung(self, text: str, art: Gtk.MessageType) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self, modal=True, message_type=art,
            buttons=Gtk.ButtonsType.OK, text=text,
        )
        dialog.run()
        dialog.destroy()

    # ----------------------------------------------------------------- Schluss

    def _beim_schliessen(self, *_args) -> bool:
        einstellungen.speichere(*self.eingabe.werte())
        return False
