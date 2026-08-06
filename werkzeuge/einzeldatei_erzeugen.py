#!/usr/bin/env python3
"""Packt die Handy-Fassung in **eine** HTML-Datei.

Aufruf::

    python3 werkzeuge/einzeldatei_erzeugen.py

Ergebnis: ``app/speichenrechner-handy.html`` – eine Datei, die alles enthält:
Stylesheet, Rechnung, Katalog, Daten. Sie braucht keinen Server, kein Netz und
kein GitHub. Auf das Handy kopieren (Kabel, Speicherkarte, an sich selbst
schicken) und im Browser öffnen, fertig.

Warum überhaupt? Die normale Fassung besteht aus mehreren Dateien und benutzt
ES-Module. Unter ``file://`` verweigert der Browser die: dort gilt jede Datei
als eigener Ursprung, und ``import`` schlägt fehl. Deshalb werden hier die
Module zusammengefügt und die ``import``- und ``export``-Zeilen entfernt – aus
vier Modulen wird ein Skript, das auch von der Festplatte läuft.

Was dabei wegfällt: der Service Worker (braucht einen Server) und der Eintrag
auf dem Startbildschirm über das Manifest. Gerechnet wird genauso.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
QUELLE = WURZEL / "app" / "public"
ZIEL = WURZEL / "app" / "speichenrechner-handy.html"

#: Reihenfolge zählt: wer benutzt wird, muss vorher stehen.
MODULE = ("js/daten.js", "js/rechnen.js", "js/katalog.js", "js/zeichnung.js", "js/app.js")


def _ohne_module(quelltext: str) -> str:
    """Entfernt ``import``- und ``export``-Anweisungen.

    Die Module sind alle von uns und benutzen eindeutige Namen; zusammengefügt
    in einem Skript sehen sie einander ohnehin. Weg müssen nur die Anweisungen,
    die es außerhalb eines Moduls nicht gibt.
    """
    # Mehrzeilige Importe mit geschweiften Klammern und einzeilige gleichermaßen.
    ohne = re.sub(r"^import\s+[^;]*?;\s*$", "", quelltext, flags=re.M | re.S)
    ohne = re.sub(r"^import\s*\{[^}]*\}\s*from\s*[^;]*;\s*$", "", ohne, flags=re.M | re.S)
    # „export const X“ → „const X“, „export function“ → „function“
    ohne = re.sub(r"^export\s+(?=(const|let|var|function|class)\b)", "", ohne, flags=re.M)
    return ohne


def erzeugen() -> str:
    seite = (QUELLE / "index.html").read_text(encoding="utf-8")
    stil = (QUELLE / "css" / "stil.css").read_text(encoding="utf-8")

    teile = []
    for name in MODULE:
        quelltext = (QUELLE / name).read_text(encoding="utf-8")
        teile.append(f"// ===== {name} " + "=" * (66 - len(name)) + "\n\n"
                     + _ohne_module(quelltext).strip() + "\n")
    skript = "\n\n".join(teile)

    # Stylesheet einsetzen
    seite = seite.replace(
        '<link rel="stylesheet" href="css/stil.css">',
        f"<style>\n{stil}\n</style>",
    )
    # Manifest und Icons brauchen einen Server – in der Einzeldatei weglassen.
    for zeile in (
        '<link rel="manifest" href="manifest.json">',
        '<link rel="icon" href="icons/icon-192.png" sizes="192x192">',
        '<link rel="apple-touch-icon" href="icons/icon-192.png">',
    ):
        seite = seite.replace(zeile + "\n", "")
    # Modul-Skript durch das zusammengefügte ersetzen
    seite = seite.replace(
        '<script type="module" src="js/app.js"></script>',
        f"<script>\n{skript}\n</script>",
    )
    # Der Service Worker läuft nur über einen Server; der Aufruf entfällt.
    seite = re.sub(
        r'// Ohne Netz nutzbar.*?\n\}\n', "", seite, flags=re.S)

    hinweis = (
        "<!-- Erzeugt von werkzeuge/einzeldatei_erzeugen.py – alles in einer Datei.\n"
        "     Quelle ist app/public/. Änderungen hier gehen beim nächsten Lauf\n"
        "     verloren. -->\n"
    )
    return seite.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + hinweis, 1)


def main() -> int:
    if not QUELLE.exists():
        print(f"{QUELLE} fehlt", file=sys.stderr)
        return 1
    inhalt = erzeugen()
    ZIEL.write_text(inhalt, encoding="utf-8")
    print(f"{ZIEL.relative_to(WURZEL)} – {len(inhalt) / 1024:.0f} KB, "
          f"{inhalt.count(chr(10)) + 1} Zeilen")
    for verboten in ("import ", "export ", 'src="js/'):
        if verboten in inhalt:
            print(f"  ACHTUNG: „{verboten}“ steht noch in der Datei – "
                  "unter file:// läuft das nicht.")
            return 1
    print("  keine Module, keine externen Dateien – läuft von der Festplatte")
    return 0


if __name__ == "__main__":
    sys.exit(main())
