"""Tests zum Platzbedarf der Eingabespalte.

Die Eingabespalte ist schon zweimal zu breit oder zu hoch geworden – einmal
durch die gleich breiten Knöpfe eines ``StackSwitcher``, einmal durch einen
neuen Abschnitt mit umbrechender Beschreibung. Beides fiel erst am laufenden
Fenster auf. Diese Tests prüfen es vorher.

Sie brauchen GTK und eine Anzeige. Fehlt beides, werden sie übersprungen –
der übrige Testlauf bleibt davon unberührt.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))


def _gtk_bereit():
    """True, wenn sich GTK öffnen lässt – sonst laufen diese Tests nicht."""
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        return Gtk.init_check([])[0]
    except Exception:
        return False


GTK_DA = _gtk_bereit()


@unittest.skipUnless(GTK_DA, "GTK oder Anzeige fehlt")
class TestEingabebreite(unittest.TestCase):
    """Kein Abschnitt darf die Spalte breiter machen als die Eingabefelder."""

    def setUp(self):
        from gi.repository import Gtk

        from speichenrechner.modelle import Einspeichung, Felge, Nabe, Speichensatz
        from speichenrechner.ui.eingabe import EingabeBereich

        self.Felge = Felge
        self._standard = (Nabe(), Einspeichung(), Speichensatz())

        self.eingabe = EingabeBereich()
        fenster = Gtk.OffscreenWindow()
        kasten = Gtk.Box()
        kasten.pack_start(self.eingabe, True, True, 0)
        fenster.add(kasten)
        fenster.show_all()
        self._fenster = fenster

    def tearDown(self):
        self._fenster.destroy()

    def _setze(self, typ: str) -> None:
        nabe, einspeichung, speichen = self._standard
        self.eingabe.setze_werte(
            nabe, self.Felge("Prüffelge", 600.0, 0.0, typ), einspeichung, speichen, 1.0
        )

    def _breite(self) -> int:
        return self.eingabe.get_preferred_width().natural_width

    def _hoehe(self) -> int:
        seite = self.eingabe.mappe.get_nth_page(0).get_child()
        return seite.get_preferred_height().natural_height

    def test_felgentyp_macht_die_spalte_nicht_breiter(self):
        """Der längste Beschreibungstext darf die Spaltenbreite nicht bestimmen.

        Sonst wandert die Trennlinie nach rechts und die Ergebnisse werden
        abgeschnitten – genau der Fehler, der schon zweimal auftrat.
        """
        self._setze("")
        ohne = self._breite()
        for typ in ("Flachbettfelge", "Hakenlose Felge (Hookless/TSS)",
                    "Schlauchreifenfelge (Tubular)", "Trekking-/City-Felge"):
            with self.subTest(typ=typ):
                self._setze(typ)
                self.assertEqual(self._breite(), ohne)

    def test_beschreibung_bestimmt_die_breite_nicht(self):
        """Die umbrechende Zeile richtet sich nach der Spalte, nicht umgekehrt."""
        self._setze("Flachbettfelge")
        self.assertLess(
            self.eingabe.felgeninfo.get_preferred_width().natural_width,
            self._breite(),
        )

    def test_beschreibung_belegt_ohne_typ_keinen_platz(self):
        """Ohne gewählten Typ ist die Zeile weg – und der Abschnitt so hoch wie zuvor."""
        self._setze("")
        self.assertFalse(self.eingabe.felgeninfo.get_visible())
        leer = self._hoehe()

        self._setze("Flachbettfelge")
        self.assertTrue(self.eingabe.felgeninfo.get_visible())
        self.assertGreater(self._hoehe(), leer)

        self._setze("")
        self.assertFalse(self.eingabe.felgeninfo.get_visible())
        self.assertEqual(self._hoehe(), leer)

    def test_filter_nennen_ihre_anzahl(self):
        """In den Filterlisten steht, wie viele Naben die Tabelle dazu führt.

        Ohne die Zahl sieht „Schraubkranz“ mit sechs Naben wie ein Fehler des
        Filters aus. Die Zahl muss zur Auswahlliste passen.
        """
        from speichenrechner import katalog

        combo = self.eingabe.nabenart
        beschriftungen = {}
        for nummer in range(combo.get_model().iter_n_children(None)):
            combo.set_active(nummer)
            beschriftungen[combo.get_active_id()] = combo.get_active_text()

        for art, anzahl in katalog.lade().arten_mit_anzahl():
            with self.subTest(art=art):
                self.assertIn(f"({anzahl})", beschriftungen[art])

    def test_filterlisten_machen_die_spalte_nicht_breit(self):
        """Lange Herstellernamen dürfen die Eingabespalte nicht aufziehen."""
        for combo in (self.eingabe.nabenart, self.eingabe.nabenhersteller):
            with self.subTest(combo=combo):
                self.assertLess(combo.get_preferred_width().natural_width, 200)

    def test_auswahl_belegt_eine_zeile(self):
        """Filter und Auswahl stehen nebeneinander, nicht übereinander.

        Zwei Zeilen kosteten rund 30 Pixel Höhe, die im Fenster von 720 Pixeln
        der Einspeichung fehlten.
        """
        self._setze("")
        oben = self.eingabe.felgenkategorie.translate_coordinates(self.eingabe, 0, 0)
        neben = self.eingabe.felgentyp.translate_coordinates(self.eingabe, 0, 0)
        self.assertIsNotNone(oben)
        self.assertIsNotNone(neben)
        self.assertEqual(oben[1], neben[1], "Filter und Auswahl liegen nicht in einer Zeile")


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(GTK_DA, "GTK oder Anzeige fehlt")
class TestReiterInhalt(unittest.TestCase):
    """Jeder Reiter muss auch enthalten, was hineingehört.

    Anlass: die Spannungsanzeige wurde in die Speichen-Seite eingehängt, kam
    dort aber nie an. Die Seite ist ein ``Gtk.ScrolledWindow``, und GTK legt
    zwischen ihn und den Kasten selbsttätig ein ``Gtk.Viewport``. Die
    Einhängung suchte nur eine Ebene tief, fand keine ``Gtk.Box`` – und tat
    stillschweigend nichts. Der Reiter blieb halb leer, ohne Fehlermeldung.
    """

    def setUp(self):
        from speichenrechner.ui.hauptfenster import Hauptfenster
        self.Hauptfenster = Hauptfenster

    @staticmethod
    def _alle_kinder(widget):
        from gi.repository import Gtk

        yield widget
        if isinstance(widget, Gtk.Container):
            for kind in widget.get_children():
                yield from TestReiterInhalt._alle_kinder(kind)

    def _fenster(self):
        from gi.repository import Gio, Gtk

        # Das Fenster gehört zu einer Anwendung; ohne sie fehlt ihm der
        # Bezugsrahmen. NON_UNIQUE, damit sich mehrere Tests nicht an
        # derselben Kennung stoßen. Angezeigt wird hier nichts.
        anwendung = Gtk.Application(application_id=None,
                                    flags=Gio.ApplicationFlags.NON_UNIQUE)
        # Weder ``register`` noch ``startup``: zwei anonyme Anwendungen
        # streiten sich um denselben Pfad auf dem Bus, und ``startup`` ohne
        # Registrierung stürzt ab. GTK schreibt dafür eine Warnung ins
        # Protokoll – die stört nur den Testlauf, nicht die Anwendung.
        fenster = self.Hauptfenster(anwendung)
        self.addCleanup(fenster.destroy)
        return fenster

    def test_spannungsanzeige_haengt_im_reiter(self):
        fenster = self._fenster()
        seiten = list(self._alle_kinder(fenster.eingabe.mappe))
        self.assertIn(fenster.ergebnis.spannung_ansicht, seiten,
                      "Die Spannungsanzeige steckt in keinem Reiter")

    def test_messen_und_vergleich_teilen_sich_eine_seite(self):
        fenster = self._fenster()
        mappe = fenster.eingabe.mappe
        beschriftungen = [mappe.get_tab_label_text(mappe.get_nth_page(n))
                          for n in range(mappe.get_n_pages())]
        self.assertNotIn("Messen", beschriftungen)
        self.assertNotIn("Vergleich", beschriftungen)
        self.assertIn("Messen / Vergleich", beschriftungen)

    def test_jede_zusatzansicht_ist_erreichbar(self):
        """Keine der vier Ansichten darf beim Umbau verloren gehen."""
        fenster = self._fenster()
        sichtbar = list(self._alle_kinder(fenster.eingabe.mappe))
        for name in ("messen", "tabelle", "spannung_ansicht", "bewertung_ansicht"):
            with self.subTest(ansicht=name):
                self.assertIn(getattr(fenster.ergebnis, name), sichtbar,
                              f"{name} ist in keinem Reiter zu finden")

    def test_kein_reiter_ist_breiter_als_das_fenster(self):
        """Was in einem Reiter steht, muss in die Startbreite passen.

        Anlass: das Fenster öffnete auf seiner Mindestbreite, während die
        Speichen-Seite 605 px verlangte. Rechts fehlte ein Viertel – die
        Klappliste der Bauart und die Zeile „Speiche unter Spannung“ standen
        außerhalb. Beides stammt aus der früher breiten Ergebnisspalte.
        """
        from gi.repository import Gtk

        fenster = self._fenster()
        fenster.show_all()
        while Gtk.events_pending():
            Gtk.main_iteration()

        platz = fenster.get_preferred_width().natural_width
        m = fenster.eingabe.mappe
        for n in range(m.get_n_pages()):
            seite = m.get_nth_page(n)
            inhalt = seite
            while isinstance(inhalt, Gtk.Bin) and not isinstance(inhalt, Gtk.Box):
                inhalt = inhalt.get_child()
            with self.subTest(reiter=m.get_tab_label_text(seite)):
                self.assertLessEqual(
                    inhalt.get_preferred_width().natural_width, platz,
                    "Der Inhalt verlangt mehr Breite, als das Fenster beim "
                    "Öffnen hergibt – rechts wird abgeschnitten",
                )

    def test_die_seiten_zeigen_ihren_rollbalken(self):
        """Längere Seiten müssen einen sichtbaren Balken haben.

        Mit den eingeblendeten Streifen sieht abgeschnitten aus, was in
        Wahrheit nur weiter unten steht.
        """
        from gi.repository import Gtk

        fenster = self._fenster()
        m = fenster.eingabe.mappe
        for n in range(m.get_n_pages()):
            seite = m.get_nth_page(n)
            if not isinstance(seite, Gtk.ScrolledWindow):
                continue
            with self.subTest(reiter=m.get_tab_label_text(seite)):
                self.assertFalse(seite.get_overlay_scrolling())


@unittest.skipUnless(GTK_DA, "GTK oder Anzeige fehlt")
class TestModellreihenZeile(unittest.TestCase):
    """Die Auswahlliste zeigt Modellreihen, die Ausführung steht darunter.

    Gebaut wird nur der Eingabebereich in einem OffscreenWindow – wie bei
    TestEingabebreite. Ein volles Hauptfenster mit ``show_all`` braucht dafür
    eine halbe Minute und bleibt beim Warten auf Ereignisse hängen.
    """

    def setUp(self):
        from gi.repository import Gtk

        from speichenrechner import katalog
        from speichenrechner.ui.eingabe import EingabeBereich

        self.katalog = katalog
        katalog.neu_laden()
        self.eingabe = EingabeBereich()
        fenster = Gtk.OffscreenWindow()
        kasten = Gtk.Box()
        kasten.pack_start(self.eingabe, True, True, 0)
        fenster.add(kasten)
        fenster.show_all()
        self._fenster = fenster

    def tearDown(self):
        self._fenster.destroy()

    def _reihe(self, mindestens: int, hoechstens: int | None = None):
        for _text, eintraege in self.katalog.als_modellreihen():
            if len(eintraege) >= mindestens and (hoechstens is None
                                                 or len(eintraege) <= hoechstens):
                return eintraege
        self.skipTest(f"keine Reihe mit {mindestens} Ausführungen im Katalog")

    def test_zeile_bleibt_weg_solange_nichts_gewaehlt_ist(self):
        self.assertFalse(self.eingabe.nabenausfuehrung.get_visible())

    def test_zeile_erscheint_nur_bei_mehreren_ausfuehrungen(self):
        self.eingabe._nabe_uebernehmen(None, self._reihe(2))
        self.assertTrue(self.eingabe.nabenausfuehrung.get_visible())

        self.eingabe._nabe_uebernehmen(None, self._reihe(1, 1))
        self.assertFalse(self.eingabe.nabenausfuehrung.get_visible())

    def test_jede_ausfuehrung_traegt_ihre_masse_ein(self):
        reihe = None
        for _text, eintraege in self.katalog.als_modellreihen():
            if len(eintraege) > 2 and all(e.hat_flanschmasse for e in eintraege):
                reihe = eintraege
                break
        if reihe is None:
            self.skipTest("keine Reihe mit mehreren vermaßten Ausführungen")

        self.eingabe._nabe_uebernehmen(None, reihe)
        gesehen = set()
        for nummer in range(len(reihe)):
            self.eingabe.nabenausfuehrung.set_active(nummer)
            gesehen.add((self.eingabe.flansch_a_links.get_value(),
                         self.eingabe.flansch_a_rechts.get_value()))
        self.assertGreater(len(gesehen), 1,
                           "Alle Ausführungen tragen dieselben Maße ein")

    def test_zeile_macht_die_spalte_nicht_breiter(self):
        """Sonst wandert die Spalte nach rechts – der Fehler von letztem Mal."""
        schmal = self.eingabe.get_preferred_width().natural_width
        self.eingabe._nabe_uebernehmen(None, self._reihe(4))
        self.assertLessEqual(self.eingabe.get_preferred_width().natural_width, schmal)

    def test_eine_vorlage_blendet_die_zeile_wieder_aus(self):
        from speichenrechner.modelle import Nabe

        self.eingabe._nabe_uebernehmen(None, self._reihe(2))
        self.assertTrue(self.eingabe.nabenausfuehrung.get_visible())
        self.eingabe._nabe_uebernehmen(None, Nabe(name="Prüfvorlage"))
        self.assertFalse(self.eingabe.nabenausfuehrung.get_visible())
