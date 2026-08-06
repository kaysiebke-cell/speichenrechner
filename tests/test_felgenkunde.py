"""Tests der Felgentypen.

Der wichtigste Test ist :class:`TestGegenTabelle`: er liest die
Herstellertabelle noch einmal ein und vergleicht sie Zelle für Zelle mit dem
erzeugten Katalog. Damit fällt auf, wenn eine erweiterte Tabelle anders
gelesen wird als gedacht – so wie beim Nabenkatalog das Prüfwerkzeug.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

from speichenrechner import berechnung, felgenkunde  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe, Speichensatz  # noqa: E402

try:
    # Die Zeichnung braucht GTK. Auf einem Rechner ohne GTK – etwa im
    # Testlauf auf GitHub – laufen die übrigen Tests trotzdem.
    from speichenrechner.ui import bauteile
except ImportError:  # pragma: no cover
    bauteile = None

QUELLE = Path(__file__).resolve().parent.parent / "daten_quelle_felgen.xlsx"


class TestKatalog(unittest.TestCase):
    def setUp(self):
        felgenkunde.neu_laden()
        self.kunde = felgenkunde.lade()

    def test_katalog_ist_gefuellt(self):
        self.assertGreaterEqual(len(self.kunde.typen), 17)

    def test_namen_sind_eindeutig(self):
        namen = [typ.name for typ in self.kunde.typen]
        self.assertEqual(len(namen), len(set(namen)))

    def test_kategorien_der_tabelle(self):
        self.assertEqual(self.kunde.kategorien(), ["Bauform", "Material", "Einsatzbereich"])

    def test_filter_kuerzt_die_liste(self):
        bauformen = self.kunde.nach_kategorie("Bauform")
        self.assertTrue(bauformen)
        self.assertLess(len(bauformen), len(self.kunde.typen))
        for typ in bauformen:
            self.assertEqual(typ.kategorie, "Bauform")

    def test_unbekannte_kategorie_ergibt_leere_liste(self):
        self.assertEqual(self.kunde.nach_kategorie("Gibtsnicht"), [])

    def test_finden_ueber_den_namen(self):
        self.assertIsNotNone(felgenkunde.finde("Stahlfelge"))
        self.assertIsNone(felgenkunde.finde("Papierfelge"))
        self.assertIsNone(felgenkunde.finde(""))

    def test_fussnote_bleibt_erhalten(self):
        """Die Hinweiszeile der Tabelle ist kein Felgentyp, geht aber nicht verloren."""
        self.assertTrue(self.kunde.fussnoten)
        self.assertNotIn("Hinweis", [typ.name for typ in self.kunde.typen])
        self.assertIn("Ösung", self.kunde.fussnoten[0])


class TestAuswertung(unittest.TestCase):
    """Was aus den Texten der Tabelle herausgelesen wird."""

    def setUp(self):
        felgenkunde.neu_laden()

    def test_material_mehrfach(self):
        typ = felgenkunde.finde("Flachbettfelge")
        self.assertEqual(typ.materialien, ("Stahl", "Aluminium"))

    def test_material_carbon_wird_auch_als_cfk_erkannt(self):
        """Die Tabelle schreibt einmal „Carbon (CFK)“ statt nur „Carbon“."""
        typ = felgenkunde.finde("Carbonfelge")
        self.assertEqual(typ.materialien, ("Carbon",))

    def test_reihenfolge_der_materialien_ist_gleichgueltig(self):
        """Die Tabelle schreibt beides: „Aluminium/Carbon“ und „Carbon/Aluminium“.

        Beide meinen dasselbe. Würde der Text als Ganzes als Schlüssel dienen,
        gäbe es zwei Werkstoffe für eine Sache und ein Filter auf „Carbon“
        würde die Hälfte übersehen.
        """
        vorwaerts = felgenkunde.finde("Aero-Felge")                     # Aluminium/Carbon
        rueckwaerts = felgenkunde.finde("Hakenlose Felge (Hookless/TSS)")  # Carbon/Aluminium
        self.assertNotEqual(vorwaerts.material, rueckwaerts.material)
        self.assertEqual(vorwaerts.materialien, rueckwaerts.materialien)
        self.assertEqual(vorwaerts.spannungsbereich, rueckwaerts.spannungsbereich)

    def test_oesenstufen(self):
        self.assertEqual(felgenkunde.finde("Flachbettfelge").oesen_stufe, 0)
        self.assertEqual(felgenkunde.finde("Hohlkammerfelge (Box-Section)").oesen_stufe, 1)
        self.assertEqual(felgenkunde.finde("MTB-Felge").oesen_stufe, 2)

    def test_wandung_kommt_aus_der_beschreibung(self):
        self.assertEqual(felgenkunde.finde("Hohlkammerfelge (Box-Section)").wandung,
                         "doppelwandig")
        self.assertEqual(felgenkunde.finde("Flachbettfelge").wandung, "einwandig")

    def test_schwaecheres_material_begrenzt_die_spannung(self):
        """„Aluminium/Stahl“ wird nicht fester gespannt als Stahl."""
        gemischt = felgenkunde.finde("Flachbettfelge")
        self.assertEqual(gemischt.spannungsbereich, felgenkunde.SPANNUNG_JE_MATERIAL["Stahl"])

    def test_titan_hat_keine_faustregel(self):
        self.assertIsNone(felgenkunde.finde("Titanfelge").spannungsbereich)

    def test_kindergroessen_werden_gelesen(self):
        self.assertEqual(felgenkunde.finde("Flachbettfelge").kindergroessen_zoll, (12, 16, 18))
        self.assertEqual(felgenkunde.finde("Hohlkammerfelge (Box-Section)").kindergroessen_zoll,
                         (16, 18))

    def test_nicht_ueblich_ergibt_keine_groessen(self):
        aero = felgenkunde.finde("Aero-Felge")
        self.assertTrue(aero.nur_ab_20_zoll)
        self.assertEqual(aero.kindergroessen_zoll, ())

    def test_nicht_ueblich_mit_zusatz_zaehlt_auch(self):
        """„nicht üblich (ab 20 Zoll)“ nennt eine Zahl, meint aber keine Kindergröße."""
        mtb = felgenkunde.finde("MTB-Felge")
        self.assertTrue(mtb.nur_ab_20_zoll)
        self.assertEqual(mtb.kindergroessen_zoll, ())

    @unittest.skipIf(bauteile is None, "GTK fehlt")
    def test_jeder_typ_hat_ein_gezeichnetes_profil(self):
        for typ in felgenkunde.lade().typen:
            with self.subTest(typ=typ.name):
                self.assertIn(typ.profil, bauteile.PROFILE)

    @unittest.skipIf(bauteile is None, "GTK fehlt")
    def test_profile_unterscheiden_sich(self):
        """Die Bauformen dürfen nicht alle dasselbe Bild ergeben."""
        self.assertEqual(felgenkunde.finde("Aero-Felge").profil, "aero")
        self.assertEqual(felgenkunde.finde("Flachbettfelge").profil, "flachbett")
        self.assertEqual(felgenkunde.finde("Hakenlose Felge (Hookless/TSS)").profil, "hakenlos")
        self.assertEqual(felgenkunde.finde("Schlauchreifenfelge (Tubular)").profil, "schlauch")

    @unittest.skipIf(bauteile is None, "GTK fehlt")
    def test_aero_ist_tiefer_als_flachbett(self):
        tief, _ = bauteile.profil_masse("aero")
        flach, _ = bauteile.profil_masse("flachbett")
        self.assertGreater(tief, 2 * flach)

    @unittest.skipIf(bauteile is None, "GTK fehlt")
    def test_unbekanntes_profil_faellt_auf_die_hohlkammer_zurueck(self):
        self.assertEqual(bauteile.profil_masse("gibtsnicht"),
                         bauteile.profil_masse("hohlkammer"))


class TestHinweise(unittest.TestCase):
    def setUp(self):
        felgenkunde.neu_laden()

    def test_ohne_oesen_und_einwandig_kommt_die_unterlegscheibe(self):
        text = " ".join(felgenkunde.finde("Flachbettfelge").hinweise())
        self.assertIn("Unterlegscheiben", text)

    def test_doppelt_genietet_wird_gelobt(self):
        text = " ".join(felgenkunde.finde("MTB-Felge").hinweise())
        self.assertIn("doppelt genietet", text)

    def test_carbon_verweist_auf_den_hersteller(self):
        text = " ".join(felgenkunde.finde("Carbonfelge").hinweise())
        self.assertIn("Höchstspannung", text)

    def test_hakenlos_nennt_den_reifendruck(self):
        text = " ".join(felgenkunde.finde("Hakenlose Felge (Hookless/TSS)").hinweise())
        self.assertIn("bar", text)

    def test_zu_hohe_spannung_wird_gemeldet(self):
        stahl = felgenkunde.finde("Stahlfelge")
        self.assertTrue(stahl.warnungen(erd=600.0, spannung=1200.0))
        self.assertFalse(stahl.warnungen(erd=600.0, spannung=700.0))

    def test_ohne_zahlen_keine_warnung(self):
        self.assertEqual(felgenkunde.finde("Stahlfelge").warnungen(), [])

    def test_kindergroesse_gegen_nicht_ueblich(self):
        aero = felgenkunde.finde("Aero-Felge")
        klein = " ".join(aero.warnungen(erd=180.0, spannung=1000.0))
        self.assertIn("20 Zoll", klein)
        gross = " ".join(aero.warnungen(erd=600.0, spannung=1000.0))
        self.assertNotIn("20 Zoll", gross)


class TestInDerBerechnung(unittest.TestCase):
    """Der Felgentyp muss in der Berechnung ankommen – nicht nur im Katalog."""

    def setUp(self):
        felgenkunde.neu_laden()
        self.nabe = Nabe("Prüfnabe", 45.0, 45.0, 35.0, 20.0)
        self.einspeichung = Einspeichung(32, 3, 3)

    def _rechne(self, typ: str, spannung: float = 1000.0, erd: float = 600.0):
        return berechnung.berechne(
            self.nabe, Felge("Prüffelge", erd, 0.0, typ), self.einspeichung,
            1.0, Speichensatz(spannung=spannung),
        )

    def test_typ_aendert_die_laenge_nicht(self):
        ohne = self._rechne("")
        mit = self._rechne("Carbonfelge")
        self.assertAlmostEqual(ohne.links.laenge, mit.links.laenge, places=9)
        self.assertAlmostEqual(ohne.rechts.laenge, mit.rechts.laenge, places=9)

    def test_typ_bringt_eine_einschaetzung(self):
        ohne = self._rechne("")
        mit = self._rechne("Flachbettfelge")
        self.assertGreater(len(mit.bewertungen), len(ohne.bewertungen))
        self.assertIn("Unterlegscheiben", " ".join(mit.bewertungen))

    def test_spannungsbereich_steht_in_der_einschaetzung(self):
        text = " ".join(self._rechne("Carbonfelge").bewertungen)
        self.assertIn("N", text)
        self.assertIn("Felgenherstellers", text)

    def test_zu_hohe_spannung_landet_bei_den_hinweisen(self):
        ergebnis = self._rechne("Stahlfelge", spannung=1300.0)
        self.assertIn("zu viel", " ".join(ergebnis.hinweise))

    def test_kleiner_erd_ist_kein_fehler_mehr(self):
        """12-Zoll-Laufräder gibt es – der ERD von 180 mm ist keine Warnung."""
        ergebnis = self._rechne("", erd=180.0)
        self.assertNotIn("außerhalb", " ".join(ergebnis.hinweise))

    def test_unbekannter_typ_stoert_nicht(self):
        ergebnis = self._rechne("Papierfelge")
        self.assertTrue(ergebnis.links.laenge > 0)

    def test_typ_steht_im_bericht(self):
        from speichenrechner import bericht
        felge = Felge("Prüffelge", 600.0, 0.0, "Aero-Felge")
        ergebnis = berechnung.berechne(self.nabe, felge, self.einspeichung)
        self.assertIn("Aero-Felge", bericht.als_text(self.nabe, felge, self.einspeichung,
                                                     ergebnis))


class TestGegenTabelle(unittest.TestCase):
    """Vergleicht den Katalog Zelle für Zelle mit der Felgentabelle."""

    @classmethod
    def setUpClass(cls):
        if not QUELLE.exists():
            raise unittest.SkipTest(f"{QUELLE.name} liegt nicht im Projekt")
        from werkzeuge.felgen_erzeugen import einlesen
        cls.typen, cls.fussnoten = einlesen(QUELLE)

    def setUp(self):
        felgenkunde.neu_laden()
        self.kunde = felgenkunde.lade()

    def test_bestand_stimmt_ueberein(self):
        aus_tabelle = {satz["name"] for satz in self.typen}
        im_katalog = {typ.name for typ in self.kunde.typen}
        self.assertEqual(aus_tabelle - im_katalog, set(), "fehlt im Katalog")
        self.assertEqual(im_katalog - aus_tabelle, set(), "steht nicht in der Tabelle")

    def test_jede_zelle_kam_an(self):
        nach_name = {typ.name: typ for typ in self.kunde.typen}
        for satz in self.typen:
            typ = nach_name[satz["name"]]
            for feld, erwartet in satz.items():
                with self.subTest(typ=satz["name"], feld=feld):
                    self.assertEqual(getattr(typ, feld), erwartet)

    def test_fussnoten_kamen_an(self):
        self.assertEqual(list(self.kunde.fussnoten), self.fussnoten)

    def test_oesung_kennt_nur_drei_schreibweisen(self):
        """Wie eine Prüfregel in einer Datenbank: nur diese drei Werte sind gültig.

        Kommt in einer erweiterten Tabelle eine vierte Schreibweise dazu, fällt
        es hier auf – und nicht erst daran, dass eine Felge ohne Ösen dasteht.
        """
        erlaubt = {"keine", "einfach genietet", "doppelt genietet"}
        gefunden = {typ.oesung for typ in self.kunde.typen}
        self.assertEqual(gefunden - erlaubt, set())

    def test_einsatzbereich_ist_eine_eigene_angabe(self):
        """Der Einsatzbereich ist nicht dasselbe wie die Kategorie.

        „Bauform“ ist die Kategorie, „Rennrad, Triathlon“ der Einsatz. Beides
        muss getrennt ankommen, sonst geht eine ganze Spalte verloren.
        """
        for typ in self.kunde.typen:
            with self.subTest(typ=typ.name):
                self.assertTrue(typ.einsatz, "ohne Einsatzbereich")
                self.assertNotEqual(typ.einsatz, typ.kategorie)

    def test_jede_zeile_ist_ausgewertet(self):
        """Steht etwas da, muss auch etwas herauskommen – sonst ein Tippfehler."""
        for typ in self.kunde.typen:
            with self.subTest(typ=typ.name):
                self.assertTrue(typ.kategorie, "ohne Kategorie")
                self.assertTrue(typ.materialien, f"Material {typ.material!r} nicht erkannt")
                self.assertTrue(typ.kindergroessen, "ohne Angabe zu Kindergrößen")
                if typ.oesung and typ.oesung.lower() != "keine":
                    self.assertTrue(typ.oesen_stufe, f"Ösung {typ.oesung!r} nicht erkannt")


if __name__ == "__main__":
    unittest.main()
