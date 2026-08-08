"""Prüft das Installationsskript – vor allem die Pfade im Menüeintrag.

Anlass: der Projektordner zog in „Projeckt Ordner" um. Der Menüeintrag trug den
Pfad ohne Anführungszeichen, der Starter zerlegte ihn am Leerzeichen und suchte
eine Datei „…/Desktop/Projeckt". Die Anwendung ließ sich nicht mehr starten,
obwohl an ihr nichts fehlte.
"""

from __future__ import annotations

import re
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
INSTALL = WURZEL / "pc" / "install.sh"


class TestInstallationsskript(unittest.TestCase):
    def setUp(self):
        self.assertTrue(INSTALL.exists(), f"{INSTALL} fehlt")
        self.inhalt = INSTALL.read_text(encoding="utf-8")

    def test_exec_pfad_steht_in_anfuehrungszeichen(self):
        """Sonst bricht jeder Ordner mit Leerzeichen den Menüeintrag."""
        zeile = re.search(r"s\|@EXEC@\|([^|]*)\|", self.inhalt)
        self.assertIsNotNone(zeile, "Ersetzung für @EXEC@ nicht gefunden")
        self.assertIn('\\"$PROJEKT/speichenrechner.py\\"', zeile.group(1))

    def test_menueeintrag_mit_leerzeichen_im_pfad(self):
        """Ein Ordner mit Leerzeichen muss zu einem aufrufbaren Eintrag führen."""
        with tempfile.TemporaryDirectory() as ordner:
            projekt = Path(ordner) / "Mein Ordner" / "Speichenrechner"
            (projekt / "pc").mkdir(parents=True)
            (projekt / "data").mkdir()
            (projekt / "pc" / "speichenrechner.py").write_text("#\n", encoding="utf-8")
            (projekt / "data" / "speichenrechner.svg").write_text("<svg/>", encoding="utf-8")
            vorlage = WURZEL / "data" / "de.speichenrechner.Speichenrechner.desktop.in"
            (projekt / "data" / vorlage.name).write_text(
                vorlage.read_text(encoding="utf-8"), encoding="utf-8")
            (projekt / "pc" / "install.sh").write_text(self.inhalt, encoding="utf-8")

            umgebung = {"HOME": ordner, "PATH": "/usr/bin:/bin", "XDG_DATA_HOME": ordner}
            subprocess.run(["bash", str(projekt / "pc" / "install.sh")],
                           env=umgebung, capture_output=True, check=False)

            eintrag = Path(ordner) / "applications" / "de.speichenrechner.Speichenrechner.desktop"
            self.assertTrue(eintrag.exists(), "Menüeintrag wurde nicht angelegt")
            exec_zeile = next(z[5:] for z in eintrag.read_text(encoding="utf-8").splitlines()
                              if z.startswith("Exec="))
            teile = shlex.split(exec_zeile)
            self.assertEqual(len(teile), 2, f"Exec zerfällt in {teile}")
            self.assertTrue(Path(teile[1]).exists(), f"{teile[1]} gibt es nicht")


if __name__ == "__main__":
    unittest.main()
