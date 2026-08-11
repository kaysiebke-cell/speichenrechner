"""Tests der Bauform: was aus Bauart und Ritzelaufnahme folgt.

Die Ableitung steckt in :mod:`speichenrechner.modelle` und läuft ohne GTK.
Geprüft wird nur das Modell – die gezeichneten Naben gibt es nicht mehr.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

from speichenrechner import berechnung, vorlagen  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
