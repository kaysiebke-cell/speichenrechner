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
            (projekt / "pc" / "data").mkdir(parents=True)
            (projekt / "pc" / "speichenrechner.py").write_text("#\n", encoding="utf-8")
            (projekt / "pc" / "data" / "speichenrechner.svg").write_text(
                "<svg/>", encoding="utf-8")
            vorlage = WURZEL / "pc" / "data" / "de.speichenrechner.Speichenrechner.desktop.in"
            (projekt / "pc" / "data" / vorlage.name).write_text(
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


class TestOrdnertrennung(unittest.TestCase):
    """Jede Fassung hat ihren Ordner; geteilt wird nur, was beide brauchen.

    ``pc/`` und ``app/`` sollen für sich stehen. ``data/`` liegt bewusst
    daneben statt in einer der beiden: dort stehen die Kataloge und die
    Prüfwerte, mit denen sich beide Fassungen gegeneinander absichern. Zwei
    Kopien davon würden genau das Auseinanderlaufen erzeugen, das die
    Prüfwerte verhindern sollen.
    """

    def test_der_pc_ordner_traegt_sein_eigenes_zubehoer(self):
        for name in ("data/speichenrechner.svg",
                     "data/de.speichenrechner.Speichenrechner.desktop.in",
                     "speichenrechner.py", "install.sh"):
            with self.subTest(datei=name):
                self.assertTrue((WURZEL / "pc" / name).exists(),
                                f"pc/{name} fehlt")

    def test_die_wurzel_bleibt_aufgeraeumt(self):
        """Oben liegt nur, was den Einstieg zeigt – alles andere hat einen Ordner."""
        erlaubt = {"README.md", "speichenrechner.py", ".gitignore"}
        lose = {p.name for p in WURZEL.iterdir()
                if p.is_file() and not p.name.startswith(".~")}
        self.assertEqual(lose - erlaubt, set(),
                         f"gehört in einen Ordner: {sorted(lose - erlaubt)}")

    def test_geteilte_daten_enthalten_nur_daten(self):
        """Kein Icon, keine Bildschirmfotos, keine Startdateien in data/."""
        fremd = [p.name for p in (WURZEL / "data").iterdir()
                 if p.suffix.lower() not in (".json",)]
        self.assertEqual(fremd, [], f"gehört nicht in data/: {fremd}")

    def test_die_handyfassung_braucht_data_nicht_zur_laufzeit(self):
        """Sie bekommt ihre Daten erzeugt – sonst liefe sie offline nicht."""
        for datei in (WURZEL / "app" / "public").rglob("*"):
            if datei.suffix not in (".js", ".html", ".json"):
                continue
            text = datei.read_text(encoding="utf-8", errors="ignore")
            for zeile in text.splitlines():
                nackt = zeile.strip()
                if nackt.startswith(("//", "*", "/*", "#")):
                    continue          # Kommentare dürfen data/ erwähnen
                with self.subTest(datei=datei.name):
                    self.assertNotIn("../data/", nackt)

    def test_bilder_liegen_im_eigenen_ordner(self):
        bilder = list((WURZEL / "doku" / "bilder").glob("*.png"))
        self.assertTrue(bilder, "doku/bilder/ ist leer")

    def test_readme_zeigt_auf_die_bilder(self):
        text = (WURZEL / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("(data/", text, "README verweist noch auf data/*.png")
        for bild in re.findall(r"\((doku/bilder/[^)]+)\)", text):
            with self.subTest(bild=bild):
                self.assertTrue((WURZEL / bild).exists(), f"{bild} fehlt")
