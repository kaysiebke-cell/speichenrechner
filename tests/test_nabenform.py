"""Tests der Bauform: was aus Bauart und Ritzelaufnahme gezeichnet wird.

Die Ableitung steckt in :mod:`speichenrechner.modelle` und läuft ohne GTK.
Die Zeichnung selbst wird nur geprüft, wenn GTK und eine Anzeige da sind.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speichenrechner import berechnung, vorlagen  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe  # noqa: E402


def _gtk_bereit():
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        return Gtk.init_check([])[0]
    except Exception:
        return False


GTK_DA = _gtk_bereit()


class TestAntrieb(unittest.TestCase):
    """Was rechts an der Nabe sitzt."""

    def test_vorderrad_hat_keinen_antrieb(self):
        self.assertEqual(Nabe(art="Vorderrad").antrieb, "keiner")

    def test_dynamo_hat_keinen_antrieb(self):
        self.assertEqual(Nabe(art="Dynamo").antrieb, "keiner")

    def test_bauart_gewinnt_vor_der_aufnahme(self):
        """Ein Dynamo bleibt ohne Antriebsseite, egal was in der Spalte steht.

        Im Katalog trägt ein Dynamo das Merkmal „Vorderrad“; sollte in der
        Freilaufspalte trotzdem etwas stehen, darf daraus kein Freilaufkörper
        werden.
        """
        self.assertEqual(Nabe(art="Dynamo", aufnahme="Kassette").antrieb, "keiner")

    def test_kassette_und_verwandte(self):
        for aufnahme in ("Kassette", "Steckritzel", "Steckzahnkranz"):
            with self.subTest(aufnahme=aufnahme):
                self.assertEqual(Nabe(art="Hinterrad", aufnahme=aufnahme).antrieb, "kassette")

    def test_geschraubte_ritzel(self):
        for aufnahme in ("Schraubkranz", "Schraubritzel", "Singlespeed"):
            with self.subTest(aufnahme=aufnahme):
                self.assertEqual(Nabe(art="Hinterrad", aufnahme=aufnahme).antrieb, "gewinde")

    def test_rohloff_bekommt_ein_gewinde(self):
        """Nabenschaltung mit Schraubritzel: dicke Schale, aber kein Freilaufkörper."""
        rohloff = next(n for n in vorlagen.NABEN_VORLAGEN if "SPEEDHUB" in n.name)
        self.assertEqual(rohloff.antrieb, "gewinde")
        self.assertEqual(rohloff.schale, "gross")

    def test_nabenschaltung_bekommt_nie_einen_kassettenkoerper(self):
        """Bei Getriebenaben sitzt das Ritzel auf einem kurzen Stummel.

        Das gilt auch, wenn die Tabelle „Steckritzel“ nennt oder die
        Freilaufspalte leer bleibt – ein Kassettenkörper wäre in beiden Fällen
        falsch gezeichnet.
        """
        for aufnahme in ("", "Steckritzel", "Kassette", "Schraubritzel"):
            with self.subTest(aufnahme=aufnahme):
                self.assertEqual(Nabe(art="Nabenschaltung", aufnahme=aufnahme).antrieb,
                                 "gewinde")

    def test_ohne_angabe_der_haeufigste_fall(self):
        self.assertEqual(Nabe().antrieb, "kassette")


class TestSchale(unittest.TestCase):
    def test_getriebe_und_generator_brauchen_platz(self):
        self.assertEqual(Nabe(art="Nabenschaltung").schale, "gross")
        self.assertEqual(Nabe(art="Dynamo").schale, "gross")

    def test_kettennabe_bleibt_schlank(self):
        self.assertEqual(Nabe(art="Hinterrad").schale, "normal")
        self.assertEqual(Nabe(art="Vorderrad").schale, "normal")
        self.assertEqual(Nabe().schale, "normal")


class TestBauformAendertDieRechnungNicht(unittest.TestCase):
    """Die Speichenlänge hängt an der Geometrie, nicht an der Bauart."""

    def test_gleiche_geometrie_gleiche_laenge(self):
        felge = Felge("28 Zoll", 600.0)
        einspeichung = Einspeichung(32, 3, 3)
        werte = []
        for art, aufnahme in (("", ""), ("Vorderrad", ""), ("Dynamo", ""),
                              ("Nabenschaltung", "Schraubritzel"),
                              ("Hinterrad", "Kassette")):
            nabe = Nabe("Prüfnabe", 45.0, 45.0, 35.0, 20.0, 2.6, art=art, aufnahme=aufnahme)
            ergebnis = berechnung.berechne(nabe, felge, einspeichung)
            werte.append((ergebnis.links.laenge, ergebnis.rechts.laenge))
        self.assertEqual(len(set(werte)), 1, werte)


class TestVorlagenTragenDieBauform(unittest.TestCase):
    def test_hinterradvorlagen_haben_eine_aufnahme(self):
        for nabe in vorlagen.NABEN_VORLAGEN:
            if nabe.art == "Hinterrad":
                with self.subTest(nabe=nabe.name):
                    self.assertTrue(nabe.aufnahme, "Hinterrad ohne Ritzelaufnahme")

    def test_vorderrad_und_dynamo_ohne_aufnahme(self):
        for nabe in vorlagen.NABEN_VORLAGEN:
            if nabe.art in ("Vorderrad", "Dynamo"):
                with self.subTest(nabe=nabe.name):
                    self.assertEqual(nabe.aufnahme, "")
                    self.assertEqual(nabe.antrieb, "keiner")


@unittest.skipUnless(GTK_DA, "GTK oder Anzeige fehlt")
class TestKontur(unittest.TestCase):
    """Die gezeichnete Kontur muss zur Bauform passen."""

    def setUp(self):
        from speichenrechner.ui import bauteile
        self.bauteile = bauteile

    def _stationen(self, nabe: Nabe, r: float = 22.5):
        return self.bauteile._stationen(
            nabe.flanschabstand_links, nabe.flanschabstand_rechts, r, r,
            nabe.antrieb, nabe.schale,
        )

    def test_vorderrad_ist_kuerzer_als_eine_kassettennabe(self):
        """Ohne Freilaufkörper braucht die Nabe rechts weniger Platz."""
        vorne = self._stationen(Nabe(art="Vorderrad"))
        hinten = self._stationen(Nabe(art="Hinterrad", aufnahme="Kassette"))
        self.assertLess(vorne[-1][0], hinten[-1][0])

    def test_gewinde_ist_schmaler_als_ein_freilaufkoerper(self):
        """Verglichen wird nur die Antriebsseite – der Flansch ist überall gleich groß."""
        def antriebsseite(nabe: Nabe) -> float:
            # Hinter dem Bund am Flanschfuß beginnt erst die Antriebsseite.
            grenze = nabe.flanschabstand_rechts + self.bauteile.GESTALT.freilauf_ab + 0.01
            return max(r for x, r in self._stationen(nabe) if x > grenze)

        gewinde = antriebsseite(Nabe(art="Hinterrad", aufnahme="Schraubkranz"))
        kassette = antriebsseite(Nabe(art="Hinterrad", aufnahme="Kassette"))
        self.assertLess(gewinde, kassette)
        self.assertEqual(kassette, self.bauteile.GESTALT.freilauf)
        self.assertEqual(gewinde, self.bauteile.GEWINDE_RADIUS)

    def test_grosse_schale_ist_dicker(self):
        schmal = self._stationen(Nabe(art="Hinterrad", aufnahme="Kassette"), r=50.0)
        dick = self._stationen(Nabe(art="Nabenschaltung", aufnahme="Schraubritzel"), r=50.0)
        mitte_schmal = min(r for x, r in schmal if abs(x) < 5)
        mitte_dick = min(r for x, r in dick if abs(x) < 5)
        self.assertGreater(mitte_dick, 2 * mitte_schmal)

    def test_koerper_bleibt_unter_dem_flansch(self):
        """Bei kleinem Lochkreis darf der Nabenkörper nicht dicker sein als der Flansch.

        Sonst verschwindet der Flansch im Körper und die Skizze wird falsch.
        """
        for radius in (12.0, 15.0, 22.5, 50.0):
            for nabe in (Nabe(art="Hinterrad", aufnahme="Kassette"),
                         Nabe(art="Nabenschaltung", aufnahme="Schraubritzel"),
                         Nabe(art="Vorderrad")):
                with self.subTest(radius=radius, art=nabe.art):
                    stationen = self._stationen(nabe, r=radius)
                    # Nur der Körper zwischen den Flanschscheiben. Die Scheiben
                    # selbst reichen absichtlich über den Lochkreis hinaus.
                    dicke = self.bauteile.GESTALT.flanschdicke
                    links = -nabe.flanschabstand_links + dicke
                    rechts = nabe.flanschabstand_rechts - dicke
                    innen = [r for x, r in stationen if links < x < rechts]
                    self.assertLess(max(innen), radius, "Körper dicker als der Flansch")


if __name__ == "__main__":
    unittest.main()
