"""Prüft, dass die erzeugten Handy-Daten zum Stand von ``data/`` passen.

``app/public/js/daten.js`` wird von ``werkzeuge/webdaten_erzeugen.py`` aus den
JSON-Dateien erzeugt. Wer die Tabelle erweitert und das Werkzeug vergisst, hätte
sonst am PC 230 Naben und auf dem Handy 218 – ohne dass es auffällt.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pc"))
sys.path.insert(0, str(WURZEL))

from werkzeuge import webdaten_erzeugen  # noqa: E402

DATEN_JS = WURZEL / "app" / "public" / "js" / "daten.js"


class TestWebdaten(unittest.TestCase):
    def test_datei_ist_vorhanden(self):
        self.assertTrue(DATEN_JS.exists(), f"{DATEN_JS} fehlt")

    def test_stand_ist_aktuell(self):
        """Sonst zeigt das Handy einen anderen Katalog als der PC."""
        erwartet = webdaten_erzeugen.erzeugen()
        vorhanden = DATEN_JS.read_text(encoding="utf-8")
        self.assertEqual(
            vorhanden, erwartet,
            "app/public/js/daten.js ist veraltet – "
            "python3 werkzeuge/webdaten_erzeugen.py ausführen",
        )

    def test_alle_naben_sind_drin(self):
        from speichenrechner import katalog
        self.assertEqual(len(webdaten_erzeugen._naben()), len(katalog.lade().naben))

    def test_felgentypen_und_fussnote(self):
        from speichenrechner import felgenkunde
        typen, fussnoten = webdaten_erzeugen._felgen()
        kunde = felgenkunde.lade()
        self.assertEqual(len(typen), len(kunde.typen))
        self.assertEqual(len(fussnoten), len(kunde.fussnoten))

    def test_vorlagen_tragen_ihre_bauform(self):
        """Ohne Bauart und Aufnahme filtert die Handy-Fassung die Vorlagen falsch."""
        naben, felgen = webdaten_erzeugen._vorlagen()
        self.assertTrue(naben)
        self.assertTrue(felgen)
        for nabe in naben:
            with self.subTest(nabe=nabe["name"]):
                self.assertIn("art", nabe)
                self.assertIn("aufnahme", nabe)


if __name__ == "__main__":
    unittest.main()
