#!/usr/bin/env python3
"""Erzeugt ``data/felgen_katalog.json`` aus der Felgentabelle.

Aufruf::

    python3 werkzeuge/felgen_erzeugen.py daten_quelle_felgen.xlsx

Die Tabelle hat ein Blatt mit einer Zeile je Felgentyp. Anders als bei den
Naben stehen dort keine Maße, sondern Eigenschaften: Bauform, Material,
Ösung, Einsatzbereich. Übernommen wird der Wortlaut; gedeutet wird erst beim
Laden in :mod:`speichenrechner.felgenkunde`.

Zeilen, die mit „Hinweis“ beginnen, sind kein Felgentyp – sie werden als
Fußnote mitgenommen und stehen in der Anwendung unter der Auswahl.

Gelesen wird wie bei den Naben ohne fremde Bibliotheken.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))          # für werkzeuge.*
sys.path.insert(0, str(WURZEL / "pc"))   # für speichenrechner.*

from werkzeuge.katalog_erzeugen import NS, REL, _blatt_lesen  # noqa: E402

import xml.etree.ElementTree as ET  # noqa: E402
import zipfile  # noqa: E402

#: Textfelder eines Felgentyps in der Reihenfolge der Tabelle.
FELDER = ("kategorie", "material", "beschreibung", "einsatz", "oesung", "kindergroessen")

#: Zeilenanfänge, die keinen Felgentyp beschreiben, aber erhalten bleiben.
FUSSNOTE = ("hinweis",)


def _feld_zu_titel(titel: str) -> str:
    """Ordnet eine Spaltenüberschrift einem Feld zu – tolerant geschrieben."""
    text = titel.lower()
    if "felgentyp" in text or text == "typ":
        return "name"
    if "kategorie" in text:
        return "kategorie"
    if "material" in text:
        return "material"
    if "beschreibung" in text:
        return "beschreibung"
    if "einsatz" in text:
        return "einsatz"
    if "ösung" in text or "speichenlochverst" in text:
        return "oesung"
    if "kindergrö" in text or "kindergro" in text:
        return "kindergroessen"
    return ""


def _kopfzeile(zeilen: list[list[str]]) -> tuple[int, dict[int, str]]:
    """Sucht die Zeile mit den Überschriften.

    Wie bei den Naben gilt: eine Beschreibungszeile nennt einzelne dieser
    Wörter auch. Als Kopfzeile zählt nur, was den Felgentyp **und** mehrere
    weitere Spalten trifft.
    """
    for nummer, zeile in enumerate(zeilen[:10]):
        zuordnung = {}
        for spalte, titel in enumerate(zeile):
            if len(titel) > 40:
                continue
            feld = _feld_zu_titel(titel)
            if feld:
                zuordnung[spalte] = feld
        gefunden = set(zuordnung.values())
        if "name" in gefunden and len(gefunden) >= 3:
            return nummer, zuordnung
    return -1, {}


def einlesen(pfad: Path) -> tuple[list[dict], list[str]]:
    """Liefert ``(Felgentypen, Fußnoten)`` im Wortlaut der Tabelle."""
    archiv = zipfile.ZipFile(pfad)
    mappe = ET.fromstring(archiv.read("xl/workbook.xml"))
    bezuege = {
        r.get("Id"): r.get("Target")
        for r in ET.fromstring(archiv.read("xl/_rels/workbook.xml.rels"))
    }

    typen: list[dict] = []
    fussnoten: list[str] = []
    bekannt: set[str] = set()

    for blatt in mappe.find(NS + "sheets"):
        zeilen = _blatt_lesen(archiv, bezuege[blatt.get(REL + "id")])
        kopf, spalten = _kopfzeile(zeilen)
        if kopf < 0:
            continue

        for zeile in zeilen[kopf + 1:]:
            erste = (zeile[0] if zeile else "").strip()
            if not erste:
                continue
            if erste.lower().startswith(FUSSNOTE):
                fussnoten.append(erste)
                continue

            werte = {
                feld: (zeile[nummer].strip() if nummer < len(zeile) else "")
                for nummer, feld in spalten.items()
            }
            name = werte.get("name", "")
            if not name or name in bekannt:
                continue
            bekannt.add(name)
            typen.append({"name": name, **{feld: werte.get(feld, "") for feld in FELDER}})

    return typen, fussnoten


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    quelle = Path(argv[1])
    ziel = Path(__file__).resolve().parent.parent / "data" / "felgen_katalog.json"

    typen, fussnoten = einlesen(quelle)
    ziel.write_text(
        json.dumps(
            {"quelle": quelle.name, "felgen": typen, "fussnoten": fussnoten},
            indent=1, ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    kategorien = collections.Counter(t["kategorie"] for t in typen)
    print(f"{len(typen)} Felgentypen → {ziel}")
    print("  Kategorien: " + ", ".join(f"{k or '–'} {n}" for k, n in kategorien.most_common()))
    print(f"  mit Ösungsangabe:   {sum(1 for t in typen if t['oesung'])}")
    print(f"  mit Kindergrößen:   {sum(1 for t in typen if t['kindergroessen'])}")
    print(f"  Fußnoten:           {len(fussnoten)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
