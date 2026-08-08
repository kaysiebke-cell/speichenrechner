"""Tests der Bauform: was aus Bauart und Ritzelaufnahme gezeichnet wird.

Die Ableitung steckt in :mod:`speichenrechner.modelle` und läuft ohne GTK.
Die Zeichnung selbst wird nur geprüft, wenn GTK und eine Anzeige da sind.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "pc"))

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

    @staticmethod
    def _radius_bei(stationen, x_gesucht: float) -> float:
        """Radius der Kontur an einer Stelle, zwischen den Stationen gemittelt.

        Nicht über die Stationen in der Nähe: eine glatte Trommel hat zwischen
        den Flanschen gar keine Zwischenpunkte, weil eine Gerade keine braucht.
        """
        vorher = None
        for x, r in stationen:
            if vorher is not None and vorher[0] <= x_gesucht <= x:
                weite = x - vorher[0]
                anteil = (x_gesucht - vorher[0]) / weite if weite else 0.0
                return vorher[1] + (r - vorher[1]) * anteil
            vorher = (x, r)
        raise AssertionError(f"x = {x_gesucht} liegt außerhalb der Kontur")

    def test_grosse_schale_ist_dicker(self):
        schmal = self._stationen(Nabe(art="Hinterrad", aufnahme="Kassette"), r=50.0)
        dick = self._stationen(Nabe(art="Nabenschaltung", aufnahme="Schraubritzel"), r=50.0)
        self.assertGreater(self._radius_bei(dick, 0.0),
                           2 * self._radius_bei(schmal, 0.0))

    def test_getriebenabe_ist_eine_glatte_trommel(self):
        """Zwischen den Flanschen darf die Schale weder Kehle noch Taille haben.

        Anlass: dort standen zwei tiefe Hohlkehlen mit einem Band dazwischen –
        aus einer falsch gelesenen Zeichnung der SON 28. Eine Rohloff SPEEDHUB
        ist eine gerade Trommel, eine Shimano Nexus ebenso.
        """
        for a_l, a_r in ((29.0, 29.0), (32.0, 26.0), (35.0, 20.0)):
            with self.subTest(a=(a_l, a_r)):
                nabe = Nabe(flanschabstand_links=a_l, flanschabstand_rechts=a_r,
                            art="Nabenschaltung", aufnahme="Schraubritzel")
                stationen = self._stationen(nabe, r=50.0)
                uebergang = self.bauteile.GESTALT.uebergang
                innen = [r for x, r in stationen
                         if -a_l + uebergang <= x <= a_r - uebergang]
                self.assertTrue(innen)
                self.assertAlmostEqual(min(innen), max(innen), places=9,
                                       msg="Die Trommel ist nicht durchgehend gerade")

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


class TestRohloffForm(unittest.TestCase):
    """Die Trommel mit ausgerundeten Schultern gehört der Rohloff allein.

    Anlass: die Form war an der „dicken Schale“ festgemacht und galt damit für
    jede Nabenschaltung – auch für Shimano Nexus und Sturmey-Archer, die anders
    aussehen.
    """

    def setUp(self):
        from speichenrechner.ui import bauteile
        self.bauteile = bauteile

    def test_erkannt_wird_am_namen(self):
        for name, erwartet in (
            ("Rohloff SPEEDHUB 500/14 CC", "rohloff"),
            ("Rohloff SPEEDHUB 500/14 A12 (148 mm, asym.)", "rohloff"),
            ("SPEEDHUB 500/14 TS", "rohloff"),
            ("Shimano Nexus SG-C6001-8R", ""),
            ("Sturmey-Archer S-RF3", ""),
            ("Eigene Nabe", ""),
            ("", ""),
        ):
            with self.subTest(name=name):
                self.assertEqual(Nabe(name=name).bauform, erwartet)

    def test_alle_rohloff_im_katalog_werden_erkannt(self):
        from speichenrechner import katalog
        eintraege = katalog.als_listeneintraege(hersteller="Rohloff")
        self.assertTrue(eintraege, "keine Rohloff im Katalog")
        for beschriftung, eintrag in eintraege:
            with self.subTest(modell=eintrag.modell):
                self.assertEqual(Nabe(name=eintrag.bezeichnung).bauform, "rohloff")

    def _kontur(self, bauform: str):
        return self.bauteile._stationen(
            29.0, 29.0, 50.0, 50.0, "gewinde", "gross",
            art="Nabenschaltung", bauform=bauform,
        )

    def test_rohloff_kommt_aus_der_umrisszeichnung(self):
        """Nicht gerechnet, sondern nachgezeichnet – Punkt für Punkt."""
        rohloff = self._kontur("rohloff")
        self.assertEqual(len(rohloff), len(self.bauteile.ROHLOFF_KONTUR))
        andere = self._kontur("")
        self.assertNotEqual(len(rohloff), len(andere))

    def test_flansche_stehen_an_ihrer_stelle(self):
        """Die Spitzen der beiden Rippen liegen auf den Flanschabständen."""
        for a_l, a_r in ((29.0, 29.0), (32.0, 26.0)):
            with self.subTest(a=(a_l, a_r)):
                kontur = self.bauteile._stationen(
                    a_l, a_r, 50.0, 50.0, "gewinde", "gross",
                    art="Nabenschaltung", bauform="rohloff")
                # Jede Seite für sich: die beiden Rippen sind in der Vorlage
                # nicht auf denselben Zehntelmillimeter hoch.
                def spitze(punkte):
                    hoch = max(r for _x, r in punkte)
                    oben = [x for x, r in punkte if r > hoch - 1e-9]
                    return sum(oben) / len(oben)

                links = [(x, r) for x, r in kontur if x < 0]
                rechts = [(x, r) for x, r in kontur if x > 0]
                self.assertTrue(links and rechts)
                self.assertAlmostEqual(spitze(links), -a_l, delta=a_l * 0.06)
                self.assertAlmostEqual(spitze(rechts), a_r, delta=a_r * 0.22)

    def test_ohne_rohloff_bleiben_die_absaetze(self):
        """Eine Nexus behält die eckigen Drehabsätze – nur zwei Radien."""
        andere = self._kontur("")
        aussen = {round(r, 6) for x, r in andere if -44.0 < x < -30.5}
        self.assertLessEqual(len(aussen), 2)

    def test_allgemeine_getriebenabe_bleibt_gerade(self):
        """Ohne Sonderform ist die Schale zwischen den Flanschen eine Gerade."""
        uebergang = self.bauteile.GESTALT.uebergang
        innen = [r for x, r in self._kontur("")
                 if -29.0 + uebergang <= x <= 29.0 - uebergang]
        self.assertTrue(innen)
        self.assertAlmostEqual(min(innen), max(innen), places=9)


class TestDynamoKugel(unittest.TestCase):
    """Der Generatorkörper ist ein Drehteil und muss rund bleiben.

    Anlass: die Kugel wurde aus zwei Hälften gebaut, und jede Hälfte nahm
    ihren eigenen Flanschabstand als Länge. Bei der SON 28 mit 37/19 mm war
    die linke Hälfte 28,5 mm lang, die rechte 14,6 mm – gleicher Scheitel,
    halbe Länge. Die kurze Seite stürzte ab, der Körper sah abgeschnitten aus.
    """

    # SON 28 mit Scheibenbremsaufnahme: die unsymmetrischste Bauform im Katalog.
    A_LINKS, A_RECHTS, RADIUS = 37.0, 19.0, 27.0

    def setUp(self):
        from speichenrechner.ui import bauteile
        self.bauteile = bauteile

    def _kugel(self, a_l=None, a_r=None):
        """Nur der Kugelabschnitt, ohne Kehle, Rippe und Achsband.

        Abgegrenzt über die Länge des Körpers, nicht über den Radius: die
        Hohlkehle daneben steigt wieder an und käme sonst mit ins Bild.
        """
        a_l = self.A_LINKS if a_l is None else a_l
        a_r = self.A_RECHTS if a_r is None else a_r
        stationen = self.bauteile._dynamo_stationen(a_l, a_r, self.RADIUS, self.RADIUS)
        mitte = (a_r - a_l) / 2.0
        halb = (a_l + a_r) / 2.0 * self.bauteile.DYNAMO["kugel_ende"]
        return [(x, r) for x, r in stationen if abs(x - mitte) <= halb + 1e-6]

    def test_kugel_ist_um_ihre_eigene_mitte_symmetrisch(self):
        kugel = self._kugel()
        mitte = (self.A_RECHTS - self.A_LINKS) / 2.0
        links = min(x for x, _ in kugel)
        rechts = max(x for x, _ in kugel)
        self.assertAlmostEqual(rechts - mitte, mitte - links, places=6,
                               msg="Die Kugel ist zur Seite verzogen")

    def test_scheitel_liegt_in_der_kugelmitte(self):
        kugel = self._kugel()
        hoechster = max(kugel, key=lambda p: p[1])
        self.assertAlmostEqual(hoechster[0], (self.A_RECHTS - self.A_LINKS) / 2.0,
                               places=6)

    def test_beide_haelften_sind_gleich_hoch_gewoelbt(self):
        """Gespiegelt an der Kugelmitte müssen sich die Radien decken."""
        kugel = self._kugel()
        mitte = (self.A_RECHTS - self.A_LINKS) / 2.0
        nach_x = {round(x - mitte, 6): r for x, r in kugel}
        for versatz, radius in nach_x.items():
            gegen = nach_x.get(round(-versatz, 6))
            if gegen is not None:
                self.assertAlmostEqual(radius, gegen, places=6)

    def test_der_scheitel_ist_gerundet_und_nicht_spitz(self):
        """Am Scheitel muss die Kontur flach auslaufen, sonst wird sie eckig."""
        kugel = sorted(self._kugel())
        mitte = (self.A_RECHTS - self.A_LINKS) / 2.0
        # Nur eine Flanke: über den Scheitel hinweg sind beide Enden gleich
        # hoch, die Differenz wäre null und der Test bewiese nichts.
        nah = [p for p in kugel if 0.0 <= p[0] - mitte < 3.0]
        rand = [p for p in kugel if 8.0 < p[0] - mitte < 14.0]
        self.assertTrue(nah and rand)

        def steigung(punkte):
            punkte = sorted(punkte)
            breite = punkte[-1][0] - punkte[0][0]
            return abs(punkte[-1][1] - punkte[0][1]) / breite if breite else 0.0

        self.assertLess(steigung(nah), steigung(rand) * 0.5,
                        "Der Scheitel fällt so steil ab wie die Flanke")

    def test_symmetrische_nabe_bleibt_mittig(self):
        """Bei gleichen Flanschabständen sitzt die Kugel auf der Nabenmitte."""
        kugel = self._kugel(a_l=28.0, a_r=28.0)
        hoechster = max(kugel, key=lambda p: p[1])
        self.assertAlmostEqual(hoechster[0], 0.0, places=6)

    def test_kugel_bleibt_zwischen_den_flanschen(self):
        """Sie darf die Rippen nicht überlaufen – sonst verschwindet der Flansch."""
        for a_l, a_r in ((37.0, 19.0), (28.0, 28.0), (19.0, 37.0), (50.0, 12.0)):
            with self.subTest(a=(a_l, a_r)):
                kugel = self.bauteile._dynamo_stationen(a_l, a_r, self.RADIUS, self.RADIUS)
                mitte = (a_r - a_l) / 2.0
                halb = (a_l + a_r) / 2.0 * self.bauteile.DYNAMO["kugel_ende"]
                self.assertLess(mitte + halb, a_r, "Kugel läuft über die rechte Rippe")
                self.assertGreater(mitte - halb, -a_l, "Kugel läuft über die linke Rippe")
                self.assertTrue(kugel)


if __name__ == "__main__":
    unittest.main()
