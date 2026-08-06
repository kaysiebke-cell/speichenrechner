"""Prüft den Service Worker der Handy-Fassung.

Anlass: der Cache hielt die alte Seite fest. Der Cache-Name trug die Fassung
``v1``, während sich `index.html` und die Skripte änderten – auf dem Handy
blieb dadurch der Nabenkatalog unsichtbar, obwohl er längst da war. Diese
Tests halten beides fest: **jede** Datei muss im Cache stehen, und wer public/
ändert, muss die Fassung hochzählen.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
PUBLIC = WURZEL / "app" / "public"
SW = PUBLIC / "sw.js"


class TestServiceWorker(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SW.exists(), f"{SW} fehlt")
        self.inhalt = SW.read_text(encoding="utf-8")

    def _dateien(self) -> list[str]:
        block = re.search(r"const DATEIEN = \[(.*?)\];", self.inhalt, re.S)
        self.assertIsNotNone(block, "DATEIEN-Liste nicht gefunden")
        return re.findall(r'"([^"]+)"', block.group(1))

    def test_jede_datei_steht_im_cache(self):
        """Fehlt eine, fehlt sie auf dem Handy – aber erst ohne Netz."""
        gelistet = set(self._dateien())
        for pfad in sorted(PUBLIC.rglob("*")):
            if not pfad.is_file():
                continue
            name = pfad.relative_to(PUBLIC).as_posix()
            if name in ("sw.js", "package.json"):
                continue      # der Worker selbst und die Node-Notiz
            with self.subTest(datei=name):
                self.assertIn(name, gelistet,
                              f"{name} steht nicht in DATEIEN in sw.js")

    def test_alle_gelisteten_dateien_gibt_es(self):
        for name in self._dateien():
            if name == ".":
                continue
            with self.subTest(datei=name):
                self.assertTrue((PUBLIC / name).exists(), f"{name} fehlt in app/public/")

    def test_fassung_ist_hochgezaehlt(self):
        """Die Fassung muss über 1 stehen – v1 war der Stand mit dem Fehler."""
        treffer = re.search(r"const FASSUNG = (\d+);", self.inhalt)
        self.assertIsNotNone(treffer, "FASSUNG nicht gefunden")
        self.assertGreater(int(treffer.group(1)), 1)

    def test_cache_name_traegt_die_fassung(self):
        self.assertIn("`speichenrechner-v${FASSUNG}`", self.inhalt)

    def test_seiten_kommen_aus_dem_netz_zuerst(self):
        """Sonst bleibt eine neue Fassung hinter dem Cache stecken."""
        self.assertIn("istSeitenaufruf", self.inhalt)
        self.assertIn("Netz zuerst", self.inhalt)


if __name__ == "__main__":
    unittest.main()
