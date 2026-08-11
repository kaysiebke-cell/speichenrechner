"""Tests des Nabenkatalogs.

Der Katalog wird aus einer Herstellertabelle erzeugt und liefert nur, was dort
steht – vor allem **nicht** Flanschabstand und Flansch-Ø. Die Tests halten
beides fest: dass die vorhandenen Angaben ankommen, und dass die Suche tut,
was sie soll.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

from speichenrechner import katalog  # noqa: E402


class TestKatalogLaden(unittest.TestCase):
    def setUp(self):
        self.katalog = katalog.lade()

    def test_katalog_ist_gefuellt(self):
        self.assertGreater(len(self.katalog.naben), 150)

    def test_hersteller_vorhanden(self):
        namen = self.katalog.hersteller()
        for erwartet in ("Rohloff", "Shimano", "Hope", "SRAM"):
            self.assertIn(erwartet, namen)
        # SON steht mit Zusatz in der Tabelle – Schreibweise bleibt, wie sie ist.
        self.assertTrue(any(name.startswith("SON") for name in namen))

    def test_eintraege_haben_ein_modell(self):
        for eintrag in self.katalog.naben:
            self.assertTrue(eintrag.modell)

    def test_zahlenfelder_sind_zahlen(self):
        for eintrag in self.katalog.naben:
            for loch in eintrag.lochzahlen:
                self.assertIsInstance(loch, int)
                self.assertTrue(8 <= loch <= 64, f"{eintrag.modell}: {loch}")
            for breite in eintrag.einbaubreiten:
                self.assertTrue(50 <= breite <= 250, f"{eintrag.modell}: {breite}")
            if eintrag.speichenloch_mm is not None:
                self.assertTrue(1.0 <= eintrag.speichenloch_mm <= 5.0)

    def test_bekannte_nabe_mit_ihren_werten(self):
        treffer = [e for e in self.katalog.naben if e.modell == "SON 28"]
        self.assertEqual(len(treffer), 1)
        son = treffer[0]
        self.assertTrue(son.hersteller.startswith("SON"))
        self.assertEqual(son.art, "Dynamo")
        self.assertEqual(son.speichenloch_mm, 2.0)
        self.assertIn(32, son.lochzahlen)
        self.assertIn(100.0, son.einbaubreiten)


class TestSuche(unittest.TestCase):
    def setUp(self):
        self.katalog = katalog.lade()

    def test_leere_suche_liefert_alles(self):
        self.assertEqual(len(self.katalog.suche("")), len(self.katalog.naben))

    def test_suche_ist_unabhaengig_von_gross_und_klein(self):
        self.assertEqual(len(self.katalog.suche("rohloff")), len(self.katalog.suche("ROHLOFF")))

    def test_mehrere_woerter_muessen_alle_passen(self):
        breit = self.katalog.suche("son")
        eng = self.katalog.suche("son disc")
        self.assertLess(len(eng), len(breit))
        for eintrag in eng:
            self.assertIn("disc", eintrag.suchtext)

    def test_nach_hersteller_filtern(self):
        treffer = self.katalog.suche("", "Rohloff")
        self.assertTrue(treffer)
        for eintrag in treffer:
            self.assertEqual(eintrag.hersteller, "Rohloff")

    def test_ohne_treffer_leere_liste(self):
        self.assertEqual(self.katalog.suche("gibtesnicht12345"), [])

    def test_sortierung_nach_hersteller_und_modell(self):
        treffer = self.katalog.suche("hub")
        schluessel = [(e.hersteller.lower(), e.modell.lower()) for e in treffer]
        self.assertEqual(schluessel, sorted(schluessel))


class TestBezeichnung(unittest.TestCase):
    def test_hersteller_wird_nicht_doppelt_genannt(self):
        eintrag = katalog.Katalogeintrag(hersteller="SON", art="", modell="SON 28")
        self.assertEqual(eintrag.bezeichnung, "SON 28")

    def test_hersteller_wird_vorangestellt(self):
        eintrag = katalog.Katalogeintrag(hersteller="Shimano", art="", modell="DH-3N30")
        self.assertEqual(eintrag.bezeichnung, "Shimano DH-3N30")


if __name__ == "__main__":
    unittest.main()


class TestArten(unittest.TestCase):
    """Die Einteilung nach Nabenart macht die lange Liste erst bedienbar."""

    def setUp(self):
        self.katalog = katalog.lade()

    def test_jede_nabe_hat_eine_art(self):
        for eintrag in self.katalog.naben:
            self.assertTrue(eintrag.art, eintrag.modell)

    def test_erwartete_arten(self):
        arten = set(self.katalog.arten())
        for erwartet in ("Dynamo", "Nabenschaltung", "Kassette", "Vorderrad"):
            self.assertIn(erwartet, arten)

    def test_arten_nach_haeufigkeit(self):
        arten = self.katalog.arten()
        anzahl = [len(self.katalog.suche(art=a)) for a in arten]
        self.assertEqual(anzahl, sorted(anzahl, reverse=True))

    def test_vorderradnaben_erkannt(self):
        """Auch Nabendynamos sind Vorderradnaben – sie stehen unter beidem."""
        vorne = self.katalog.suche(art="Vorderrad")
        self.assertGreater(len(vorne), 80)
        for eintrag in vorne:
            self.assertTrue(
                "vorderrad" in eintrag.freilauf.lower()
                or "front" in eintrag.modell.lower(), eintrag.modell)
        self.assertTrue(any(e.art == "Dynamo" for e in vorne))

    def test_nach_art_filtern(self):
        dynamos = self.katalog.suche(art="Dynamo")
        self.assertTrue(dynamos)
        for eintrag in dynamos:
            self.assertIn("Dynamo", eintrag.merkmale)
        self.assertLess(len(dynamos), len(self.katalog.naben))

    def test_liste_laesst_sich_auf_eine_art_beschraenken(self):
        alle = katalog.als_listeneintraege()
        nur_dynamo = katalog.als_listeneintraege("Dynamo")
        self.assertLess(len(nur_dynamo), len(alle))
        for _, eintrag in nur_dynamo:
            self.assertEqual(eintrag.art, "Dynamo")


class TestFlanschmasse(unittest.TestCase):
    """Die Tabelle führt Flanschabstand und Flansch-Ø in einer Spalte je Maß."""

    def setUp(self):
        self.katalog = katalog.lade()

    def _nabe(self, modell: str):
        return next(e for e in self.katalog.naben if e.modell == modell)

    def test_es_gibt_rechenfertige_naben(self):
        fertig = [e for e in self.katalog.naben if e.hat_flanschmasse]
        self.assertGreater(len(fertig), 40)

    def test_gesamtabstand_wird_halbiert(self):
        """„58 (symmetrisch)“ ist der Abstand beider Flansche zusammen."""
        links, rechts = self._nabe("SPEEDHUB 500/14 CC").flanschabstaende
        self.assertAlmostEqual(links, 29.0)
        self.assertAlmostEqual(rechts, 29.0)

    def test_einzelner_durchmesser_gilt_fuer_beide_seiten(self):
        """„Ø100“ heißt 100 mm links wie rechts."""
        links, rechts = self._nabe("SPEEDHUB 500/14 CC").flanschdurchmesser_paar
        self.assertAlmostEqual(links, 100.0)
        self.assertAlmostEqual(rechts, 100.0)

    def test_paar_in_klammern_gewinnt(self):
        """„47,5 (22,5/25)“ – die Klammer nennt die Seiten einzeln."""
        links, rechts = self._nabe("SON 28 disc 6-bolt").flanschabstaende
        self.assertAlmostEqual(links, 22.5)
        self.assertAlmostEqual(rechts, 25.0)

    def test_schraegstrich_ohne_klammer(self):
        links, rechts = self._nabe("SON 28 disc 6-bolt").flanschdurchmesser_paar
        self.assertAlmostEqual(links, 59.0)
        self.assertAlmostEqual(rechts, 54.0)

    def test_mehrdeutige_angaben_bleiben_leer(self):
        """„42/42 (18-24L) bzw. 38/38 (32/36L)“ hängt von der Lochzahl ab."""
        mehrdeutig = [
            e for e in self.katalog.naben if "bzw" in e.flanschdurchmesser.lower()
        ]
        self.assertTrue(mehrdeutig)
        for eintrag in mehrdeutig:
            self.assertIsNone(eintrag.flanschdurchmesser_paar)

    def test_werte_sind_plausibel(self):
        for eintrag in self.katalog.naben:
            abstand = eintrag.flanschabstaende
            if abstand is not None:
                for wert in abstand:
                    self.assertTrue(5 <= wert <= 90, f"{eintrag.modell}: {wert}")
            durchmesser = eintrag.flanschdurchmesser_paar
            if durchmesser is not None:
                for wert in durchmesser:
                    self.assertTrue(20 <= wert <= 200, f"{eintrag.modell}: {wert}")

    def test_rechenfertige_stehen_vorn(self):
        eintraege = katalog.als_listeneintraege()
        fertig = [i for i, (_, e) in enumerate(eintraege) if e.hat_flanschmasse]
        offen = [i for i, (_, e) in enumerate(eintraege) if not e.hat_flanschmasse]
        self.assertLess(max(fertig), min(offen))

    def test_listentext_kennzeichnet_vollstaendige(self):
        """Ein Häkchen genügt – der Satz stand zweihundertmal untereinander."""
        rohloff = self._nabe("SPEEDHUB 500/14 CC")
        self.assertIn("✓", rohloff.listentext)

    def test_listentext_bleibt_kurz(self):
        """Nur Name und Häkchen: Kennwerte gehören nicht in die Auswahlliste.

        Vorher trug jede Zeile Einbaubreite, Lochzahl, Bremsaufnahme und
        Freilauftyp mit sich. Bei zweihundert Naben untereinander findet man
        darin den Namen nicht mehr.
        """
        rohloff = self._nabe("SPEEDHUB 500/14 CC")
        self.assertNotIn("mm", rohloff.listentext)
        self.assertNotIn("Loch", rohloff.listentext)
        self.assertLessEqual(len(rohloff.listentext), len(rohloff.bezeichnung) + 8)

    def test_kennwerte_tragen_das_weggelassene(self):
        rohloff = self._nabe("SPEEDHUB 500/14 CC")
        self.assertIn("mm", rohloff.kennwerte)
        self.assertIn("Loch", rohloff.kennwerte)


class TestHerstellerfilter(unittest.TestCase):
    """Art und Hersteller lassen sich einzeln und gemeinsam einschränken."""

    def setUp(self):
        self.katalog = katalog.lade()

    def test_alle_hersteller(self):
        """Jeder Hersteller mit mindestens einer Nabe steht in der Liste."""
        erwartet = {e.hersteller for e in self.katalog.naben if e.hersteller}
        self.assertEqual(set(self.katalog.hersteller()), erwartet)
        self.assertGreaterEqual(len(erwartet), 14)

    def test_hersteller_zur_art(self):
        """Zur Art Dynamo darf kein Hersteller ohne Dynamo auftauchen."""
        namen = self.katalog.hersteller("Dynamo")
        self.assertTrue(any(n.startswith("SON") for n in namen))
        self.assertNotIn("Pinion", namen)
        for name in namen:
            self.assertTrue(self.katalog.suche(hersteller=name, art="Dynamo"))

    def test_leere_namen_fliegen_raus(self):
        self.assertNotIn("", self.katalog.hersteller())

    def test_beide_filter_zusammen(self):
        son = next(n for n in self.katalog.hersteller() if n.startswith("SON"))
        treffer = self.katalog.suche(hersteller=son, art="Dynamo")
        self.assertTrue(treffer)
        for eintrag in treffer:
            self.assertEqual(eintrag.hersteller, son)
            self.assertEqual(eintrag.art, "Dynamo")

    def test_liste_mit_beiden_filtern(self):
        son = next(n for n in self.katalog.hersteller() if n.startswith("SON"))
        eintraege = katalog.als_listeneintraege("Dynamo", son)
        self.assertTrue(eintraege)
        self.assertLess(len(eintraege), len(katalog.als_listeneintraege("Dynamo")))
        for _, eintrag in eintraege:
            self.assertEqual(eintrag.hersteller, son)

    def test_unpassende_kombination_bleibt_leer(self):
        self.assertEqual(self.katalog.suche(hersteller="Pinion", art="Dynamo"), [])


class TestErgaenzungen(unittest.TestCase):
    """Nachträge aus dem Tabellenfenster liegen getrennt von der Tabelle."""

    @staticmethod
    def _bestand() -> int:
        """Naben ohne eigene Nachträge: Tabelle plus mitgelieferte Zusätze."""
        pfad = katalog._katalogdatei()
        aus_tabelle = json.loads(pfad.read_text(encoding="utf-8"))["naben"]
        return len(aus_tabelle) + len(katalog.lade_zusatz())

    def setUp(self):
        self._verzeichnis = tempfile.TemporaryDirectory()
        self._alt = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = self._verzeichnis.name
        katalog.neu_laden()

    def tearDown(self):
        if self._alt is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._alt
        katalog.neu_laden()
        self._verzeichnis.cleanup()

    def _nabe(self, modell: str):
        return next(e for e in katalog.lade().naben if e.modell == modell)

    def test_ohne_nachtrag_bleibt_alles_wie_in_der_tabelle(self):
        self.assertEqual(katalog.lade_ergaenzungen(), {})
        self.assertFalse(self._nabe("SPEEDHUB 500/14 CC").ergaenzt)

    def test_nachtrag_macht_eine_nabe_rechenfertig(self):
        offen = next(e for e in katalog.lade().naben if not e.hat_flanschmasse)
        katalog.speichere_ergaenzungen({
            offen.schluessel: {"flanschabstand": "60 (30/30)",
                               "flanschdurchmesser": "45/45"},
        })
        danach = self._nabe(offen.modell)
        self.assertTrue(danach.hat_flanschmasse)
        self.assertTrue(danach.ergaenzt)
        self.assertEqual(danach.flanschabstaende, (30.0, 30.0))
        self.assertEqual(danach.flanschdurchmesser_paar, (45.0, 45.0))

    def test_nachtrag_ueberlagert_die_tabelle(self):
        katalog.speichere_ergaenzungen({
            "Rohloff|SPEEDHUB 500/14 CC": {"flanschdurchmesser": "Ø98"},
        })
        self.assertEqual(self._nabe("SPEEDHUB 500/14 CC").flanschdurchmesser_paar, (98.0, 98.0))

    def test_unbekannte_felder_werden_ignoriert(self):
        katalog.speichere_ergaenzungen({
            "Rohloff|SPEEDHUB 500/14 CC": {"quatsch": "x", "lochzahl": "28/32"},
        })
        nabe = self._nabe("SPEEDHUB 500/14 CC")
        self.assertEqual(nabe.lochzahl, "28/32")
        self.assertFalse(hasattr(nabe, "quatsch"))

    def test_nachtrag_ohne_gegenstueck_legt_eine_nabe_an(self):
        """So kommen Naben in den Katalog, die in der Tabelle fehlen."""
        katalog.speichere_ergaenzungen({
            "Shimano|FH-M732 (Schraubkranz)": {
                "hersteller": "Shimano", "modell": "FH-M732 (Schraubkranz)",
                "art": "Hinterrad", "freilauf": "Schraubkranz (klassisches Gewinde)",
            },
        })
        naben = katalog.lade().naben
        self.assertEqual(len(naben), self._bestand() + 1)
        neu = next(e for e in naben if e.modell == "FH-M732 (Schraubkranz)")
        self.assertTrue(neu.selbst_angelegt)
        self.assertTrue(neu.ergaenzt)
        self.assertIn("Schraubkranz", neu.merkmale)
        self.assertIn("Shimano", katalog.lade().hersteller("Schraubkranz"))

    def test_verwerfen_stellt_die_tabelle_wieder_her(self):
        katalog.speichere_ergaenzungen({
            "Rohloff|SPEEDHUB 500/14 CC": {"flanschdurchmesser": "Ø98"},
        })
        katalog.speichere_ergaenzungen({})
        self.assertEqual(self._nabe("SPEEDHUB 500/14 CC").flanschdurchmesser_paar, (100.0, 100.0))

    def test_kaputte_datei_wird_uebergangen(self):
        pfad = katalog._ergaenzungsdatei()
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text("kein JSON", encoding="utf-8")
        katalog.neu_laden()
        self.assertEqual(katalog.lade_ergaenzungen(), {})
        self.assertEqual(len(katalog.lade().naben), self._bestand())


class TestFreilauf(unittest.TestCase):
    """Die Spalte zum Freilauf entscheidet über die Bauart und die Kurzform."""

    def setUp(self):
        self.katalog = katalog.lade()

    def _nabe(self, modell: str):
        return next(e for e in self.katalog.naben if e.modell == modell)

    def test_spalte_ist_gefuellt(self):
        mit = [e for e in self.katalog.naben if e.freilauf]
        self.assertGreater(len(mit), 190)

    def test_vorderrad_aus_der_freilaufspalte(self):
        """„entfällt (Vorderradnabe, kein Freilauf)“ heißt Vorderrad."""
        vorne = self.katalog.suche(art="Vorderrad")
        self.assertTrue(vorne)
        for eintrag in vorne:
            self.assertIn("vorderrad", eintrag.freilauf.lower())

    def test_singlespeed_wird_nicht_zur_kassette(self):
        """„entfällt (Singlespeed, kein Freilauf/Kassette)“ enthält das Wort
        Kassette, meint aber das Gegenteil."""
        single = self.katalog.suche(art="Singlespeed")
        self.assertTrue(single)
        for eintrag in single:
            self.assertIn("singlespeed", eintrag.freilauf.lower())

    def test_kassette_hat_einen_freilaufkoerper(self):
        for eintrag in self.katalog.suche(art="Kassette"):
            text = eintrag.freilauf.lower()
            self.assertFalse(text.startswith("entfällt"), eintrag.modell)

    def test_schraubkranz_erkannt(self):
        schraub = self.katalog.suche(art="Schraubkranz")
        self.assertTrue(schraub)
        for eintrag in schraub:
            self.assertIn("schraub", eintrag.freilauf.lower())

    def test_kurzform_nennt_die_standards(self):
        self.assertEqual(
            katalog.Katalogeintrag(
                hersteller="Hope", art="Kassette", modell="X",
                freilauf="Shimano HG (9–11-fach) und SRAM XD (11/12-fach)",
            ).freilauf_kurz,
            "HG · XD",
        )

    def test_xd_wird_nicht_aus_xdr_gelesen(self):
        kurz = katalog.Katalogeintrag(
            hersteller="Hope", art="Kassette", modell="X",
            freilauf="Shimano HG-11 / SRAM XDR (Rennrad/Gravel-Freilaufkörper)",
        ).freilauf_kurz
        self.assertEqual(kurz, "HG · XDR")

    def test_entfaellt_ergibt_keine_kurzform(self):
        self.assertEqual(
            katalog.Katalogeintrag(
                hersteller="Hope", art="Vorderrad", modell="X",
                freilauf="entfällt (Vorderradnabe, kein Freilauf)",
            ).freilauf_kurz,
            "",
        )

    def test_freilauf_ist_durchsuchbar(self):
        treffer = self.katalog.suche("micro spline")
        self.assertTrue(treffer)
        for eintrag in treffer:
            self.assertIn("micro spline", eintrag.suchtext)


class TestMerkmale(unittest.TestCase):
    """Bauart und Ritzelaufnahme sind zwei Dinge – eine Nabe hat beides.

    Vorher steckten sie in einem einzigen Feld, deshalb tauchte unter
    „Schraubkranz“ nur Hope auf: die Sturmey-Archer AW ist eine
    Nabenschaltung *und* hat einen Schraubkranz, konnte aber nur eines sein.
    """

    def setUp(self):
        self.katalog = katalog.lade()

    def test_nabe_kann_in_mehreren_schubladen_stehen(self):
        son = next(e for e in self.katalog.naben if e.modell == "SON 28")
        self.assertIn("Dynamo", son.merkmale)
        self.assertIn("Vorderrad", son.merkmale)

    def test_rohloff_ist_nabenschaltung_und_schraubritzel(self):
        rohloff = next(e for e in self.katalog.naben if e.modell == "SPEEDHUB 500/14 CC")
        self.assertIn("Nabenschaltung", rohloff.merkmale)
        self.assertIn("Schraubritzel", rohloff.merkmale)

    def test_schraubkranz_nicht_nur_von_einem_hersteller(self):
        hersteller = self.katalog.hersteller("Schraubkranz")
        self.assertIn("Hope", hersteller)
        self.assertIn("Sturmey-Archer", hersteller)

    def test_kassette_ueber_hersteller_hinweg(self):
        hersteller = self.katalog.hersteller("Kassette")
        self.assertGreater(len(hersteller), 1)

    def test_aufnahme_aus_der_freilaufspalte(self):
        beispiele = {
            "Shimano HG (9–11-fach) und SRAM XD": "Kassette",
            "Schraubkranz (klassisches Gewinde)": "Schraubkranz",
            "Schraubritzel (Rohloff-eigenes Gewinde), 16Z": "Schraubritzel",
            "Steckzahnkranz (Push-on-Ritzel)": "Steckzahnkranz",
            "Steckritzel (3-Punkt-Aufnahme mit Sprengring)": "Steckritzel",
            "entfällt (Singlespeed, kein Freilauf/Kassette)": "Singlespeed",
            "entfällt (Vorderradnabe, kein Freilauf)": "",
            "k. A.": "",
        }
        for text, erwartet in beispiele.items():
            eintrag = katalog.Katalogeintrag(
                hersteller="X", art="Hinterrad", modell="Y", freilauf=text)
            self.assertEqual(eintrag.aufnahme, erwartet, text)

    def test_schraubritzel_wird_nicht_als_schraubkranz_gelesen(self):
        eintrag = katalog.Katalogeintrag(
            hersteller="Rohloff", art="Nabenschaltung", modell="X",
            freilauf="Schraubritzel (Rohloff-eigenes Gewinde)")
        self.assertEqual(eintrag.aufnahme, "Schraubritzel")

    def test_merkmale_haben_keine_doppelten(self):
        for eintrag in self.katalog.naben:
            self.assertEqual(len(eintrag.merkmale), len(set(eintrag.merkmale)), eintrag.modell)

    def test_jede_nabe_hat_mindestens_ein_merkmal(self):
        for eintrag in self.katalog.naben:
            self.assertTrue(eintrag.merkmale, eintrag.modell)


class TestEinordnungIstWiderspruchsfrei(unittest.TestCase):
    """Dieselben Prüfungen wie ``werkzeuge/katalog_pruefen.py``, nur ohne Tabelle.

    Sie halten fest, was mehrfach schiefging: eine Schraubkranznabe, deren
    Text „kein Freilaufkörper“ enthält, wurde als „ohne Aufnahme“ gelesen;
    eine Singlespeed-Nabe landete wegen des Worts „Kassette“ bei den Kassetten.
    """

    OHNE_RITZEL = {"Vorderrad", "Dynamo"}

    def setUp(self):
        self.katalog = katalog.lade()

    def test_keine_vorderradnabe_mit_ritzelaufnahme(self):
        for eintrag in self.katalog.naben:
            if set(eintrag.merkmale) & self.OHNE_RITZEL:
                self.assertFalse(eintrag.aufnahme, f"{eintrag.modell}: {eintrag.aufnahme}")

    def test_hinterrad_mit_freilauftext_hat_eine_aufnahme(self):
        for eintrag in self.katalog.naben:
            if eintrag.art == "Hinterrad" and eintrag.freilauf:
                self.assertTrue(eintrag.aufnahme, f"{eintrag.modell}: {eintrag.freilauf}")

    def test_screw_on_ist_schraubkranz(self):
        """Der Fall, der die Prüfung ausgelöst hat."""
        nabe = next(e for e in self.katalog.naben if e.modell.startswith("Screw-on"))
        self.assertEqual(nabe.aufnahme, "Schraubkranz")
        self.assertIn("Schraubkranz", nabe.merkmale)

    def test_kein_freilaufkoerper_verneint_nicht(self):
        eintrag = katalog.Katalogeintrag(
            hersteller="X", art="Hinterrad", modell="Y",
            freilauf="Schraubkranz (klassisches Gewinde, kein Freilaufkörper)")
        self.assertEqual(eintrag.aufnahme, "Schraubkranz")

    def test_alles_auswertbar_was_dasteht(self):
        for eintrag in self.katalog.naben:
            proben = (
                (eintrag.flanschabstand, eintrag.flanschabstaende),
                (eintrag.flanschdurchmesser, eintrag.flanschdurchmesser_paar),
                (eintrag.speichenloch, eintrag.speichenloch_mm),
            )
            for text, wert in proben:
                if text and not any(w in text.lower() for w in
                                    ("bzw", "je nach", "abhängig", "k. a.")):
                    self.assertIsNotNone(wert, f"{eintrag.modell}: {text!r}")


class TestNichtEinspeichbar(unittest.TestCase):
    """Tretlager-Getriebe stehen in der Tabelle, sind aber keine Laufradnaben.

    Die Tabelle trennt sie mit der Zeile „folgende Systeme sind KEINE
    einspeichbaren Laufradnaben, sondern Tretlager-Getriebe“ ab. Ohne diese
    Trennung standen 15 Pinion- und Effigear-Getriebe in der Nabenauswahl.
    """

    def setUp(self):
        self.katalog = katalog.lade()

    def test_getriebe_sind_erkannt(self):
        getriebe = [e for e in self.katalog.naben if not e.einspeichbar]
        self.assertEqual(len(getriebe), 15)
        for eintrag in getriebe:
            self.assertIn(eintrag.hersteller, ("Pinion", "Effigear"))

    def test_getriebe_stehen_nicht_in_der_nabenauswahl(self):
        auswahl = [e for _, e in katalog.als_listeneintraege()]
        self.assertTrue(auswahl)
        for eintrag in auswahl:
            self.assertTrue(eintrag.einspeichbar, eintrag.modell)

    def test_getriebe_tauchen_in_keinem_filter_auf(self):
        self.assertNotIn(katalog.KEIN_LAUFRAD, self.katalog.arten())

    def test_nabenschaltungen_ohne_getriebe(self):
        """Die Getriebe waren vorher als Nabenschaltung mitgezählt."""
        schaltungen = katalog.als_listeneintraege("Nabenschaltung")
        self.assertEqual(len(schaltungen), 73)

    def test_getriebe_bleiben_im_katalog(self):
        """Sie gehören zur Tabelle – nur eben nicht in die Auswahl."""
        self.assertTrue(any(e.hersteller == "Pinion" for e in self.katalog.naben))


if __name__ == "__main__":
    unittest.main()


class TestAnzahlenImFilter(unittest.TestCase):
    """Die Zahl in der Filterliste muss stimmen.

    Sie ist der Grund, warum ein Merkmal mit sechs Naben nicht mehr wie ein
    Fehler des Filters aussieht – dann muss sie aber auch zur Auswahlliste
    passen.
    """

    def setUp(self):
        katalog.neu_laden()
        self.katalog = katalog.lade()

    def test_anzahl_passt_zur_auswahlliste(self):
        for art, anzahl in self.katalog.arten_mit_anzahl():
            with self.subTest(art=art):
                self.assertEqual(anzahl, len(katalog.als_listeneintraege(art)))

    def test_reihenfolge_wie_ohne_anzahl(self):
        self.assertEqual([name for name, _ in self.katalog.arten_mit_anzahl()],
                         self.katalog.arten())

    def test_nicht_einspeichbares_wird_nicht_gezaehlt(self):
        gesamt = sum(1 for e in self.katalog.naben if e.einspeichbar)
        self.assertLess(gesamt, len(self.katalog.naben))
        self.assertEqual(gesamt, len(katalog.als_listeneintraege()))

    def test_hersteller_mit_anzahl_passt(self):
        for name, anzahl in self.katalog.hersteller_mit_anzahl():
            with self.subTest(hersteller=name):
                self.assertEqual(anzahl, len(katalog.als_listeneintraege(hersteller=name)))

    def test_hersteller_zu_einem_merkmal(self):
        """Schraubkranz: die Tabelle führt dazu nur zwei Hersteller.

        Kein Fehler des Filters, sondern eine Lücke in der Tabelle – dieser
        Test hält fest, dass die Anzeige sie richtig wiedergibt.
        """
        mit_anzahl = self.katalog.hersteller_mit_anzahl("Schraubkranz")
        summe = sum(anzahl for _, anzahl in mit_anzahl)
        self.assertEqual(summe, len(katalog.als_listeneintraege("Schraubkranz")))
        self.assertNotIn("Shimano", [name for name, _ in mit_anzahl])


class TestZusatznaben(unittest.TestCase):
    """Naben aus ``data/naben_zusatz.json`` – nachgetragen, mit Quellenangabe.

    Sie stehen absichtlich **nicht** in der Herstellertabelle: die bleibt
    unberührt und wird von ``katalog_erzeugen.py`` überschrieben. Deshalb muss
    an jeder dieser Naben erkennbar sein, woher sie kommt.
    """

    def setUp(self):
        katalog.neu_laden()
        self.katalog = katalog.lade()
        self.zusatz = katalog.lade_zusatz()

    def test_zusatzdatei_ist_vorhanden(self):
        self.assertTrue(self.zusatz)
        for satz in self.zusatz:
            with self.subTest(modell=satz.get("modell")):
                self.assertTrue(satz.get("hersteller"))
                self.assertTrue(satz.get("modell"))
                self.assertTrue(satz.get("quelle"), "ohne Quellenangabe")

    def test_zusatznaben_stehen_im_katalog(self):
        im_katalog = {e.schluessel for e in self.katalog.naben}
        for satz in self.zusatz:
            with self.subTest(modell=satz["modell"]):
                self.assertIn(f"{satz['hersteller']}|{satz['modell']}", im_katalog)

    def test_herkunft_ist_erkennbar(self):
        for eintrag in self.katalog.naben:
            with self.subTest(modell=eintrag.modell):
                self.assertEqual(eintrag.aus_tabelle, not eintrag.quelle)

    def test_ungeprueftes_wird_als_solches_ausgewiesen(self):
        ungeprueft = [e for e in self.katalog.naben if e.quelle == katalog.UNGEPRUEFT]
        self.assertTrue(ungeprueft)
        for eintrag in ungeprueft:
            with self.subTest(modell=eintrag.modell):
                self.assertIn("ungeprüft", eintrag.listentext)
                self.assertFalse(eintrag.hat_flanschmasse,
                                 "ungeprüft und trotzdem Flanschmaße?")

    def test_belegtes_nennt_nachgetragen(self):
        belegt = [e for e in self.katalog.naben
                  if e.quelle and e.quelle != katalog.UNGEPRUEFT]
        self.assertTrue(belegt)
        for eintrag in belegt:
            with self.subTest(modell=eintrag.modell):
                self.assertIn("nachgetragen", eintrag.listentext)

    def test_die_tabelle_gewinnt_bei_doppelten_modellen(self):
        """Steht ein Modell in beidem, zählt die Tabelle."""
        aus_tabelle = {
            f"{s['hersteller']}|{s['modell']}"
            for s in json.loads(katalog._katalogdatei().read_text(encoding="utf-8"))["naben"]
        }
        for satz in self.zusatz:
            with self.subTest(modell=satz["modell"]):
                self.assertNotIn(f"{satz['hersteller']}|{satz['modell']}", aus_tabelle,
                                 "doppelt geführt – gehört in die Tabelle, nicht daneben")

    def test_schraubkranz_ist_gewachsen(self):
        namen = [t for t, _ in katalog.als_listeneintraege("Schraubkranz")]
        self.assertGreater(len(namen), 6)
        text = " ".join(namen)
        for hersteller in ("Joytech", "Quando", "Formula", "Phil Wood"):
            with self.subTest(hersteller=hersteller):
                self.assertIn(hersteller, text)

    def test_rx100_ist_rechenfertig(self):
        eintrag = next(e for e in self.katalog.naben if "FH-A550" in e.modell)
        self.assertTrue(eintrag.hat_flanschmasse)
        self.assertEqual(eintrag.flanschdurchmesser_paar, (45.0, 45.0))
        links, rechts = eintrag.flanschabstaende
        self.assertAlmostEqual(links, 37.3, places=2)
        self.assertAlmostEqual(rechts, 20.7, places=2)
        self.assertEqual(eintrag.aufnahme, "Kassette")

    def test_phil_wood_bleibt_unvollstaendig(self):
        """Halbe Daten dürfen nicht als rechenfertig gelten."""
        for eintrag in self.katalog.naben:
            if eintrag.hersteller == "Phil Wood":
                with self.subTest(modell=eintrag.modell):
                    self.assertFalse(eintrag.hat_flanschmasse)
                    self.assertEqual(eintrag.aufnahme, "Schraubkranz")


class TestModellreihen(unittest.TestCase):
    """Die Auswahlliste fasst Ausführungen derselben Reihe zusammen.

    Anlass: 230 Naben in einer Klappliste, von denen viele nur Achsvarianten
    derselben Reihe sind – allein die Hope Pro 2 Evo fünfmal. Die Zuordnung
    steht in ``data/naben_modellreihen.json`` und wird aus der
    Zuordnungstabelle erzeugt.
    """

    def setUp(self):
        katalog.neu_laden()

    def test_liste_wird_kuerzer(self):
        einzeln = katalog.als_listeneintraege()
        reihen = katalog.als_modellreihen()
        self.assertLess(len(reihen), len(einzeln))
        self.assertEqual(sum(len(e) for _t, e in reihen), len(einzeln),
                         "Beim Zusammenfassen ist eine Nabe verloren gegangen")

    def test_keine_nabe_faellt_heraus(self):
        """Auch ohne Eintrag in der Zuordnung muss die Nabe wählbar bleiben."""
        aus_reihen = {e.schluessel for _t, eintraege in katalog.als_modellreihen()
                      for e in eintraege}
        einzeln = {e.schluessel for _t, e in katalog.als_listeneintraege()}
        self.assertEqual(aus_reihen, einzeln)

    def test_ohne_zuordnung_steht_die_nabe_fuer_sich(self):
        eintrag = katalog.Katalogeintrag(hersteller="Prüfhaus", art="Vorderrad",
                                         modell="Einzelstück")
        self.assertEqual(eintrag.modellreihe, "")

    def test_jede_reihe_hat_mindestens_eine_ausfuehrung(self):
        for text, eintraege in katalog.als_modellreihen():
            with self.subTest(reihe=text[:40]):
                self.assertTrue(eintraege)

    def test_ausfuehrungen_gehoeren_zu_einem_hersteller(self):
        for text, eintraege in katalog.als_modellreihen():
            with self.subTest(reihe=text[:40]):
                self.assertEqual(len({e.hersteller for e in eintraege}), 1)

    def test_mit_flanschmassen_steht_vorn(self):
        """Innerhalb der Reihe zuerst, was sich ohne Nachmessen rechnen lässt."""
        for text, eintraege in katalog.als_modellreihen():
            if len(eintraege) < 2:
                continue
            with self.subTest(reihe=text[:40]):
                masse = [e.hat_flanschmasse for e in eintraege]
                self.assertEqual(masse, sorted(masse, reverse=True))

    def test_filter_wirken_auch_auf_reihen(self):
        alle = katalog.als_modellreihen()
        hope = katalog.als_modellreihen(hersteller="Hope")
        self.assertLess(len(hope), len(alle))
        for _text, eintraege in hope:
            self.assertEqual(eintraege[0].hersteller, "Hope")

    def test_reihenzeile_nennt_keine_anzahl(self):
        """„5 Ausführungen“ sagte nicht, wonach man wählt – nur, dass man muss."""
        for text, eintraege in katalog.als_modellreihen():
            if len(eintraege) < 2:
                continue
            with self.subTest(reihe=text[:40]):
                self.assertNotIn("Ausführungen", text)
                self.assertNotIn("mm", text)
                self.assertNotIn("Loch", text)

    def test_reihenzeile_bleibt_kurz(self):
        """Name, höchstens ein Häkchen dahinter."""
        for text, eintraege in katalog.als_modellreihen():
            if len(eintraege) < 2:
                continue
            with self.subTest(reihe=text[:40]):
                self.assertLessEqual(text.count("·"), 1)

    def test_zuordnung_deckt_den_katalog_weitgehend(self):
        """Bleibt die Zuordnungsdatei zurück, fällt es hier auf."""
        naben = [e for e in katalog.lade().naben if e.einspeichbar]
        zugeordnet = [e for e in naben if e.schluessel in katalog.lade_modellreihen()]
        self.assertGreater(len(zugeordnet), len(naben) * 0.9,
                           "Mehr als jede zehnte Nabe hat keine Modellreihe")
