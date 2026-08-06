"""Tests der mitgelieferten Vorlagen und der Zahlenformatierung."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speichenrechner import berechnung, formatierung, vorlagen  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe  # noqa: E402


class TestVorlagen(unittest.TestCase):
    def test_namen_sind_eindeutig(self):
        namen = [n.name for n in vorlagen.NABEN_VORLAGEN]
        self.assertEqual(len(namen), len(set(namen)))
        namen = [f.name for f in vorlagen.FELGEN_VORLAGEN]
        self.assertEqual(len(namen), len(set(namen)))

    def test_jede_nabe_liefert_plausible_laengen(self):
        felge = Felge("28 Zoll", 600.0)
        for nabe in vorlagen.NABEN_VORLAGEN:
            with self.subTest(nabe=nabe.name):
                ergebnis = berechnung.berechne(nabe, felge, Einspeichung(32, 3, 3))
                for seite in (ergebnis.links, ergebnis.rechts):
                    self.assertTrue(250.0 < seite.laenge < 300.0, seite.laenge)

    def test_herstellernaben_vorhanden(self):
        namen = " ".join(n.name for n in vorlagen.NABEN_VORLAGEN)
        self.assertIn("Rohloff", namen)
        self.assertIn("SON", namen)

    def test_rohloff_ist_symmetrisch_mit_grossem_flansch(self):
        rohloff = next(n for n in vorlagen.NABEN_VORLAGEN if n.name.endswith("(135/142 mm)"))
        self.assertEqual(rohloff.flanschdurchmesser_links, 100.0)
        self.assertEqual(rohloff.flanschabstand_links, rohloff.flanschabstand_rechts)
        self.assertEqual(rohloff.speichenloch, 2.7)

    def test_son_disc_ist_unsymmetrisch(self):
        son = next(n for n in vorlagen.NABEN_VORLAGEN if n.name.startswith("SON 28 Disc"))
        self.assertNotEqual(son.flanschabstand_links, son.flanschabstand_rechts)
        self.assertEqual(son.speichenloch, 2.0)


class TestEigeneVorlagen(unittest.TestCase):
    """Speichern und Löschen in einem eigenen Konfigurationsverzeichnis."""

    def setUp(self):
        self._verzeichnis = tempfile.TemporaryDirectory()
        self._alt = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._verzeichnis.name

    def tearDown(self):
        if self._alt is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._alt
        self._verzeichnis.cleanup()

    def test_speichern_laden_loeschen(self):
        nabe = Nabe("Meine Nabe", 46.0, 44.0, 33.0, 21.0, 2.4)
        vorlagen.speichere_nabe(nabe)

        self.assertTrue(vorlagen.ist_eigene_nabe("Meine Nabe"))
        geladen = next(n for n in vorlagen.alle_naben() if n.name == "Meine Nabe")
        self.assertEqual(geladen, nabe)

        self.assertTrue(vorlagen.loesche_nabe("Meine Nabe"))
        self.assertFalse(vorlagen.ist_eigene_nabe("Meine Nabe"))
        self.assertFalse(vorlagen.loesche_nabe("Meine Nabe"))

    def test_gleicher_name_ueberschreibt(self):
        vorlagen.speichere_felge(Felge("Meine Felge", 601.0))
        vorlagen.speichere_felge(Felge("Meine Felge", 605.0))
        eigene = [f for f in vorlagen.eigene_felgen() if f.name == "Meine Felge"]
        self.assertEqual(len(eigene), 1)
        self.assertEqual(eigene[0].erd, 605.0)

    def test_mitgelieferte_bleiben_erhalten(self):
        vorlagen.speichere_nabe(Nabe("Meine Nabe", 46.0, 44.0, 33.0, 21.0))
        namen = [n.name for n in vorlagen.alle_naben()]
        self.assertIn("Rohloff SPEEDHUB 500/14 (135/142 mm)", namen)
        self.assertEqual(namen[-1], "Meine Nabe")


class TestFormatierung(unittest.TestCase):
    def test_komma_statt_punkt(self):
        self.assertEqual(formatierung.zahl(292.92, 2), "292,92")
        self.assertEqual(formatierung.zahl(293.0), "293,0")
        self.assertEqual(formatierung.zahl(600.0, 0), "600")

    def test_einheiten(self):
        self.assertEqual(formatierung.mm(292.9), "292,9 mm")
        self.assertEqual(formatierung.grad(6.83), "6,8°")


class TestVorlagenfilter(unittest.TestCase):
    """Ein Filter muss auch die mitgelieferten Vorlagen kürzen.

    Sonst stehen beim Filter „Kassette“ weiterhin Dynamos und Getriebenaben
    obenan und der Filter wirkt wirkungslos.
    """

    def test_ohne_filter_alle(self):
        self.assertEqual(len(vorlagen.alle_naben()), len(vorlagen.NABEN_VORLAGEN))

    def test_jede_mitgelieferte_vorlage_hat_eine_art(self):
        for nabe in vorlagen.NABEN_VORLAGEN:
            self.assertTrue(nabe.art, nabe.name)

    def test_filter_kuerzt_die_liste(self):
        gefiltert = vorlagen.alle_naben("Hinterrad")
        self.assertTrue(gefiltert)
        self.assertLess(len(gefiltert), len(vorlagen.NABEN_VORLAGEN))
        for nabe in gefiltert:
            self.assertEqual(nabe.art, "Hinterrad")

    def test_dynamos_enthalten_keine_getriebenaben(self):
        namen = [n.name for n in vorlagen.alle_naben("Dynamo")]
        self.assertTrue(any("SON" in name for name in namen))
        self.assertFalse(any("SPEEDHUB" in name for name in namen))

    def test_unbekannte_art_ergibt_leere_liste(self):
        self.assertEqual(vorlagen.alle_naben("Gibtsnicht"), [])

    def test_arten_passen_zu_denen_des_katalogs(self):
        from speichenrechner import katalog
        bekannt = set(katalog.lade().arten())
        for nabe in vorlagen.NABEN_VORLAGEN:
            self.assertIn(nabe.art, bekannt, nabe.name)


if __name__ == "__main__":
    unittest.main()


class TestVorlagenMerkmale(unittest.TestCase):
    """Vorlagen müssen unter denselben Merkmalen zu finden sein wie Katalognaben.

    Der Tooltip des Filters verspricht: „eine Rohloff findet sich unter
    Nabenschaltung wie unter Schraubritzel“. Vorher galt das nur für den
    Katalog, nicht für die Vorlagen.
    """

    def test_rohloff_steht_unter_beidem(self):
        unter_bauart = [n.name for n in vorlagen.alle_naben("Nabenschaltung")]
        unter_aufnahme = [n.name for n in vorlagen.alle_naben("Schraubritzel")]
        self.assertTrue(any("SPEEDHUB" in name for name in unter_bauart))
        self.assertTrue(any("SPEEDHUB" in name for name in unter_aufnahme))

    def test_schraubkranz_hat_vorlagen(self):
        """Beim Filter „Schraubkranz“ muss ein Startpunkt zur Verfügung stehen.

        Die Herstellertabelle führt dazu nur sechs Naben – ohne Vorlagen wirkte
        der Filter wie ein Fehler.
        """
        namen = [n.name for n in vorlagen.alle_naben("Schraubkranz")]
        self.assertGreaterEqual(len(namen), 3)
        self.assertTrue(any("(typisch)" in name for name in namen))
        self.assertTrue(any("White Industries" in name for name in namen))

    def test_gewindenaben_sind_symmetrisch(self):
        """Ohne Ritzelpaket sitzt der rechte Flansch so weit außen wie der linke.

        Bei den beiden White-Industries-Naben gibt der Hersteller je Seite
        denselben Abstand an – das ist der Prüfstein dafür, dass hier nicht aus
        Gewohnheit eine Kassettengeometrie eingetragen wurde.
        """
        for nabe in vorlagen.alle_naben("Schraubkranz"):
            if "White Industries" not in nabe.name:
                continue
            with self.subTest(nabe=nabe.name):
                self.assertEqual(nabe.flanschabstand_links, nabe.flanschabstand_rechts)
                self.assertEqual(nabe.flanschdurchmesser_links, nabe.flanschdurchmesser_rechts)
                self.assertEqual(nabe.antrieb, "gewinde")

    def test_kassettenvorlagen_erscheinen_unter_kassette(self):
        namen = [n.name for n in vorlagen.alle_naben("Kassette")]
        self.assertTrue(any("Hinterrad 135" in name for name in namen))
        self.assertFalse(any("SPEEDHUB" in name for name in namen))

    def test_vorderrad_nicht_unter_einer_aufnahme(self):
        for merkmal in ("Kassette", "Schraubkranz", "Schraubritzel"):
            with self.subTest(merkmal=merkmal):
                namen = [n.name for n in vorlagen.alle_naben(merkmal)]
                self.assertFalse(any("Vorderrad" in name for name in namen))

    def test_merkmale_ohne_angaben_bleiben_leer(self):
        from speichenrechner.modelle import Nabe
        self.assertEqual(Nabe().merkmale, ())
        self.assertEqual(Nabe(art="Hinterrad").merkmale, ("Hinterrad",))
        self.assertEqual(Nabe(art="Hinterrad", aufnahme="Kassette").merkmale,
                         ("Hinterrad", "Kassette"))
