#!/usr/bin/env python3
"""Erzeugt ``data/naben_modellreihen.json`` aus der Zuordnungstabelle.

Aufruf::

    python3 werkzeuge/modellreihen_erzeugen.py daten_quelle_modellreihen.xlsx

Die Tabelle ordnet die einzelnen Naben zu Modellreihen zusammen: aus 260
Katalogzeilen werden 186 Reihen. Sie enthält **keine Maße** – Flanschabstand
und Flansch-Ø stehen weiter im Katalog. Hier entsteht nur die Zuordnung
``Hersteller|Modell → Modellreihe``, damit die Auswahlliste kurz wird.

Gelesen wird ohne fremde Bibliotheken, wie beim Katalogwerkzeug: ein .xlsx ist
ein ZIP mit XML darin. Anders als die alte Herstellertabelle legt diese Datei
ihren Text **im Blatt** ab (``t="inlineStr"``) statt in der gemeinsamen
Zeichenkettentabelle. Wer nur letztere liest, bekommt lauter leere Zellen –
und schreibt am Ende eine leere Datei.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
sys.path.insert(0, str(WURZEL / "pc"))

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

#: Wie das Blatt heißt, in dem die Zuordnung steht.
BLATT_ZUORDNUNG = "Zuordnung"

#: Spalten, die dort erwartet werden.
SPALTEN = ("Hersteller", "Modell", "Modellreihe")

ZIEL = WURZEL / "data" / "naben_modellreihen.json"


def _zellwert(zelle, zeichenketten: list[str]) -> str:
    """Text einer Zelle – gleich, ob inline oder aus der Zeichenkettentabelle."""
    if zelle.get("t") == "inlineStr":
        return "".join(t.text or "" for t in zelle.iter(f"{NS}t")).strip()
    wert = zelle.find(f"{NS}v")
    if wert is None:
        return ""
    if zelle.get("t") == "s":
        return zeichenketten[int(wert.text)].strip()
    return (wert.text or "").strip()


def _zeichenketten(archiv: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archiv.namelist():
        return []
    wurzel = ET.fromstring(archiv.read("xl/sharedStrings.xml"))
    return ["".join(t.text or "" for t in si.iter(f"{NS}t"))
            for si in wurzel.iter(f"{NS}si")]


def _blatt(archiv: zipfile.ZipFile, gesucht: str) -> ET.Element:
    """Das Blatt mit diesem Namen, über die Reihenfolge in der Mappe."""
    mappe = ET.fromstring(archiv.read("xl/workbook.xml"))
    namen = [b.get("name") for b in mappe.iter(f"{NS}sheet")]
    if gesucht not in namen:
        raise SystemExit(f"Blatt „{gesucht}“ fehlt – vorhanden: {', '.join(namen)}")
    nummer = namen.index(gesucht) + 1
    return ET.fromstring(archiv.read(f"xl/worksheets/sheet{nummer}.xml"))


def zuordnung_lesen(quelle: Path) -> dict[str, str]:
    """``{"Hersteller|Modell": "Modellreihe"}`` aus der Tabelle."""
    with zipfile.ZipFile(quelle) as archiv:
        ketten = _zeichenketten(archiv)
        blatt = _blatt(archiv, BLATT_ZUORDNUNG)

    zeilen = [[_zellwert(c, ketten) for c in r.iter(f"{NS}c")]
              for r in blatt.iter(f"{NS}row")]
    if not zeilen:
        raise SystemExit(f"Blatt „{BLATT_ZUORDNUNG}“ ist leer")

    kopf = zeilen[0]
    fehlend = [s for s in SPALTEN if s not in kopf]
    if fehlend:
        raise SystemExit(f"Spalten fehlen: {', '.join(fehlend)} – gefunden: {kopf}")
    spalte = {name: kopf.index(name) for name in SPALTEN}

    zuordnung: dict[str, str] = {}
    for zeile in zeilen[1:]:
        if len(zeile) <= max(spalte.values()):
            continue
        hersteller = zeile[spalte["Hersteller"]]
        modell = zeile[spalte["Modell"]]
        reihe = zeile[spalte["Modellreihe"]]
        if not (hersteller and modell and reihe):
            continue
        zuordnung[f"{hersteller}|{modell}"] = reihe
    return zuordnung


def main(argumente: list[str]) -> int:
    if len(argumente) != 1:
        print(__doc__)
        return 2
    quelle = Path(argumente[0])
    if not quelle.exists():
        print(f"{quelle} gibt es nicht")
        return 1

    zuordnung = zuordnung_lesen(quelle)
    if not zuordnung:
        print("Keine Zuordnung gefunden – nichts geschrieben.")
        return 1

    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(json.dumps(zuordnung, ensure_ascii=False, indent=1,
                               sort_keys=True) + "\n", encoding="utf-8")

    reihen = sorted(set(zuordnung.values()))
    print(f"{len(zuordnung)} Naben → {len(reihen)} Modellreihen → {ZIEL}")

    # Gegenprobe am Katalog: was findet sich nicht wieder?
    from speichenrechner import katalog
    naben = katalog.lade().naben
    ohne = [e for e in naben if e.schluessel not in zuordnung]
    print(f"  im Katalog: {len(naben)} Naben, {len(naben) - len(ohne)} zugeordnet")
    if ohne:
        print(f"  ohne Modellreihe ({len(ohne)}):")
        for eintrag in ohne:
            print(f"    {eintrag.hersteller} | {eintrag.modell}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
