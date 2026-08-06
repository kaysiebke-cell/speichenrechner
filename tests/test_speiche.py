"""Tests zur Speiche: Dehnung, Gewicht, Ton – und ein Abgleich mit Spokomat.

Der Abgleich prüft die Geometrie gegen ein durchgerechnetes Beispiel aus dem
Spokomat (Novatec D712SB-AA 135 mm Disc, DT Super Comp, 3-fach, 2×16 Speichen,
ERD 544 mm). Damit ist sichergestellt, dass die Formel dieselben Längen liefert
wie ein etablierter Rechner.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

from speichenrechner import berechnung, speiche  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe, Speichensatz  # noqa: E402

SPOKOMAT_NABE = Nabe("Spokomat-Beispiel", 58.0, 49.0, 36.2, 22.2, 2.5)
SPOKOMAT_FELGE = Felge("Spokomat-Beispiel", 544.0)
SPOKOMAT_EINSPEICHUNG = Einspeichung(32, 3, 3)


class TestAbgleichSpokomat(unittest.TestCase):
    def test_speichenlaengen(self):
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        self.assertAlmostEqual(ergebnis.links.laenge, 263.51, places=2)
        self.assertAlmostEqual(ergebnis.rechts.laenge, 263.28, places=2)

    def test_lateraler_winkel(self):
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        self.assertAlmostEqual(ergebnis.links.speichenwinkel, 7.9, places=1)
        self.assertAlmostEqual(ergebnis.rechts.speichenwinkel, 4.8, places=1)

    def test_spannungsanteil(self):
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        # Spokomat nennt 61,27 % – der Rest ist dessen Luftdruck-Abzug.
        self.assertAlmostEqual(ergebnis.spannung_links_prozent, 61.3, delta=0.2)
        self.assertAlmostEqual(ergebnis.spannung_rechts_prozent, 100.0, places=1)

    def test_nabenmasse_aus_einbaubreite(self):
        links, rechts = berechnung.flanschabstand_aus_einbaubreite(135.0, 31.3, 45.3)
        self.assertAlmostEqual(links, 36.2, places=2)
        self.assertAlmostEqual(rechts, 22.2, places=2)

    def test_steifigkeit_mittelteil(self):
        """E·A/l des Mittelteils – Spokomat nennt 1788,1 N/mm."""
        bauart = speiche.bauart_nach_name("2,0/1,7/1,8 dreifach konifiziert")
        laenge_mitte, flaeche_mitte = speiche.abschnitte(bauart, 263.51)[2]
        steifigkeit = speiche.E_MODUL * flaeche_mitte / laenge_mitte
        self.assertAlmostEqual(steifigkeit, 1788.1, delta=1.0)

    def test_dehnung_der_enden(self):
        """Spokomat nennt 0,05 mm für die verdickten Enden bei 707,67 N."""
        bauart = speiche.bauart_nach_name("2,0/1,7/1,8 dreifach konifiziert")
        enden = sum(
            707.67 / speiche.E_MODUL * laenge / flaeche
            for laenge, flaeche in speiche.abschnitte(bauart, 263.51)[:2]
        )
        self.assertAlmostEqual(enden, 0.05, places=2)


class TestDehnung(unittest.TestCase):
    def test_ohne_spannung_keine_dehnung(self):
        bauart = speiche.BAUARTEN[1]
        self.assertEqual(speiche.dehnung(bauart, 290.0, 0.0), 0.0)

    def test_duennere_mitte_dehnt_mehr(self):
        dick = speiche.bauart_nach_name("2,0 mm durchgehend (14 G)")
        duenn = speiche.bauart_nach_name("2,0/1,5/2,0 sehr leicht")
        self.assertLess(
            speiche.dehnung(dick, 290.0, 1000.0), speiche.dehnung(duenn, 290.0, 1000.0)
        )

    def test_dehnung_waechst_linear_mit_der_spannung(self):
        bauart = speiche.BAUARTEN[1]
        einfach = speiche.dehnung(bauart, 290.0, 500.0)
        doppelt = speiche.dehnung(bauart, 290.0, 1000.0)
        self.assertAlmostEqual(doppelt, 2 * einfach, places=6)

    def test_kurze_speiche_bleibt_gueltig(self):
        """Auch bei 30 mm dürfen keine negativen Abschnitte entstehen."""
        bauart = speiche.BAUARTEN[1]
        for laenge, flaeche in speiche.abschnitte(bauart, 30.0):
            self.assertGreaterEqual(laenge, 0.0)
            self.assertGreater(flaeche, 0.0)


class TestGewichtUndTon(unittest.TestCase):
    def test_gewicht_plausibel(self):
        """Eine 260-mm-Speiche wiegt rund 5 g."""
        bauart = speiche.bauart_nach_name("2,0/1,7/1,8 dreifach konifiziert")
        self.assertAlmostEqual(speiche.masse(bauart, 260.0), 4.8, delta=0.3)

    def test_hoehere_spannung_klingt_hoeher(self):
        bauart = speiche.BAUARTEN[1]
        self.assertLess(
            speiche.frequenz(bauart, 290.0, 800.0), speiche.frequenz(bauart, 290.0, 1200.0)
        )

    def test_frequenz_folgt_der_wurzel(self):
        """Vierfache Spannung heißt doppelte Frequenz."""
        bauart = speiche.BAUARTEN[1]
        self.assertAlmostEqual(
            speiche.frequenz(bauart, 290.0, 1600.0),
            2 * speiche.frequenz(bauart, 290.0, 400.0),
            places=6,
        )

    def test_notennamen(self):
        self.assertEqual(speiche.note(440.0), "a¹")
        self.assertEqual(speiche.note(261.63), "c¹")
        self.assertEqual(speiche.note(880.0), "a²")
        self.assertEqual(speiche.note(0.0), "")


class TestKorrektur(unittest.TestCase):
    def test_korrektur_verkuerzt_die_bestelllaenge(self):
        satz = Speichensatz(korrektur_anwenden=True)
        ohne = berechnung.berechne(Nabe(), Felge(), Einspeichung(), 0.5)
        mit = berechnung.berechne(Nabe(), Felge(), Einspeichung(), 0.5, satz)
        self.assertLessEqual(mit.links.laenge_gerundet, ohne.links.laenge_gerundet)
        self.assertAlmostEqual(mit.links.laenge, ohne.links.laenge, places=9)

    def test_korrektur_setzt_sich_zusammen(self):
        satz = Speichensatz(korrektur_anwenden=True, weitung=0.1, nippel_verkuerzung=0.5)
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung(), 1.0, satz)
        self.assertAlmostEqual(
            ergebnis.links.korrektur, ergebnis.links.dehnung + 0.6, places=9
        )

    def test_ohne_speichensatz_bleibt_die_geometrie(self):
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung())
        self.assertEqual(ergebnis.links.dehnung, 0.0)
        self.assertEqual(ergebnis.links.frequenz, 0.0)


if __name__ == "__main__":
    unittest.main()


class TestZusatzgroessen(unittest.TestCase):
    """Winkel an der Felge, Lochabstand, Straightpull, Kopflage, Scheiben."""

    def test_felgenwinkel_wie_spokomat(self):
        """Spokomat nennt Winkel beta 5,9° links und 4,9° rechts."""
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        self.assertAlmostEqual(ergebnis.links.felgenwinkel, 5.9, delta=0.1)
        self.assertAlmostEqual(ergebnis.rechts.felgenwinkel, 4.9, delta=0.1)

    def test_delta_ist_alpha_plus_beta(self):
        """Spokomat nennt delta = 73,4° als Summe aus alpha und beta."""
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        summe = ergebnis.links.sehnenwinkel + ergebnis.links.felgenwinkel
        self.assertAlmostEqual(summe, 73.4, delta=0.1)

    def test_radial_hat_keinen_felgenwinkel(self):
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung(32, 0, 0))
        self.assertAlmostEqual(ergebnis.links.felgenwinkel, 0.0, places=9)

    def test_lochabstand(self):
        """Umfang des Lochkreises geteilt durch die Speichen dieser Seite."""
        self.assertAlmostEqual(berechnung.lochabstand(58.0, 16), math.pi * 58.0 / 16.0)
        ergebnis = berechnung.berechne(SPOKOMAT_NABE, SPOKOMAT_FELGE, SPOKOMAT_EINSPEICHUNG)
        self.assertAlmostEqual(ergebnis.links.lochabstand, 11.39, places=2)

    def test_straightpull_ohne_lochabzug(self):
        """Ohne Bogen entfällt der Abzug für das halbe Speichenloch."""
        mit_bogen = berechnung.berechne(Nabe(), Felge(), Einspeichung())
        gerade = berechnung.berechne(
            Nabe(), Felge(), Einspeichung(), 1.0, Speichensatz(straightpull=True)
        )
        self.assertAlmostEqual(gerade.links.laenge - mit_bogen.links.laenge, 1.3, places=9)

    def test_straightpull_ohne_bogenweitung(self):
        satz = Speichensatz(korrektur_anwenden=True, straightpull=True, weitung=0.1)
        ergebnis = berechnung.berechne(Nabe(), Felge(), Einspeichung(), 1.0, satz)
        self.assertAlmostEqual(ergebnis.links.korrektur, ergebnis.links.dehnung, places=9)

    def test_kopflage_verschiebt_beide_seiten(self):
        """Alle Köpfe innen rückt den Ansatzpunkt um die halbe Flanschdicke nach rechts."""
        nabe = Nabe("Test", 45.0, 45.0, 35.0, 20.0, 2.6, flanschdicke=3.2)
        gemischt = berechnung.berechne(nabe, Felge(), Einspeichung(), 1.0, Speichensatz())
        innen = berechnung.berechne(
            nabe, Felge(), Einspeichung(), 1.0, Speichensatz(kopf="innen")
        )
        aussen = berechnung.berechne(
            nabe, Felge(), Einspeichung(), 1.0, Speichensatz(kopf="außen")
        )
        # Links wächst der wirksame Abstand, die Speiche wird länger.
        self.assertGreater(innen.links.laenge, gemischt.links.laenge)
        self.assertLess(aussen.links.laenge, gemischt.links.laenge)

    def test_unterlegscheibe_vergroessert_den_erd(self):
        """0,5 mm Scheibe je Seite heißt 1 mm mehr ERD."""
        ohne = berechnung.berechne(Nabe(), Felge(), Einspeichung(), 1.0, Speichensatz())
        mit = berechnung.berechne(
            Nabe(), Felge(), Einspeichung(), 1.0, Speichensatz(unterlegscheibe=0.5)
        )
        groesserer_erd = berechnung.berechne(
            Nabe(), Felge("dicker", 601.0), Einspeichung(), 1.0, Speichensatz()
        )
        self.assertAlmostEqual(mit.links.laenge, groesserer_erd.links.laenge, places=9)
        self.assertGreater(mit.links.laenge, ohne.links.laenge)

    def test_eigene_bauart(self):
        eigene = {"durchmesser_mitte": 1.5, "laenge_kopf": 10.0, "laenge_unten": 10.0}
        bauart = speiche.bauart_nach_name(speiche.EIGENE_BAUART, eigene)
        self.assertAlmostEqual(bauart.durchmesser_mitte, 1.5)
        self.assertAlmostEqual(bauart.laenge_kopf, 10.0)
        # Fehlende Angaben kommen aus der Vorgabe.
        self.assertAlmostEqual(bauart.durchmesser_kopf, 2.0)

    def test_e_modul_wirkt_umgekehrt_proportional(self):
        bauart = speiche.BAUARTEN[1]
        weich = speiche.dehnung(bauart, 290.0, 1000.0, 90_000.0)
        steif = speiche.dehnung(bauart, 290.0, 1000.0, 180_000.0)
        self.assertAlmostEqual(weich, 2 * steif, places=9)

    def test_drahtspannung(self):
        bauart = speiche.bauart_nach_name("2,0/1,7/1,8 dreifach konifiziert")
        self.assertAlmostEqual(
            speiche.drahtspannung(bauart, 1200.0), 1200.0 / bauart.flaeche_mitte, places=6
        )
