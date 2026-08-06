"""Tests der Berechnung – laufen ohne GTK.

    python3 -m unittest discover -s tests
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

from speichenrechner import berechnung  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe  # noqa: E402


class TestSpeichenlaenge(unittest.TestCase):
    def test_radial_entspricht_pythagoras(self):
        """Ohne Kreuzung ist die Speiche die Hypotenuse aus Radius- und Seitenversatz."""
        erwartet = math.sqrt((300.0 - 22.5) ** 2 + 35.0**2) - 1.3
        gerechnet = berechnung.speichenlaenge(
            erd=600.0, flanschdurchmesser=45.0, flanschabstand=35.0,
            speichenzahl=32, kreuzungen=0, speichenloch=2.6,
        )
        self.assertAlmostEqual(erwartet, gerechnet, places=9)

    def test_bekannter_wert(self):
        """32 Loch, 3-fach, ERD 600, Flansch 45 mm, Abstand 35 mm."""
        laenge = berechnung.speichenlaenge(600.0, 45.0, 35.0, 32, 3, 2.6)
        self.assertAlmostEqual(laenge, 292.92, places=2)

    def test_mehr_kreuzungen_ergibt_laengere_speiche(self):
        werte = [berechnung.speichenlaenge(600.0, 45.0, 35.0, 32, k) for k in range(4)]
        self.assertEqual(werte, sorted(werte))

    def test_sehnenwinkel(self):
        self.assertAlmostEqual(berechnung.sehnenwinkel(32, 3), 67.5)
        self.assertAlmostEqual(berechnung.sehnenwinkel(36, 3), 60.0)
        self.assertAlmostEqual(berechnung.sehnenwinkel(32, 0), 0.0)

    def test_ungueltige_eingaben(self):
        with self.assertRaises(ValueError):
            berechnung.speichenlaenge(0.0, 45.0, 35.0, 32, 3)
        with self.assertRaises(ValueError):
            berechnung.speichenlaenge(600.0, 0.0, 35.0, 32, 3)
        with self.assertRaises(ValueError):
            berechnung.sehnenwinkel(0, 3)


class TestSpeichenwinkel(unittest.TestCase):
    def test_ohne_versatz_ist_null(self):
        self.assertAlmostEqual(berechnung.speichenwinkel(600.0, 45.0, 0.0, 32, 3), 0.0)

    def test_groesserer_abstand_gibt_groesseren_winkel(self):
        klein = berechnung.speichenwinkel(600.0, 45.0, 20.0, 32, 3)
        gross = berechnung.speichenwinkel(600.0, 45.0, 35.0, 32, 3)
        self.assertLess(klein, gross)
        self.assertTrue(0.0 < gross < 90.0)


class TestRunden(unittest.TestCase):
    def test_schritte(self):
        self.assertAlmostEqual(berechnung.runden(292.92, 1.0), 293.0)
        self.assertAlmostEqual(berechnung.runden(292.92, 0.5), 293.0)
        self.assertAlmostEqual(berechnung.runden(292.20, 0.5), 292.0)
        self.assertAlmostEqual(berechnung.runden(293.10, 2.0), 294.0)


class TestHilfsrechnungen(unittest.TestCase):
    def test_flanschabstand_aus_einbaubreite(self):
        links, rechts = berechnung.flanschabstand_aus_einbaubreite(135.0, 30.5, 48.5)
        self.assertAlmostEqual(links, 37.0)
        self.assertAlmostEqual(rechts, 19.0)

    def test_erd_aus_messung(self):
        self.assertAlmostEqual(berechnung.erd_aus_messung(596.0, 2.0), 600.0)


class TestGesamtberechnung(unittest.TestCase):
    def test_symmetrische_nabe_beide_seiten_gleich(self):
        nabe = Nabe("Test", 45.0, 45.0, 35.0, 35.0)
        ergebnis = berechnung.berechne(nabe, Felge("Test", 600.0), Einspeichung(32, 3, 3))
        self.assertAlmostEqual(ergebnis.links.laenge, ergebnis.rechts.laenge)
        self.assertTrue(ergebnis.symmetrisch)
        self.assertAlmostEqual(ergebnis.spannung_links_prozent, 100.0)
        self.assertAlmostEqual(ergebnis.spannung_rechts_prozent, 100.0)

    def test_hinterrad_rechts_kuerzer_und_geringer_gespannt(self):
        nabe = Nabe("Hinterrad", 45.0, 45.0, 37.0, 19.0)
        ergebnis = berechnung.berechne(nabe, Felge("Test", 600.0), Einspeichung(32, 3, 3))
        self.assertLess(ergebnis.rechts.laenge, ergebnis.links.laenge)
        # Die flacher stehende rechte Seite braucht die hoehere Spannung.
        self.assertAlmostEqual(ergebnis.spannung_rechts_prozent, 100.0)
        self.assertLess(ergebnis.spannung_links_prozent, 100.0)

    def test_felgenversatz_zur_linken_seite_gleicht_spannung_an(self):
        """Beim Hinterrad wird das Speichenbett zur Bremsseite (links) versetzt."""
        nabe = Nabe("Hinterrad", 45.0, 45.0, 37.0, 19.0)
        einspeichung = Einspeichung(32, 3, 3)
        ohne = berechnung.berechne(nabe, Felge("gerade", 600.0, 0.0), einspeichung)
        mit = berechnung.berechne(nabe, Felge("asymmetrisch", 600.0, -4.0), einspeichung)
        differenz_ohne = abs(ohne.spannung_links_prozent - ohne.spannung_rechts_prozent)
        differenz_mit = abs(mit.spannung_links_prozent - mit.spannung_rechts_prozent)
        self.assertLess(differenz_mit, differenz_ohne)

    def test_hinweis_bei_unmoeglicher_kreuzung(self):
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung(16, 4, 4))
        self.assertTrue(any("nicht möglich" in h for h in ergebnis.hinweise))

    def test_hinweis_bei_radial(self):
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung(32, 0, 0))
        self.assertTrue(any("radial" in h for h in ergebnis.hinweise))


if __name__ == "__main__":
    unittest.main()


class TestBestelllaenge(unittest.TestCase):
    """Was zu bestellen ist – und wann gewarnt werden muss.

    157,18 und 156,92 mm sind rechnerisch verschieden, gerundet aber dieselbe
    Speiche. Dann ist es ein Posten und es gibt nichts zu vertauschen.
    """

    def _ergebnis(self, flansch_rechts: float):
        nabe = Nabe("Prüfnabe", 54.0, 54.0, 28.0, flansch_rechts, 2.0)
        felge = Felge("16 Zoll", 328.0)
        return berechnung.berechne(nabe, felge, Einspeichung(32, 3, 3))

    def test_gleiche_bestelllaenge_wird_zusammengefasst(self):
        ergebnis = self._ergebnis(26.5)
        self.assertFalse(ergebnis.symmetrisch)          # exakt verschieden
        self.assertTrue(ergebnis.gleiche_bestelllaenge)  # gerundet gleich
        self.assertEqual(len(ergebnis.einkaufsliste), 1)
        self.assertIn("32 ×", ergebnis.einkaufsliste[0])

    def test_ohne_echten_unterschied_keine_vertauschwarnung(self):
        hinweise = " ".join(self._ergebnis(26.5).hinweise)
        self.assertNotIn("nicht vertauschen", hinweise)

    def test_stattdessen_steht_es_in_der_einschaetzung(self):
        bewertungen = " ".join(self._ergebnis(26.5).bewertungen)
        self.assertIn("ein einziger Satz Speichen", bewertungen)

    def test_bei_zwei_laengen_wird_weiter_gewarnt(self):
        ergebnis = self._ergebnis(18.0)
        self.assertFalse(ergebnis.gleiche_bestelllaenge)
        self.assertEqual(len(ergebnis.einkaufsliste), 2)
        self.assertIn("nicht vertauschen", " ".join(ergebnis.hinweise))


class TestFremdeNabendatenbanken(unittest.TestCase):
    """Umrechnung von „flange offset“ aus fremden Datenbanken.

    Was dort „flange offset“ heißt, ist ab Kontermutter gemessen, nicht ab der
    Nabenmitte: ``flange offset = OLD/2 − Flanschabstand``. Trägt man die Werte
    direkt als Flanschabstand ein, rechnet die App still falsch – deshalb
    stehen hier belegte Beispiele als Prüfstein.
    """

    def test_hope_pro_4_vorderrad(self):
        """Beispiel aus der Anleitung von spokelengthcalculator.com.

        Dort: LFO 30 mm, RFO 16,99 mm bei OLD 100 mm. Ab Nabenmitte ergibt das
        20 / 33 mm – genau die Werte, die auch in der Herstellertabelle für die
        baugleiche Hope Pro 2 Evo stehen.
        """
        links, rechts = berechnung.flanschabstand_aus_einbaubreite(100.0, 30.0, 16.99)
        self.assertAlmostEqual(links, 20.0, places=2)
        self.assertAlmostEqual(rechts, 33.01, places=2)

    def test_hope_pro_4_hinterrad_135(self):
        """Dort: 34,5 / 48,5 bei OLD 135 – ab Mitte 33,0 / 19,0.

        Ab Nabenmitte gelesen wären es 83 mm Flanschabstand in einer 135er
        Nabe, mit der Antriebsseite weiter außen als die Bremsseite. Das ist
        die Probe, an der die Verwechslung auffällt.
        """
        links, rechts = berechnung.flanschabstand_aus_einbaubreite(135.0, 34.5, 48.5)
        self.assertAlmostEqual(links, 33.0, places=2)
        self.assertAlmostEqual(rechts, 19.0, places=2)
        self.assertGreater(links, rechts, "die Antriebsseite muss innen liegen")

    def test_rx100_fh_a550_126(self):
        """Dort: 25,7 / 42,3 bei OLD 126 – ab Mitte 37,3 / 20,7, Abstand 58 mm."""
        links, rechts = berechnung.flanschabstand_aus_einbaubreite(126.0, 25.7, 42.3)
        self.assertAlmostEqual(links, 37.3, places=2)
        self.assertAlmostEqual(rechts, 20.7, places=2)
        self.assertAlmostEqual(links + rechts, 58.0, places=2)

    def test_umrechnung_ist_umkehrbar(self):
        """Die Formel der Quelle ist genau die Umkehrung unserer eigenen."""
        for old, links_aussen, rechts_aussen in ((100.0, 30.0, 17.0), (135.0, 34.5, 48.5),
                                                 (148.0, 39.0, 52.0), (126.0, 25.7, 42.3)):
            with self.subTest(old=old):
                links, rechts = berechnung.flanschabstand_aus_einbaubreite(
                    old, links_aussen, rechts_aussen)
                self.assertAlmostEqual(old / 2 - links, links_aussen, places=6)
                self.assertAlmostEqual(old / 2 - rechts, rechts_aussen, places=6)
