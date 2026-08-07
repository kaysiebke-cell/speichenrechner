"""Prüft die Einzeldatei der Handy-Fassung.

``app/speichenrechner-handy.html`` enthält die ganze Anwendung: Stylesheet,
Rechnung, Katalog, Daten. Sie ist der Weg aufs Handy, der weder Server noch
GitHub braucht – also muss sie zum Stand von ``app/public/`` passen und ohne
Module auskommen, sonst läuft sie unter ``file://`` nicht.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "pc"))

from werkzeuge import einzeldatei_erzeugen  # noqa: E402

DATEI = WURZEL / "app" / "speichenrechner-handy.html"


class TestEinzeldatei(unittest.TestCase):
    def setUp(self):
        self.assertTrue(DATEI.exists(), f"{DATEI} fehlt")
        self.inhalt = DATEI.read_text(encoding="utf-8")

    def test_stand_ist_aktuell(self):
        """Sonst liegt auf dem Handy eine andere Fassung als in app/public/."""
        self.assertEqual(
            self.inhalt, einzeldatei_erzeugen.erzeugen(),
            "app/speichenrechner-handy.html ist veraltet – "
            "python3 werkzeuge/einzeldatei_erzeugen.py ausführen",
        )

    def test_keine_module_und_keine_fremden_dateien(self):
        """Unter file:// verweigert der Browser Module und externe Verweise."""
        for verboten in ("import ", "export ", 'src="js/', 'href="css/', "manifest.json"):
            with self.subTest(verboten=verboten):
                self.assertNotIn(verboten, self.inhalt)

    def test_keine_doppelten_namen_ueber_die_module(self):
        """Zwei Module dürfen nicht denselben Namen auf oberster Ebene tragen.

        Getrennt sind die Module gegeneinander abgeschottet – zusammengefügt
        landen sie in **einem** Scope, und die spätere Deklaration überschreibt
        die frühere. Das schlägt still zu: `speiche.js` und `katalog.js` hatten
        beide ein `masse`, die Handy-Fassung rief daraufhin die falsche
        Funktion auf und zeigte nur noch Striche statt Längen. Nichts an dieser
        Datei sah dabei verdächtig aus, denn einzeln lief jedes Modul.
        """
        namen = {}
        doppelt = []
        muster = re.compile(
            r"^(?:export\s+)?(?:function|const|let|var|class)\s+([A-Za-z_$][\w$]*)", re.M
        )
        for name_modul in einzeldatei_erzeugen.MODULE:
            quelltext = (einzeldatei_erzeugen.QUELLE / name_modul).read_text(encoding="utf-8")
            for treffer in muster.finditer(quelltext):
                name = treffer.group(1)
                if name in namen and namen[name] != name_modul:
                    doppelt.append(f"{name} in {namen[name]} und {name_modul}")
                namen.setdefault(name, name_modul)
        self.assertEqual(doppelt, [], "Namen kollidieren in der Einzeldatei: "
                                      + ", ".join(doppelt))

    def test_alles_ist_drin(self):
        for muster in ("<style>", "NABEN = [", "FELGENTYPEN = [",
                       "function berechne", "artenMitAnzahl"):
            with self.subTest(muster=muster):
                self.assertIn(muster, self.inhalt)

    def test_katalog_ist_vollstaendig(self):
        """Alle Naben und Felgentypen müssen in der Datei stehen."""
        from speichenrechner import felgenkunde, katalog
        for eintrag in katalog.lade().naben:
            with self.subTest(nabe=eintrag.modell):
                self.assertIn(eintrag.modell, self.inhalt)
        for typ in felgenkunde.lade().typen:
            with self.subTest(typ=typ.name):
                self.assertIn(typ.name, self.inhalt)


if __name__ == "__main__":
    unittest.main()
