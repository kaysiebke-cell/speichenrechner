"""Rechte Spalte: Ergebnisanzeige.

Oben die Speichenlängen und was zu bestellen ist, darunter das
Spannungsverhältnis, textuelle Messwerte und der Vergleich, die fachliche
Einschätzung und zuletzt die Warnungen zur Eingabe.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from ..formatierung import grad, zahl
from ..modelle import Einspeichung, Ergebnis, Felge, Nabe, SeitenErgebnis, Speichensatz
from ..speiche import note
from . import widgets
from .messen import MessAnsicht
from .vergleich import Kreuzungsvergleich


class SeitenKarte(Gtk.Frame):
    """Große Anzeige der Speichenlänge einer Seite."""

    def __init__(self, titel: str) -> None:
        super().__init__()
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        kasten.set_border_width(widgets.RAND)
        self.add(kasten)

        kopf = Gtk.Label(label=titel.upper(), xalign=0.5)
        kopf.get_style_context().add_class("ergebnis-seite")
        kopf.get_style_context().add_class("dim-label")
        kasten.pack_start(kopf, False, False, 0)

        zahlzeile = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        zahlzeile.set_halign(Gtk.Align.CENTER)
        self.zahl = Gtk.Label(label="–")
        self.zahl.get_style_context().add_class("ergebnis-zahl")
        einheit = Gtk.Label(label="mm")
        einheit.get_style_context().add_class("ergebnis-einheit")
        einheit.get_style_context().add_class("dim-label")
        einheit.set_valign(Gtk.Align.END)
        zahlzeile.pack_start(self.zahl, False, False, 0)
        zahlzeile.pack_start(einheit, False, False, 0)
        kasten.pack_start(zahlzeile, False, False, 0)

        self.details = Gtk.Label(xalign=0.5)
        self.details.get_style_context().add_class("dim-label")
        self.details.get_style_context().add_class("klein")
        self.details.set_justify(Gtk.Justification.CENTER)
        kasten.pack_start(self.details, False, False, 0)

    def aktualisiere(self, seite: SeitenErgebnis) -> None:
        self.zahl.set_text(zahl(seite.laenge_gerundet))
        self.details.set_text(
            f"exakt {zahl(seite.laenge, 2)} mm\n"
            f"{seite.speichen} Speichen · {seite.kreuzungen}-fach\n"
            f"Nabe {grad(seite.speichenwinkel)} · Felge {grad(seite.felgenwinkel)}"
        )

    def leeren(self) -> None:
        self.zahl.set_text("–")
        self.details.set_text("")


class ErgebnisBereich(Gtk.Box):
    """Ergebniskarten, Spannungsverhältnis, Text-Messwerte, Einschätzung, Hinweise."""

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)

        self.karte_links = SeitenKarte("links")
        self.karte_rechts = SeitenKarte("rechts")

        # Die große Speichenlängen-Anzeige wird jetzt vom Hauptfenster
        # oberhalb der Tab-Leiste dargestellt.
        self.bestellung = Gtk.Label(xalign=0.5)
        self.bestellung.set_line_wrap(True)
        self.bestellung.set_width_chars(20)

        # Die Zusatzansichten werden vom Hauptfenster in die gemeinsame
        # Tab-Leiste eingesetzt. Die Spannungsanzeige wird dabei unter
        # „Speichen“ eingehängt; rechts bleiben nur die eigentlichen Ergebnisse.
        self.messen, self.tabelle, self.spannung_ansicht, self.bewertung_ansicht = self._baue_ansichten()

        # Der Hinweisbereich wird vom Hauptfenster links unter den Tabs
        # eingehängt und deshalb hier nicht selbst gepackt.
        self.hinweis_kasten = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4,
        )

    def kurzanzeige(self) -> Gtk.Widget:
        """Speichenlängen-Anzeige für oberhalb der Tab-Leiste."""
        kasten = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=widgets.ABSTAND,
        )

        karten = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=widgets.ABSTAND,
        )
        karten.set_homogeneous(True)
        karten.pack_start(self.karte_links, True, True, 0)
        karten.pack_start(self.karte_rechts, True, True, 0)

        kasten.pack_start(karten, False, False, 0)
        kasten.pack_start(self.bestellung, False, False, 0)

        return kasten

    def _baue_spannung(self) -> Gtk.Frame:
        rahmen, raster = widgets.abschnitt("Spannungsverhältnis")
        raster.set_column_spacing(widgets.ABSTAND)

        self.spannung_balken = {}
        self.spannung_text = {}
        for reihe, seite in enumerate(("links", "rechts")):
            raster.attach(Gtk.Label(label=seite, xalign=0.0), 0, reihe, 1, 1)

            balken = Gtk.LevelBar()
            balken.set_min_value(0.0)
            balken.set_max_value(100.0)
            balken.set_value(100.0)
            balken.set_hexpand(True)
            balken.set_valign(Gtk.Align.CENTER)
            raster.attach(balken, 1, reihe, 1, 1)
            self.spannung_balken[seite] = balken

            text = Gtk.Label(label="100 %", xalign=1.0)
            text.set_width_chars(6)
            text.get_style_context().add_class("dim-label")
            raster.attach(text, 2, reihe, 1, 1)
            self.spannung_text[seite] = text

        return rahmen

    def _baue_speichenwerte(self) -> Gtk.Frame:
        """Dehnung und Speichenton – beides hängt an der Bauart und Spannung."""
        rahmen, raster = widgets.abschnitt("Speiche unter Spannung")

        self.speichen_zeilen = {}
        for reihe, seite in enumerate(("links", "rechts")):
            raster.attach(Gtk.Label(label=seite, xalign=0.0), 0, reihe, 1, 1)
            wert = Gtk.Label(xalign=0.0)
            wert.set_hexpand(True)
            # Die Zeile trägt Kraft, Dehnung und Ton hintereinander. Ohne
            # Umbruch verlangte sie 557 px und schnitt damit den ganzen Reiter
            # rechts ab – der Abschnitt stammt aus der breiten Ergebnisspalte.
            wert.set_line_wrap(True)
            wert.set_width_chars(20)
            wert.set_max_width_chars(30)
            raster.attach(wert, 1, reihe, 1, 1)
            self.speichen_zeilen[seite] = wert

        fussnote = Gtk.Label(xalign=0.0)
        fussnote.set_line_wrap(True)
        fussnote.set_width_chars(22)
        fussnote.set_max_width_chars(50)
        fussnote.set_text(
            "Der Ton gilt für die ganze, frei schwingende Speiche. Am fertigen "
            "Laufrad klingt nur der Abschnitt zwischen letzter Kreuzung und "
            "Nippel – der ist kürzer und klingt höher. Zum Einstellen bleibt ein "
            "Tensiometer die verlässlichere Wahl."
        )
        fussnote.get_style_context().add_class("dim-label")
        fussnote.get_style_context().add_class("klein")
        raster.attach(fussnote, 0, 2, 2, 1)

        return rahmen

    def baue_messen_vergleich(self) -> Gtk.Widget:
        """„Messen“ und „Vergleich“ auf einer Seite – ein Reiter weniger.

        Seit die Skizzen weg sind, ist „Messen“ nur noch ein halbes Dutzend
        Zeilen Text. Ein eigener Reiter dafür kostet mehr Platz in der Leiste,
        als er an Übersicht bringt. Beide Ansichten behalten ihre Überschrift,
        damit man weiß, was man vor sich hat.
        """
        # Der Rand sitzt jetzt am gemeinsamen Kasten, nicht mehr an beiden
        # Ansichten einzeln – sonst stünde alles doppelt eingerückt.
        self.messen.set_border_width(widgets.ABSTAND)
        self.tabelle.set_border_width(widgets.ABSTAND)

        oben = widgets.rahmen("Messen")
        oben.add(self.messen)
        unten = widgets.rahmen("Kreuzungen im Vergleich")
        unten.add(self.tabelle)
        return self._rollbar(oben, unten)

    def _baue_ansichten(self) -> tuple[Gtk.Widget, Gtk.Widget, Gtk.Widget, Gtk.Widget]:
        """Erzeugt die vier Zusatzseiten für die gemeinsame Tab-Leiste."""
        messen = MessAnsicht()
        tabelle = Kreuzungsvergleich()
        spannung = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)
        # Kein eigener Rand: die Anzeige hängt in der Speichen-Seite, und die
        # hat schon einen. Zweimal eingerückt bliebe weniger Platz für die
        # Werte selbst.
        spannung.pack_start(self._baue_spannung(), False, False, 0)
        spannung.pack_start(self._baue_speichenwerte(), False, False, 0)
        bewertung = self._rollbar(self._baue_einschaetzung())
        return messen, tabelle, spannung, bewertung

    @staticmethod
    def _rollbar(*abschnitte: Gtk.Widget) -> Gtk.Widget:
        kasten = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=widgets.ABSTAND)
        kasten.set_border_width(widgets.RAND)
        for eintrag in abschnitte:
            kasten.pack_start(eintrag, False, False, 0)

        rollbar = Gtk.ScrolledWindow()
        rollbar.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # Die natürliche Breite durchreichen: sonst verlangt die Seite nur 240
        # px, und Tabelle wie Einschätzung stehen halb außerhalb.
        rollbar.set_propagate_natural_width(True)
        rollbar.set_overlay_scrolling(False)
        rollbar.set_min_content_width(240)
        rollbar.add(kasten)
        return rollbar

    def _baue_einschaetzung(self) -> Gtk.Widget:
        self.einschaetzung_text = Gtk.Label(xalign=0.0)
        self.einschaetzung_text.set_line_wrap(True)
        self.einschaetzung_text.set_width_chars(24)
        self.einschaetzung_text.set_max_width_chars(52)
        self.einschaetzung_text.get_style_context().add_class("klein")
        return self.einschaetzung_text

    # ---------------------------------------------------------- Aktualisieren

    def zeige(
        self,
        nabe: Nabe,
        felge: Felge,
        einspeichung: Einspeichung,
        ergebnis: Ergebnis,
        schritt: float = 1.0,
        speichen: Speichensatz | None = None,
    ) -> None:
        self.karte_links.aktualisiere(ergebnis.links)
        self.karte_rechts.aktualisiere(ergebnis.rechts)
        self.bestellung.set_markup(
            "Zu bestellen: <b>" + "</b>   ·   <b>".join(ergebnis.einkaufsliste) + "</b>"
        )

        for seite, prozent in (("links", ergebnis.spannung_links_prozent),
                               ("rechts", ergebnis.spannung_rechts_prozent)):
            self.spannung_balken[seite].set_value(max(0.0, min(100.0, prozent)))
            self.spannung_text[seite].set_text(f"{prozent:.0f} %")

        for seite, wert in (("links", ergebnis.links), ("rechts", ergebnis.rechts)):
            if wert.frequenz > 0:
                klang = note(wert.frequenz)
                self.speichen_zeilen[seite].set_markup(
                    f"{wert.spannung:.0f} N   ·   Dehnung {zahl(wert.dehnung, 2)} mm"
                    f"   ·   Ton {wert.frequenz:.0f} Hz"
                    f" <span size=\"small\">({klang})</span>"
                    f"   ·   {zahl(wert.gewicht, 1)} g je Speiche"
                )
            else:
                self.speichen_zeilen[seite].set_text("–")

        self.messen.setze_daten(nabe, felge)
        self.tabelle.zeige(nabe, felge, einspeichung, schritt, speichen)

        self.einschaetzung_text.set_text("\n".join(f"• {t}" for t in ergebnis.bewertungen))
        self._zeige_hinweise(ergebnis.hinweise)

    def zeige_fehler(self, meldung: str) -> None:
        self.karte_links.leeren()
        self.karte_rechts.leeren()
        self.bestellung.set_text("")
        self.einschaetzung_text.set_text("")
        self._zeige_hinweise([meldung], Gtk.MessageType.ERROR)

    def _zeige_hinweise(
        self, hinweise: list[str], art: Gtk.MessageType = Gtk.MessageType.WARNING
    ) -> None:
        for kind in self.hinweis_kasten.get_children():
            kind.destroy()

        for hinweis in hinweise:
            leiste = Gtk.InfoBar()
            leiste.set_message_type(art)
            leiste.set_show_close_button(False)
            label = Gtk.Label(label=hinweis, xalign=0.0)
            label.set_line_wrap(True)
            label.set_width_chars(22)
            label.set_max_width_chars(52)
            leiste.get_content_area().add(label)
            self.hinweis_kasten.pack_start(leiste, False, False, 0)

        self.hinweis_kasten.show_all()
