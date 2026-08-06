"""Prüft die Einzeldatei der Handy-Fassung.

``app/speichenrechner-handy.html`` enthält die ganze Anwendung: Stylesheet,
Rechnung, Katalog, Daten. Sie ist der Weg aufs Handy, der weder Server noch
GitHub braucht – also muss sie zum Stand von ``app/public/`` passen und ohne
Module auskommen, sonst läuft sie unter ``file://`` nicht.
"""

from __future__ import annotations

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
