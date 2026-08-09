"""Linke Spalte: alle Eingaben zu Nabe, Felge und Einspeichung.

Der Bereich kennt weder die Berechnung noch die Ergebnisanzeige. Er meldet
jede Änderung über das Signal ``geaendert``; das Hauptfenster rechnet dann neu.
Die Vorlagenverwaltung steckt in :mod:`~speichenrechner.ui.vorlagen_leiste`.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Pango", "1.0")
from gi.repository import GObject, Gtk, Pango  # noqa: E402

from .. import felgenkunde
from .. import katalog as nabenkatalog
from .. import vorlagen as vorlagen_speicher
from ..berechnung import RUNDUNGSSCHRITTE
from ..formatierung import zahl
from ..modelle import (
    KOPFLAGEN, NIPPEL_LAENGEN, NIPPEL_STANDARD, VERTEILUNGEN,
    Einspeichung, Felge, Nabe, Speichensatz, nippel_abzug,
)
from ..speiche import BAUARTEN, EIGENE_BAUART, E_MODUL, SPANNUNG_STANDARD, WEITUNG_STANDARD
from . import widgets
from .bauart_dialog import BauartDialog
from .nabe_hilfe import NabenmassDialog
from .vorlagen_leiste import VorlagenLeiste

#: Kennung des Listeneintrags, der das Abzugsfeld freigibt.
EIGENER_ABZUG = "eigen"

RUNDUNG_TEXTE = {
    1.0: "auf 1 mm (üblich)",
    0.5: "auf 0,5 mm",
    2.0: "auf 2 mm",
}


class EingabeBereich(Gtk.Box):
    """Formular für Nabe, Felge und Einspeichung."""

    __gsignals__ = {
        "geaendert": (GObject.SignalFlags.RUN_FIRST, None, ()),
        # Eine Nabe wurde aus dem Katalog übernommen.
        "katalog-gewaehlt": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)
        self._stumm = False  # unterdrückt Signale beim programmatischen Setzen
        self._katalogart = ""                  # Filter über die Nabenart
        self._kataloghersteller = ""           # Filter über den Hersteller
        self._katalogname: str | None = None   # Nabenname aus dem Katalog
        self._nabenart = ""                    # Bauart der gewählten Nabe
        self._nabenaufnahme = ""               # Ritzelaufnahme der gewählten Nabe
        self._einbaubreite: float | None = None  # zuletzt bekannte Einbaubreite
        self._felgenkategorie = ""             # Filter über die Felgenkategorie

        # Zwei Reiter statt einer langen Spalte: so bleibt das Fenster auch
        # unmaximiert bedienbar. Das Nötigste steht im ersten Reiter.
        self.mappe = Gtk.Notebook()
        self.mappe.set_scrollable(False)
        # Alle sechs Ansichten werden wie die bestehenden Reiter „Laufrad“
        # und „Speichen“ direkt in diesem Notebook geöffnet.
        self.mappe.set_show_tabs(True)
        self.mappe.append_page(
            self._seite(self._baue_nabe(), self._baue_felge(), self._baue_einspeichung()),
            Gtk.Label(label="Laufrad"),
        )
        self.mappe.append_page(
            self._seite(self._baue_speichen(), self._baue_nippel()),
            Gtk.Label(label="Speichen"),
        )
        self.pack_start(self.mappe, True, True, 0)

    @staticmethod
    def _seite(*rahmen: Gtk.Widget) -> Gtk.Widget:
        """Packt Abschnitte scrollbar in einen Reiter."""
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)
        kasten.set_border_width(widgets.RAND)
        for eintrag in rahmen:
            kasten.pack_start(eintrag, False, False, 0)

        rollbar = Gtk.ScrolledWindow()
        rollbar.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        rollbar.set_propagate_natural_width(True)
        rollbar.set_min_content_width(220)
        rollbar.add(kasten)
        return rollbar

    # ------------------------------------------------------------------ Aufbau

    def _baue_nabe(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Nabe")
        reihe = 0

        self.nabe_vorlage = VorlagenLeiste(
            "Nabe als Vorlage speichern",
            laden=self._nabenvorlagen,
            speichern=vorlagen_speicher.speichere_nabe,
            loeschen=vorlagen_speicher.loesche_nabe,
            ist_eigene=vorlagen_speicher.ist_eigene_nabe,
            aktuelle_werte=lambda: self.werte()[0],
            zusatz=lambda: nabenkatalog.als_listeneintraege(
                self._katalogart, self._kataloghersteller
            ),
        )
        self.nabe_vorlage.connect("gewaehlt", self._nabe_uebernehmen)

        # Zwei Filter über der Liste: Art und Hersteller. Sie halten die
        # Auswahl kurz, ohne dass man tippen muss.
        self.nabenart = Gtk.ComboBoxText()
        katalog_jetzt = nabenkatalog.lade()
        gesamt = sum(1 for e in katalog_jetzt.naben if e.einspeichbar)
        self.nabenart.append("", f"alle Arten ({gesamt})")
        # Die Anzahl steht dabei: sonst wirkt ein Merkmal mit sechs Naben wie
        # ein Fehler des Filters, obwohl die Tabelle nicht mehr hergibt.
        for art, anzahl in katalog_jetzt.arten_mit_anzahl():
            self.nabenart.append(art, f"{art} ({anzahl})")
        self.nabenart.set_active_id("")
        self.nabenart.set_tooltip_text(
            "Schränkt die Auswahlliste ein; in Klammern steht, wie viele Naben "
            "die Tabelle dazu führt. Bauart und Ritzelaufnahme stehen "
            "nebeneinander: eine Rohloff findet sich unter „Nabenschaltung“ "
            "wie unter „Schraubritzel“, ein SON-Dynamo unter „Dynamo“ wie "
            "unter „Vorderrad“."
        )
        self._kurz_halten(self.nabenart, 18)
        self.nabenart.connect("changed", self._nabenart_geaendert)

        self.nabenhersteller = Gtk.ComboBoxText()
        self.nabenhersteller.set_tooltip_text(
            "Schränkt die Auswahlliste auf einen Hersteller ein."
        )
        self._hersteller_fuellen()
        self.nabenhersteller.connect("changed", self._nabenhersteller_geaendert)

        filterzeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        filterzeile.set_homogeneous(True)
        filterzeile.pack_start(self.nabenart, True, True, 0)
        filterzeile.pack_start(self.nabenhersteller, True, True, 0)
        raster.attach(filterzeile, 0, reihe, 3, 1)
        reihe += 1

        raster.attach(self.nabe_vorlage, 0, reihe, 3, 1)
        reihe += 1

        reihe = widgets.spaltenkoepfe(raster, reihe)

        self.flansch_d_links = widgets.zahlenfeld(10, 200, 0.5, 1, 45.0)
        self.flansch_d_rechts = widgets.zahlenfeld(10, 200, 0.5, 1, 45.0)
        reihe = widgets.doppelzeile(
            raster, reihe, "Flansch-Ø",
            self.flansch_d_links, self.flansch_d_rechts,
            hilfe="Durchmesser durch die Mitten der Speichenlöcher im Flansch.",
        )

        self.flansch_a_links = widgets.zahlenfeld(0, 120, 0.5, 1, 35.0)
        self.flansch_a_rechts = widgets.zahlenfeld(0, 120, 0.5, 1, 20.0)
        reihe = widgets.doppelzeile(
            raster, reihe, "Flanschabstand",
            self.flansch_a_links, self.flansch_a_rechts,
            hilfe="Flanschabstand: von der Nabenmitte bis zur Flanschmitte.",
        )

        self.speichenloch = widgets.zahlenfeld(1.0, 5.0, 0.1, 1, 2.6)
        reihe = widgets.zeile(
            raster, reihe, "Speichenloch-Ø", self.speichenloch,
            hilfe="Lochdurchmesser im Flansch, meist 2,5 bis 2,6 mm.",
        )

        self.flanschdicke = widgets.zahlenfeld(0.5, 12.0, 0.1, 1, 3.2)
        reihe = widgets.zeile(
            raster, reihe, "Flanschdicke", self.flanschdicke,
            hilfe="Nur nötig, wenn alle Speichenköpfe auf derselben Flanschseite "
                  "sitzen – dann verschiebt sich der Ansatzpunkt um die Hälfte davon.",
        )

        hilfe_knopf = widgets.knopf(
            "Flanschabstand aus Einbaubreite …", "accessories-calculator-symbolic",
            "Maße ab Kontermutter/Endkappe in Abstände ab Nabenmitte umrechnen",
        )
        hilfe_knopf.connect("clicked", self._nabenmass_hilfe)
        raster.attach(hilfe_knopf, 0, reihe, 3, 1)

        for feld in (self.flansch_d_links, self.flansch_d_rechts, self.flansch_a_links,
                     self.flansch_a_rechts, self.speichenloch, self.flanschdicke):
            feld.connect("value-changed", self._feld_geaendert, self.nabe_vorlage)
        return rahmen

    def _baue_felge(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Felge")
        reihe = 0

        self.felge_vorlage = VorlagenLeiste(
            "Felge als Vorlage speichern",
            laden=vorlagen_speicher.alle_felgen,
            speichern=vorlagen_speicher.speichere_felge,
            loeschen=vorlagen_speicher.loesche_felge,
            ist_eigene=vorlagen_speicher.ist_eigene_felge,
            aktuelle_werte=lambda: self.werte()[1],
        )
        self.felge_vorlage.connect("gewaehlt", self._felge_uebernehmen)
        raster.attach(self.felge_vorlage, 0, reihe, 3, 1)
        reihe += 1

        self.erd = widgets.zahlenfeld(100, 800, 0.5, 1, 600.0)
        reihe = widgets.zeile(
            raster, reihe, "ERD", self.erd,
            hilfe="Effektiver Felgendurchmesser: Nippelsitz zu Nippelsitz, nicht der Reifensitz.",
        )

        self.versatz = widgets.zahlenfeld(-15, 15, 0.5, 1, 0.0)
        reihe = widgets.zeile(
            raster, reihe, "Versatz", self.versatz,
            hilfe="Asymmetrische Felge: Versatz des Speichenbetts aus der Mitte.\n"
                  "Minus = nach links, Plus = nach rechts. Beim Hinterrad ist ein "
                  "Versatz nach links üblich, er gleicht die Spannung an.",
        )

        reihe = self._baue_felgentyp(raster, reihe)

        for feld in (self.erd, self.versatz):
            feld.connect("value-changed", self._feld_geaendert, self.felge_vorlage)

        return rahmen

    def _baue_felgentyp(self, raster: Gtk.Grid, reihe: int) -> int:
        """Bauform der Felge – gleich unter ERD und Versatz, nicht im Menü.

        Der Typ ändert die Speichenlänge nicht. Er bestimmt die Hinweise zu
        Ösung, Werkstoff und Spannung – deshalb steht er hier und nicht abseits.

        Der Abschnitt belegt **eine** Zeile: Filter und Auswahl stehen
        nebeneinander, die Beschreibung erscheint erst, wenn ein Typ gewählt
        ist. Sonst wächst der Reiter „Laufrad“ über die Fensterhöhe und die
        Einspeichung rutscht aus dem Bild.
        """
        kunde = felgenkunde.lade()
        # Die Fußnote der Tabelle gehört an die Auswahl, auf die sie sich bezieht.
        fussnote = "  ".join(kunde.fussnoten)

        self.felgenkategorie = Gtk.ComboBoxText()
        self.felgenkategorie.append("", "alle")
        for kategorie in kunde.kategorien():
            self.felgenkategorie.append(kategorie, kategorie)
        self.felgenkategorie.set_active_id("")
        self.felgenkategorie.set_tooltip_text(
            "Schränkt die Auswahl ein: Bauform, Material oder Einsatzbereich."
        )
        self.felgenkategorie.connect("changed", self._felgenkategorie_geaendert)

        self.felgentyp = Gtk.ComboBoxText()
        self.felgentyp.set_hexpand(True)
        # Lange Namen wie „Hakenlose Felge (Hookless/TSS)“ würden die Klappliste
        # und damit die ganze Eingabespalte breit machen. Gekürzt wird nur die
        # Anzeige – in der aufgeklappten Liste und im Tooltip steht der
        # vollständige Name, und darunter ohnehin die Beschreibung.
        for zelle in self.felgentyp.get_cells():
            zelle.set_property("ellipsize", Pango.EllipsizeMode.END)
            zelle.set_property("width-chars", 16)
        self.felgentyp.connect("changed", self._felgentyp_geaendert)
        self._felgentypen_fuellen()

        auswahl = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        auswahl.pack_start(self.felgenkategorie, False, False, 0)
        auswahl.pack_start(self.felgentyp, True, True, 0)

        beschriftung = Gtk.Label(label="Felgentyp", xalign=0.0)
        hilfe = ("Bauform der Felge. Sie ändert die Speichenlänge nicht, wohl aber "
                 "die Hinweise zu Ösung, Werkstoff und Spannung."
                 + (f"\n\n{fussnote}" if fussnote else ""))
        beschriftung.set_tooltip_text(hilfe)
        self.felgentyp.set_tooltip_text(hilfe)
        raster.attach(beschriftung, 0, reihe, 1, 1)
        raster.attach(auswahl, 1, reihe, 2, 1)
        reihe += 1

        self.felgeninfo = Gtk.Label(label="", xalign=0.0)
        self.felgeninfo.set_line_wrap(True)
        self.felgeninfo.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        # Ein kleiner Wunsch-Wert heißt: die Zeile richtet sich nach der Breite,
        # die die übrigen Felder vorgeben, statt sie zu bestimmen. Ohne das zog
        # der längste Beschreibungstext die ganze Eingabespalte breiter.
        self.felgeninfo.set_max_width_chars(16)
        self.felgeninfo.get_style_context().add_class("dim-label")
        # Ohne gewählten Typ bleibt die Zeile leer – und darf dann auch keinen
        # Platz belegen. set_no_show_all verhindert, dass show_all() sie holt.
        self.felgeninfo.set_no_show_all(True)
        raster.attach(self.felgeninfo, 0, reihe, 3, 1)
        reihe += 1
        self._felgeninfo_setzen()

        return reihe

    def _felgentypen_fuellen(self) -> None:
        """Baut die Typenliste zur gewählten Kategorie neu auf."""
        vorher = self.felgentyp.get_active_id() or ""
        stumm_vorher = self._stumm
        self._stumm = True

        self.felgentyp.remove_all()
        self.felgentyp.append("", "kein bestimmter Typ")
        namen = []
        for _text, typ in felgenkunde.als_listeneintraege(self._felgenkategorie):
            self.felgentyp.append(typ.name, typ.listentext)
            namen.append(typ.name)

        # Die bisherige Wahl behalten, wenn sie in dieser Kategorie vorkommt.
        self.felgentyp.set_active_id(vorher if vorher in namen else "")
        self._stumm = stumm_vorher

    def _felgenkategorie_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        if self._stumm:
            return
        self._felgenkategorie = combo.get_active_id() or ""
        vorher = self.felgentyp.get_active_id() or ""
        self._felgentypen_fuellen()
        self._felgeninfo_setzen()
        if (self.felgentyp.get_active_id() or "") != vorher:
            # Der Filter hat die Wahl verworfen – das ist eine Änderung.
            self._melde()

    def _felgentyp_geaendert(self, _combo) -> None:
        # Beim Aufbau und beim Neufüllen der Liste feuert „changed“ ebenfalls;
        # dann steht die Beschriftung noch gar nicht. Wer die Liste umbaut,
        # setzt die Beschreibung selbst.
        if self._stumm:
            return
        self._felgeninfo_setzen()
        self._melde()

    def _felgeninfo_setzen(self) -> None:
        """Zeigt unter der Auswahl, was die Tabelle zu diesem Typ sagt.

        Ohne gewählten Typ bleibt die Zeile weg, damit der Abschnitt so hoch
        bleibt wie zuvor.
        """
        typ = felgenkunde.finde(self.felgentyp.get_active_id() or "")
        if typ is None:
            self.felgeninfo.set_text("")
            self.felgeninfo.hide()
            return

        # Drei Zeilen, jede mit einer eigenen Aussage – der vollständige Name
        # zuerst, weil die Klappliste ihn kürzt.
        kopf = f"{typ.name} · {typ.kategorie}" if typ.kategorie else typ.name
        zeilen = [kopf, typ.kurzbeschreibung]

        dritte = []
        if typ.einsatz:
            dritte.append(typ.einsatz)
        if typ.kindergroessen:
            dritte.append(f"Kinder: {typ.kindergroessen}")
        bereich = typ.spannungsbereich
        if bereich:
            dritte.append(f"{bereich[0]:.0f}–{bereich[1]:.0f} N üblich")
        if dritte:
            zeilen.append(" · ".join(dritte))

        text = "\n".join(zeile for zeile in zeilen if zeile)
        self.felgeninfo.set_text(text)
        self.felgeninfo.set_tooltip_text(text)
        self.felgeninfo.show()

    def _baue_einspeichung(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Einspeichung")
        reihe = 0

        self.speichenzahl = widgets.zahlenfeld(8, 64, 2, 0, 32)
        reihe = widgets.zeile(
            raster, reihe, "Speichenzahl", self.speichenzahl, einheit="Stück",
            hilfe="Gesamtzahl der Speichen im Laufrad, je Seite die Hälfte.",
        )

        self.verteilung = Gtk.ComboBoxText()
        for schluessel, beschriftung in VERTEILUNGEN.items():
            self.verteilung.append(schluessel, beschriftung)
        self.verteilung.set_active_id("1:1")
        self.verteilung.connect("changed", self._einfach_geaendert)
        reihe = widgets.zeile(
            raster, reihe, "Verteilung", self.verteilung, einheit=None,
            hilfe="1:1 ist der Normalfall. Bei 2:1 trägt die rechte Seite doppelt "
                  "so viele Speichen – das gleicht beim Hinterrad die Spannung an, "
                  "die Nabe muss dafür gebohrt sein.",
        )

        self.kreuzungen_links = widgets.zahlenfeld(0, 6, 1, 0, 3)
        self.kreuzungen_rechts = widgets.zahlenfeld(0, 6, 1, 0, 3)
        reihe = widgets.doppelzeile(
            raster, reihe, "Kreuzungen", self.kreuzungen_links, self.kreuzungen_rechts,
            einheit="fach",
            hilfe="Wie oft eine Speiche andere Speichen derselben Seite kreuzt. 0 = radial.",
        )

        self.gekoppelt = Gtk.CheckButton(label="Beide Seiten gleich kreuzen")
        self.gekoppelt.set_active(True)
        self.gekoppelt.connect("toggled", self._kopplung_geaendert)
        raster.attach(self.gekoppelt, 0, reihe, 3, 1)
        reihe += 1

        self.rundung = Gtk.ComboBoxText()
        for schritt in RUNDUNGSSCHRITTE:
            self.rundung.append(str(schritt), RUNDUNG_TEXTE[schritt])
        self.rundung.set_active_id("1.0")
        self.rundung.connect("changed", self._einfach_geaendert)
        reihe = widgets.zeile(raster, reihe, "Rundung", self.rundung, einheit=None,
                              hilfe="Speichen gibt es meist nur in ganzen Millimetern.")

        self.speichenzahl.connect("value-changed", self._einfach_geaendert)
        self.kreuzungen_links.connect("value-changed", self._kreuzung_links_geaendert)
        self.kreuzungen_rechts.connect("value-changed", self._kreuzung_rechts_geaendert)

        return rahmen

    def _baue_speichen(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Speichen")
        reihe = 0

        self._eigene_bauart: dict | None = None
        self._e_modul = E_MODUL

        self.bauart = Gtk.ComboBoxText()
        for eintrag in BAUARTEN:
            self.bauart.append(eintrag.name, eintrag.name)
        self.bauart.append(EIGENE_BAUART, EIGENE_BAUART)
        self.bauart.set_active_id(BAUARTEN[1].name)
        self.bauart.set_hexpand(True)
        self.bauart.connect("changed", self._bauart_geaendert)

        masse_knopf = widgets.knopf("", "document-edit-symbolic",
                                    "Speichenmaße und E-Modul bearbeiten")
        masse_knopf.connect("clicked", self._bauart_bearbeiten)

        kopf = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        kopf.pack_start(self.bauart, True, True, 0)
        kopf.pack_start(masse_knopf, False, False, 0)
        raster.attach(Gtk.Label(label="Bauart", xalign=0.0), 0, reihe, 1, 1)
        raster.attach(kopf, 1, reihe, 2, 1)
        reihe += 1

        self.spannung = widgets.zahlenfeld(200, 1600, 25, 0, SPANNUNG_STANDARD)
        reihe = widgets.zeile(
            raster, reihe, "Spannung", self.spannung, einheit="N",
            hilfe="Zielspannung der stärker gespannten Seite. Die andere Seite "
                  "ergibt sich aus dem Spannungsverhältnis.",
        )

        self.kopf = Gtk.ComboBoxText()
        for schluessel, beschriftung in KOPFLAGEN.items():
            self.kopf.append(schluessel, beschriftung)
        self.kopf.set_active_id("gemischt")
        self.kopf.connect("changed", self._einfach_geaendert)
        reihe = widgets.zeile(
            raster, reihe, "Kopflage", self.kopf, einheit=None,
            hilfe="Normalerweise wechseln sich Köpfe innen und außen ab, dann zählt "
                  "die Flanschmitte. Sitzen alle Köpfe auf derselben Seite, "
                  "verschiebt sich der Ansatzpunkt um die halbe Flanschdicke.",
        )

        self.straightpull = Gtk.CheckButton(label="Straightpull (Speiche ohne Bogen)")
        self.straightpull.set_tooltip_text(
            "Straightpull-Speichen haben keinen Bogen, der sich am Lochrand anlegt. "
            "Der Abzug für das Speichenloch und die Bogenweitung entfallen."
        )
        self.straightpull.connect("toggled", self._einfach_geaendert)
        raster.attach(self.straightpull, 0, reihe, 3, 1)

        self.spannung.connect("value-changed", self._einfach_geaendert)

        return rahmen

    def _baue_nippel(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Nippel und Korrektur")
        reihe = 0

        self.unterlegscheibe = widgets.zahlenfeld(0.0, 3.0, 0.1, 1, 0.0)
        reihe = widgets.zeile(
            raster, reihe, "Unterlegscheiben", self.unterlegscheibe,
            hilfe="Scheiben unter dem Nippel rücken den Nippelsitz nach außen. "
                  "Der wirksame ERD wächst um das Doppelte dieser Dicke.",
        )

        # Gefragt wird nach der Nippellänge – die steht auf der Packung. Der
        # Abzug daraus ist eine Rechnung, keine Angabe, die man kennen muss.
        # „Nippel-Verkürzung" als Feldname war irreführend: dort stand nicht die
        # Länge, sondern die Differenz.
        self.nippellaenge = Gtk.ComboBoxText()
        for laenge in NIPPEL_LAENGEN:
            beschriftung = f"{zahl(laenge, 0)} mm"
            if laenge == NIPPEL_STANDARD:
                beschriftung += "  (üblich)"
            self.nippellaenge.append(str(laenge), beschriftung)
        self.nippellaenge.append(EIGENER_ABZUG, "eigener Abzug …")
        self.nippellaenge.set_active_id(str(NIPPEL_STANDARD))
        self.nippellaenge.connect("changed", self._nippellaenge_geaendert)
        reihe = widgets.zeile(
            raster, reihe, "Nippellänge", self.nippellaenge, einheit=None,
            hilfe="Die Länge, die auf der Nippelpackung steht. Ein längerer "
                  "Nippel greift tiefer, die Speiche darf entsprechend kürzer "
                  "sein – wie viel, steht in der Zeile darunter.",
        )

        self.nippel_korrektur = widgets.zahlenfeld(0.0, 4.0, 0.5, 1, 0.0)
        self.nippel_korrektur.set_sensitive(False)
        reihe = widgets.zeile(
            raster, reihe, "→ Abzug", self.nippel_korrektur,
            hilfe="Der Abzug, mit dem gerechnet wird: Nippellänge minus 12 mm. "
                  "Zum Eintippen einer Herstellerangabe oben „eigener Abzug“ wählen.",
        )

        self.weitung = widgets.zahlenfeld(0.0, 1.0, 0.05, 2, WEITUNG_STANDARD)
        reihe = widgets.zeile(
            raster, reihe, "Weitung", self.weitung,
            hilfe="Unter Last weiten sich Speichenloch und Speichenbogen etwas auf. "
                  "Üblich sind rund 0,1 mm je Seite.",
        )

        self.korrektur_anwenden = Gtk.CheckButton(
            label="Korrektur von der Bestelllänge abziehen"
        )
        self.korrektur_anwenden.set_tooltip_text(
            "Die berechnete Länge gilt für das gespannte Laufrad. Ungespannt ist "
            "die Speiche um Dehnung, Weitung und Nippel-Verkürzung kürzer. "
            "Klassische Rechner lassen diese Korrektur weg."
        )
        self.korrektur_anwenden.connect("toggled", self._einfach_geaendert)
        raster.attach(self.korrektur_anwenden, 0, reihe, 3, 1)

        for feld in (self.unterlegscheibe, self.nippel_korrektur, self.weitung):
            feld.connect("value-changed", self._einfach_geaendert)

        return rahmen

    def _nippellaenge_wert(self) -> float:
        """Die gewählte Länge; bei „eigener Abzug" bleibt die Vorgabe stehen."""
        wahl = self.nippellaenge.get_active_id() or str(NIPPEL_STANDARD)
        return NIPPEL_STANDARD if wahl == EIGENER_ABZUG else float(wahl)

    def _nippellaenge_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        """Setzt den Abzug aus der Länge – oder gibt das Feld frei."""
        wahl = combo.get_active_id() or str(NIPPEL_STANDARD)
        eigen = wahl == EIGENER_ABZUG
        self.nippel_korrektur.set_sensitive(eigen)
        if not eigen:
            stumm_vorher = self._stumm
            self._stumm = True
            self.nippel_korrektur.set_value(nippel_abzug(float(wahl)))
            self._stumm = stumm_vorher
        self._melde()

    def _bauart_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        """Bei „eigene Maße“ gleich den Dialog anbieten, sonst nur rechnen."""
        if not self._stumm and combo.get_active_id() == EIGENE_BAUART \
                and self._eigene_bauart is None:
            self._bauart_bearbeiten(None)
            return
        self._einfach_geaendert(combo)

    def _bauart_bearbeiten(self, _knopf) -> None:
        dialog = BauartDialog(self.get_toplevel(), self._eigene_bauart, self._e_modul)
        ergebnis = dialog.ausfuehren()
        dialog.destroy()
        if ergebnis is None:
            return
        self._eigene_bauart, self._e_modul = ergebnis
        self._stumm = True
        self.bauart.set_active_id(EIGENE_BAUART)
        self._stumm = False
        self._melde()

    # ------------------------------------------------------------- Reaktionen

    def _melde(self) -> None:
        if not self._stumm:
            self.emit("geaendert")

    def _einfach_geaendert(self, _widget) -> None:
        self._melde()

    def _feld_geaendert(self, _widget, leiste: VorlagenLeiste) -> None:
        """Handeingabe löst die Vorlagenauswahl auf „eigene Werte“."""
        if not self._stumm:
            leiste.auf_eigene_werte()
        self._melde()

    def _kopplung_geaendert(self, schalter: Gtk.CheckButton) -> None:
        self.kreuzungen_rechts.set_sensitive(not schalter.get_active())
        if schalter.get_active():
            self.kreuzungen_rechts.set_value(self.kreuzungen_links.get_value())
        self._melde()

    def _kreuzung_links_geaendert(self, feld: Gtk.SpinButton) -> None:
        if self.gekoppelt.get_active():
            self._stumm = True
            self.kreuzungen_rechts.set_value(feld.get_value())
            self._stumm = False
        self._melde()

    def _kreuzung_rechts_geaendert(self, _feld) -> None:
        self._melde()

    # --------------------------------------------------------------- Vorlagen

    def aktualisiere_vorlagen(self) -> None:
        """Lädt beide Vorlagenlisten neu – auch nach Nachträgen im Katalog."""
        self._hersteller_fuellen()
        self.nabe_vorlage.aktualisieren()
        self.felge_vorlage.aktualisieren()

    def _nabe_uebernehmen(self, _leiste, auswahl) -> None:
        """In der Liste stehen Vorlagen und Katalognaben nebeneinander."""
        if auswahl is None:
            self._katalogname = None
            self._einbaubreite = None
            return
        if isinstance(auswahl, Nabe):
            self._vorlage_uebernehmen(auswahl)
        else:
            self._katalognabe_uebernehmen(auswahl)

    def _vorlage_uebernehmen(self, nabe: Nabe) -> None:
        self._katalogname = None
        self._einbaubreite = None
        self._nabenart = nabe.art
        self._nabenaufnahme = nabe.aufnahme
        self._stumm = True
        self.flansch_d_links.set_value(nabe.flanschdurchmesser_links)
        self.flansch_d_rechts.set_value(nabe.flanschdurchmesser_rechts)
        self.flansch_a_links.set_value(nabe.flanschabstand_links)
        self.flansch_a_rechts.set_value(nabe.flanschabstand_rechts)
        self.speichenloch.set_value(nabe.speichenloch)
        self.flanschdicke.set_value(nabe.flanschdicke)
        self._stumm = False
        self._melde()

    def _felge_uebernehmen(self, _leiste, felge: Felge | None) -> None:
        if felge is None:
            return
        self._stumm = True
        self.erd.set_value(felge.erd)
        self.versatz.set_value(felge.versatz)
        self._stumm = False
        self._melde()

    def _nabenvorlagen(self) -> list[Nabe]:
        """Vorlagen für die Auswahlliste – dem Filter unterworfen wie der Katalog.

        Ist ein Hersteller gewählt, bleiben die Vorlagen ganz draußen: sie
        gehören zu keinem Hersteller.
        """
        if self._kataloghersteller:
            return []
        return vorlagen_speicher.alle_naben(self._katalogart)

    @staticmethod
    def _kurz_halten(combo: Gtk.ComboBoxText, zeichen: int) -> None:
        """Deckelt die Breite einer Klappliste auf ``zeichen`` Zeichen.

        ``width-chars`` allein genügt nicht – das ist eine **Mindest**breite.
        Erst ``max-width-chars`` begrenzt, was die Liste an Platz verlangt;
        gekürzt wird nur die Anzeige, in der aufgeklappten Liste steht der
        ganze Text.
        """
        for zelle in combo.get_cells():
            zelle.set_property("ellipsize", Pango.EllipsizeMode.END)
            zelle.set_property("width-chars", min(zeichen, 8))
            try:
                zelle.set_property("max-width-chars", zeichen)
            except TypeError:      # ältere GTK-Fassung kennt die Eigenschaft nicht
                pass

    @staticmethod
    def _herstellerkurz(name: str) -> str:
        """„SON (Schmidt Maschinenbau)“ → „SON“ – nur für die Filterliste.

        Der vollständige Name bleibt in den Listeneinträgen der Naben stehen;
        hier zählt, dass die Klappliste die Eingabespalte nicht breit macht.
        """
        kurz = name.split(" (")[0].strip()
        return kurz if len(kurz) >= 3 else name

    def _hersteller_fuellen(self) -> None:
        """Zeigt nur Hersteller, die zur gewählten Art auch Naben haben."""
        self._stumm = True
        self.nabenhersteller.remove_all()
        mit_anzahl = nabenkatalog.lade().hersteller_mit_anzahl(self._katalogart)
        gesamt = sum(anzahl for _, anzahl in mit_anzahl)
        self.nabenhersteller.append("", f"alle Hersteller ({gesamt})")
        namen = [name for name, _ in mit_anzahl]
        for name, anzahl in mit_anzahl:
            self.nabenhersteller.append(name, f"{self._herstellerkurz(name)} ({anzahl})")
        self._kurz_halten(self.nabenhersteller, 18)
        # Die bisherige Wahl behalten, wenn es sie in dieser Art noch gibt.
        if self._kataloghersteller not in namen:
            self._kataloghersteller = ""
        self.nabenhersteller.set_active_id(self._kataloghersteller)
        self._stumm = False

    def _nabenart_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        """Baut Herstellerliste und Auswahlliste für die gewählte Art neu auf."""
        if self._stumm:
            return
        self._katalogart = combo.get_active_id() or ""
        self._hersteller_fuellen()
        self.nabe_vorlage.aktualisieren()

    def _nabenhersteller_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        if self._stumm:
            return
        self._kataloghersteller = combo.get_active_id() or ""
        self.nabe_vorlage.aktualisieren()

    def _katalognabe_uebernehmen(self, eintrag) -> None:
        """Übernimmt aus dem Katalog, was dort hinterlegt ist."""
        self._stumm = True
        if eintrag.speichenloch_mm:
            self.speichenloch.set_value(eintrag.speichenloch_mm)
        if eintrag.hat_flanschmasse:
            # Führt die Tabelle auch die Flanschmaße, ist nichts mehr zu messen.
            abstand = eintrag.flanschabstaende
            durchmesser = eintrag.flanschdurchmesser_paar
            self.flansch_a_links.set_value(abstand[0])
            self.flansch_a_rechts.set_value(abstand[1])
            self.flansch_d_links.set_value(durchmesser[0])
            self.flansch_d_rechts.set_value(durchmesser[1])
        if eintrag.lochzahlen:
            # Die aktuelle Speichenzahl behalten, wenn das Modell sie anbietet.
            aktuell = int(self.speichenzahl.get_value())
            if aktuell not in eintrag.lochzahlen:
                self.speichenzahl.set_value(max(eintrag.lochzahlen))
        self._einbaubreite = eintrag.einbaubreiten[0] if eintrag.einbaubreiten else None
        self._katalogname = eintrag.bezeichnung
        self._nabenart = eintrag.art
        self._nabenaufnahme = eintrag.aufnahme
        self._vollstaendig = eintrag.hat_flanschmasse
        self._stumm = False

        self._melde()
        self.emit("katalog-gewaehlt", eintrag.bezeichnung)

    def _nabenmass_hilfe(self, _knopf) -> None:
        dialog = NabenmassDialog(self.get_toplevel(), self._einbaubreite)
        ergebnis = dialog.ausfuehren()
        dialog.destroy()
        if ergebnis is None:
            return
        links, rechts = ergebnis
        self._stumm = True
        self.flansch_a_links.set_value(links)
        self.flansch_a_rechts.set_value(rechts)
        self.nabe_vorlage.auf_eigene_werte()
        self._stumm = False
        self._melde()

    # ------------------------------------------------------------ Datenzugang

    def werte(self) -> tuple[Nabe, Felge, Einspeichung, Speichensatz, float]:
        """Liest den aktuellen Formularstand aus."""
        nabe = Nabe(
            name=self._katalogname or self.nabe_vorlage.name() or "Eigene Nabe",
            flanschdurchmesser_links=self.flansch_d_links.get_value(),
            flanschdurchmesser_rechts=self.flansch_d_rechts.get_value(),
            flanschabstand_links=self.flansch_a_links.get_value(),
            flanschabstand_rechts=self.flansch_a_rechts.get_value(),
            speichenloch=self.speichenloch.get_value(),
            flanschdicke=self.flanschdicke.get_value(),
            art=self._nabenart,
            aufnahme=self._nabenaufnahme,
        )
        felge = Felge(
            name=self.felge_vorlage.name() or "Eigene Felge",
            erd=self.erd.get_value(),
            versatz=self.versatz.get_value(),
            typ=self.felgentyp.get_active_id() or "",
        )
        einspeichung = Einspeichung(
            speichenzahl=int(self.speichenzahl.get_value()),
            kreuzungen_links=int(self.kreuzungen_links.get_value()),
            kreuzungen_rechts=int(self.kreuzungen_rechts.get_value()),
            verteilung=self.verteilung.get_active_id() or "1:1",
        )
        speichen = Speichensatz(
            bauart=self.bauart.get_active_id() or BAUARTEN[1].name,
            eigene_bauart=self._eigene_bauart,
            e_modul=self._e_modul,
            spannung=self.spannung.get_value(),
            korrektur_anwenden=self.korrektur_anwenden.get_active(),
            weitung=self.weitung.get_value(),
            nippellaenge=self._nippellaenge_wert(),
            nippel_verkuerzung=self.nippel_korrektur.get_value(),
            unterlegscheibe=self.unterlegscheibe.get_value(),
            straightpull=self.straightpull.get_active(),
            kopf=self.kopf.get_active_id() or "gemischt",
        )
        schritt = float(self.rundung.get_active_id() or 1.0)
        return nabe, felge, einspeichung, speichen, schritt

    def setze_werte(
        self,
        nabe: Nabe,
        felge: Felge,
        einspeichung: Einspeichung,
        speichen: Speichensatz,
        schritt: float,
    ) -> None:
        """Übernimmt einen gespeicherten Stand ohne Zwischen-Neuberechnungen."""
        self._stumm = True

        self.flansch_d_links.set_value(nabe.flanschdurchmesser_links)
        self.flansch_d_rechts.set_value(nabe.flanschdurchmesser_rechts)
        self.flansch_a_links.set_value(nabe.flanschabstand_links)
        self.flansch_a_rechts.set_value(nabe.flanschabstand_rechts)
        self.speichenloch.set_value(nabe.speichenloch)
        self.flanschdicke.set_value(nabe.flanschdicke)
        self._nabenart = nabe.art
        self._nabenaufnahme = nabe.aufnahme

        self.erd.set_value(felge.erd)
        self.versatz.set_value(felge.versatz)
        # Ein gespeicherter Typ kann aus einer anderen Kategorie stammen –
        # dafür erst den Filter aufheben, sonst steht er nicht in der Liste.
        if felge.typ and felgenkunde.finde(felge.typ) is not None:
            self._felgenkategorie = ""
            self.felgenkategorie.set_active_id("")
            self._felgentypen_fuellen()
        self.felgentyp.set_active_id(felge.typ if felgenkunde.finde(felge.typ) else "")
        self._felgeninfo_setzen()

        self.speichenzahl.set_value(einspeichung.speichenzahl)
        if einspeichung.verteilung in VERTEILUNGEN:
            self.verteilung.set_active_id(einspeichung.verteilung)
        self.kreuzungen_links.set_value(einspeichung.kreuzungen_links)
        self.kreuzungen_rechts.set_value(einspeichung.kreuzungen_rechts)
        gleich = einspeichung.kreuzungen_links == einspeichung.kreuzungen_rechts
        self.gekoppelt.set_active(gleich)
        self.kreuzungen_rechts.set_sensitive(not gleich)

        self._eigene_bauart = speichen.eigene_bauart
        self._e_modul = speichen.e_modul
        self.bauart.set_active_id(speichen.bauart)
        if self.bauart.get_active_id() is None:
            self.bauart.set_active_id(BAUARTEN[1].name)
        self.spannung.set_value(speichen.spannung)
        self.weitung.set_value(speichen.weitung)
        # Passt der Abzug zur Länge, zeigt die Liste die Länge; sonst „eigener
        # Abzug", damit ein von Hand eingetragener Wert nicht überschrieben wird.
        laenge = speichen.nippellaenge
        if laenge in NIPPEL_LAENGEN and abs(nippel_abzug(laenge)
                                            - speichen.nippel_verkuerzung) < 0.01:
            self.nippellaenge.set_active_id(str(laenge))
            self.nippel_korrektur.set_sensitive(False)
        else:
            self.nippellaenge.set_active_id(EIGENER_ABZUG)
            self.nippel_korrektur.set_sensitive(True)
        self.nippel_korrektur.set_value(speichen.nippel_verkuerzung)
        self.unterlegscheibe.set_value(speichen.unterlegscheibe)
        self.straightpull.set_active(speichen.straightpull)
        if speichen.kopf in KOPFLAGEN:
            self.kopf.set_active_id(speichen.kopf)
        self.korrektur_anwenden.set_active(speichen.korrektur_anwenden)

        if schritt in RUNDUNGSSCHRITTE:
            self.rundung.set_active_id(str(schritt))

        self.nabe_vorlage.waehle(nabe.name)
        self.felge_vorlage.waehle(felge.name)

        self._stumm = False
        self._melde()

    def zuruecksetzen(self) -> None:
        """Setzt das Formular auf die Vorgabewerte zurück."""
        self.setze_werte(Nabe(), Felge(), Einspeichung(), Speichensatz(), 1.0)
