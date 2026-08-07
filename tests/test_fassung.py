"""Prüft, dass die Fassungsnummer überall dieselbe ist.

Sie steht an vier Stellen: in der Android-Hülle (``versionName``), in der
PC-Anwendung (``VERSION``), in der Paketzeile des README und – beim
Veröffentlichen – im Git-Tag. Laufen sie auseinander, meldet die App etwas
anderes, als das Release verspricht.

Der wunde Punkt ist ``versionCode``: Android vergleibt **nur** ihn, um zu
entscheiden, ob eine APK eine Aktualisierung der installierten ist. Bleibt er
gleich, verweigert das Gerät die Installation über die alte App – und zwar
wortkarg. Genau das ist bei v1.6.0 passiert: der Tag saß auf einem Stand, in
dem die Nummern noch auf 1.5.0 standen.

Den Abgleich mit dem Git-Tag macht der Ablauf beim Bauen
(``.github/workflows/android.yml``); hier bleibt, was ohne Git prüfbar ist.
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "pc"))


def _lies(datei: str, muster: str) -> str:
    text = (WURZEL / datei).read_text(encoding="utf-8")
    treffer = re.search(muster, text)
    if treffer is None:
        raise AssertionError(f"{datei}: „{muster}“ nicht gefunden")
    return treffer.group(1)


class TestFassung(unittest.TestCase):
    def test_ueberall_dieselbe_nummer(self):
        from speichenrechner import VERSION

        gradle = _lies("app/android/app/build.gradle", r'versionName\s+"([^"]+)"')
        readme = _lies("README.md", r"de\.speichenrechner\.app\s+(\S+)")

        self.assertEqual(gradle, VERSION,
                         "versionName in build.gradle und VERSION der PC-Fassung "
                         "müssen gleich sein")
        self.assertEqual(readme, VERSION,
                         "Die Paketzeile im README nennt eine andere Fassung als "
                         "die PC-Anwendung")

    def test_versioncode_ist_eine_zahl_ueber_null(self):
        """Ohne gültigen versionCode nimmt Android die APK gar nicht erst an."""
        code = _lies("app/android/app/build.gradle", r"versionCode\s+(\d+)")
        self.assertGreater(int(code), 0)

    def test_fassung_sieht_aus_wie_eine_fassung(self):
        from speichenrechner import VERSION

        self.assertRegex(VERSION, r"^\d+\.\d+\.\d+$")


if __name__ == "__main__":
    unittest.main()
