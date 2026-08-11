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
        # Die Höhe steht fest, die Breite misst sich beim Anzeigen selbst –
        # siehe _startbreite_setzen.
        self.set_default_size(0, 752)
        self.set_icon_von_datei()

        self._baue_kopfleiste()

        self.eingabe = EingabeBereich()
        self.ergebnis = ErgebnisBereich()


        # Die vier Zusatzansichten werden genauso wie „Laufrad“ und
        # „Speichen“ als Seiten des linken Notebooks geöffnet. Dadurch gibt
        # es nur noch eine Tab-Leiste oben links und keine versteckte
        # Tab-Leiste mehr in der rechten Ergebnisspalte.
        # „Messen“ und „Vergleich“ teilen sich eine Seite: zwei kurze
        # Ansichten, die zusammen bequem auf eine passen und in der Leiste
        # sonst zweimal Platz kosten.
        self.eingabe.mappe.append_page(self.ergebnis.baue_messen_vergleich(),
                                       Gtk.Label(label="Messen / Vergleich"))
        self.eingabe.fuege_spannung_ein(self.ergebnis.spannung_ansicht)
        self.eingabe.mappe.append_page(self.ergebnis.bewertung_ansicht, Gtk.Label(label="Bewertung"))

        self.eingabe.connect("geaendert", lambda _w: self.neu_berechnen())
        self.eingabe.connect("katalog-gewaehlt", lambda _w, name: self.katalog_uebernommen(name))

        self.add(self._baue_koerper())

        self.eingabe.setze_werte(*einstellungen.lade())

        # Erst wenn das Fenster auf dem Schirm ist, kennen die Widgets ihren
        # Platzbedarf; vorher meldet ein unsichtbares Kind schlicht 0.
        self._breite_gesetzt = False
        self.connect("map", self._startbreite_setzen)

        self.connect("delete-event", self._beim_schliessen)

    def _startbreite_setzen(self, *_egal) -> None:
        """Zieht das Fenster einmalig auf die Breite des breitesten Reiters.

        Ohne das öffnet GTK auf der **Mindest**breite, und der Inhalt der
        Reiter steht rechts außerhalb. Gemessen wird erst beim Anzeigen: vorher
        sind die Kinder unsichtbar und melden 0.
        """
        if self._breite_gesetzt:
            return
        self._breite_gesetzt = True
        breite = self.get_preferred_width().natural_width
        hoehe = self.get_allocation().height or 752
        if breite > self.get_allocation().width:
            self.resize(breite, hoehe)

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
        """Gesamter sichtbarer Inhalt ohne leere rechte Ergebnisspalte."""
        self.eingabe.set_border_width(6)
        self.ergebnis.set_border_width(6)

        inhalt = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=widgets.ABSTAND,
        )

        # Speichenlängen ganz oben.
        inhalt.pack_start(
            self.ergebnis.kurzanzeige(),
            False,
            False,
            0,
        )

        # Eingabe-Notebook nimmt den Hauptbereich ein.
        inhalt.pack_start(
            self.eingabe,
            True,
            True,
            0,
        )

        # Hinweise ganz unten.
        inhalt.pack_start(
            self.ergebnis.hinweis_kasten,
            False,
            False,
            0,
        )
        self.ergebnis.hinweis_kasten.show_all()

        return inhalt

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
