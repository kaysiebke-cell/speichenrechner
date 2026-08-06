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
