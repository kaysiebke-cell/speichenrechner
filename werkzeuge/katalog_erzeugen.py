#!/usr/bin/env python3
"""Erzeugt ``data/naben_katalog.json`` aus der Hersteller-Tabelle.

Aufruf::

    python3 werkzeuge/katalog_erzeugen.py quellen/naben_modelle.xlsx

Die Tabelle hat ein Blatt je Nabenart (Nabendynamo, Nabenschaltung,
Vorderradnabe, Hinterradnabe …). Die Spalten werden **über ihre Überschriften**
zugeordnet, nicht über feste Positionen – eine umsortierte oder erweiterte
Tabelle bricht damit nicht.

Blätter wie „Nabe mit Kassette“ sind Querlisten: sie führen Naben auf, die
schon in einem anderen Blatt stehen. Solche Zeilen werden zusammengeführt, nicht
doppelt aufgenommen; das Blatt liefert dafür einen Hinweis auf die
Ritzelaufnahme.

Übernommen werden die Angaben **im Wortlaut**; ausgewertet wird erst beim Laden
in :mod:`speichenrechner.tabelle`.

Gelesen wird ohne fremde Bibliotheken – ein .xlsx ist ein ZIP mit XML darin,
und openpyxl ist auf Linux Mint nicht überall vorhanden.
"""

from __future__ import annotations

import collections
import json
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))          # für werkzeuge.*
sys.path.insert(0, str(WURZEL / "pc"))   # für speichenrechner.*

from speichenrechner import tabelle  # noqa: E402

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

#: Textfelder eines Eintrags in der Reihenfolge der Tabelle.
FELDER = (
    "lochzahl", "einbaubreite", "achstyp", "bremse",
    "speichenloch", "flanschabstand", "flanschdurchmesser", "freilauf",
)

#: Zeilenanfänge, die keine Nabe beschreiben.
KEINE_NABE = ("gesamt:", "hinweis", "alle ", "kettenschaltungs", "hersteller")

#: Ab dieser Zeile listet ein Blatt etwas anderes auf. Der Text stammt aus der
#: Tabelle: „folgende Systeme sind KEINE einspeichbaren Laufradnaben, sondern
#: Tretlager-Getriebe“.
ABSCHNITT_KEIN_LAUFRAD = ("keine einspeichbaren", "kein laufradnaben", "tretlager")

#: Bauart für alles hinter dieser Marke.
KEIN_LAUFRAD = "Tretlagergetriebe"

#: Blattname → Bauart.
BAUARTEN = {
    "nabendynamo": "Dynamo",
    "nabenschaltung": "Nabenschaltung",
    "vorderradnabe": "Vorderrad",
    "hinterradnabe": "Hinterrad",
}

#: Querlisten: Blattname → Ritzelaufnahme, falls die Freilaufspalte schweigt.
QUERLISTEN = {
    "nabe mit schraubkranz": "Schraubkranz",
    "nabe mit kassette": "Kassette",
    "nabe mit steckritzel": "Steckritzel",
}


def _spaltennummer(bezug: str) -> int:
    buchstaben = "".join(z for z in bezug if z.isalpha())
    nummer = 0
    for zeichen in buchstaben:
        nummer = nummer * 26 + (ord(zeichen) - 64)
    return nummer - 1


def _blatt_lesen(archiv: zipfile.ZipFile, ziel: str) -> list[list[str]]:
    baum = ET.fromstring(archiv.read(ziel.lstrip("/")))
    zeilen = []
    for zeile in baum.iter(NS + "row"):
        werte: dict[int, str] = {}
        for zelle in zeile.iter(NS + "c"):
            if zelle.get("t") == "inlineStr":
                inhalt = zelle.findtext(".//" + NS + "t") or ""
            else:
                inhalt = zelle.findtext(NS + "v") or ""
            if inhalt:
                werte[_spaltennummer(zelle.get("r"))] = inhalt.strip()
        if werte:
            zeilen.append([werte.get(i, "") for i in range(max(werte) + 1)])
    return zeilen


def _feld_zu_titel(titel: str) -> str:
    """Ordnet eine Spaltenüberschrift einem Feld zu – tolerant geschrieben."""
    text = titel.lower()
    if "hersteller" in text:
        return "hersteller"
    if "modell" in text:
        return "modell"
    if "lochzahl" in text:
        return "lochzahl"
    if "einbaubreite" in text or "old" in text:
        return "einbaubreite"
    if "achstyp" in text or "achse" in text:
        return "achstyp"
    if "bremse" in text or "bremsaufnahme" in text:
        return "bremse"
    if "speichenloch" in text:
        return "speichenloch"
    if "flanschabstand" in text:
        return "flanschabstand"
    if "flansch" in text and any(
        wort in text for wort in ("ø", "durchmesser", "lochkreis", "teilkreis", "pcd")
    ):
        return "flanschdurchmesser"
    if any(wort in text for wort in ("freilauf", "ritzel", "kassette")):
        return "freilauf"
    return ""


def _kopfzeile(zeilen: list[list[str]]) -> tuple[int, dict[int, str]]:
    """Sucht die Zeile mit den Überschriften und ordnet die Spalten zu.

    Eine Beschreibungszeile wie „… + neu ergänzte Shimano-Modelle“ enthält das
    Wort „Modell“ ebenfalls. Als Kopfzeile gilt deshalb nur, was mehrere
    Spalten trifft und dabei Hersteller **und** Modell nennt.
    """
    for nummer, zeile in enumerate(zeilen[:10]):
        zuordnung = {}
        for spalte, titel in enumerate(zeile):
            # Überschriften sind kurz; Fließtext ist keine Überschrift.
            if len(titel) > 40:
                continue
            feld = _feld_zu_titel(titel)
            if feld:
                zuordnung[spalte] = feld
        gefunden = set(zuordnung.values())
        if {"hersteller", "modell"} <= gefunden and len(gefunden) >= 4:
            return nummer, zuordnung
    return -1, {}


def _ist_nabe(hersteller: str, modell: str) -> bool:
    if not modell or not hersteller:
        return False
    return not hersteller.lower().startswith(KEINE_NABE)


def einlesen(pfad: Path) -> list[dict]:
    """Liest die Tabelle; mehrfach gelistete Naben werden zusammengeführt."""
    archiv = zipfile.ZipFile(pfad)
    mappe = ET.fromstring(archiv.read("xl/workbook.xml"))
    bezuege = {
        r.get("Id"): r.get("Target")
        for r in ET.fromstring(archiv.read("xl/_rels/workbook.xml.rels"))
    }

    saetze: dict[tuple[str, str], dict] = {}
    for blatt in mappe.find(NS + "sheets"):
        name = blatt.get("name")
        zeilen = _blatt_lesen(archiv, bezuege[blatt.get(REL + "id")])
        kopf, spalten = _kopfzeile(zeilen)
        if kopf < 0:
            continue

        schlicht = name.lower()
        bauart = BAUARTEN.get(schlicht, "")
        quer = QUERLISTEN.get(schlicht, "")

        abschnitt_bauart = bauart
        for zeile in zeilen[kopf + 1:]:
            erste = (zeile[0] if zeile else "").lower()
            if any(marke in erste for marke in ABSCHNITT_KEIN_LAUFRAD):
                # Alles ab hier ist kein Laufradbauteil mehr.
                abschnitt_bauart = KEIN_LAUFRAD
                continue

            werte = {
                feld: (zeile[nummer].strip() if nummer < len(zeile) else "")
                for nummer, feld in spalten.items()
            }
            hersteller = werte.get("hersteller", "")
            modell = werte.get("modell", "")
            if not _ist_nabe(hersteller, modell):
                continue

            schluessel = (hersteller, modell)
            satz = saetze.setdefault(schluessel, {
                "hersteller": hersteller, "modell": modell,
                "art": abschnitt_bauart, "aufnahme_blatt": "",
                **{feld: "" for feld in FELDER},
            })

            # Erstes Blatt gewinnt; Querlisten füllen nur Lücken.
            if abschnitt_bauart and not satz["art"]:
                satz["art"] = abschnitt_bauart
            if quer and not satz["aufnahme_blatt"]:
                satz["aufnahme_blatt"] = quer
            for feld in FELDER:
                wert = werte.get(feld, "")
                if not satz[feld] and not tabelle.ist_leer(wert):
                    satz[feld] = wert

    for satz in saetze.values():
        if not satz["art"]:
            satz["art"] = "Hinterrad"
    return list(saetze.values())


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    quelle = Path(argv[1])
    ziel = Path(__file__).resolve().parent.parent / "data" / "naben_katalog.json"

    eintraege = einlesen(quelle)
    ziel.write_text(
        json.dumps({"quelle": quelle.name, "naben": eintraege}, indent=1, ensure_ascii=False),
        encoding="utf-8",
    )

    arten = collections.Counter(e["art"] for e in eintraege)
    hersteller = {e["hersteller"] for e in eintraege}
    fertig = sum(
        1 for e in eintraege
        if tabelle.seitenwerte(e["flanschabstand"], True)
        and tabelle.seitenwerte(e["flanschdurchmesser"], False)
    )

    print(f"{len(eintraege)} Naben von {len(hersteller)} Herstellern → {ziel}")
    print(f"  mit Speichenloch-Ø: {sum(1 for e in eintraege if e['speichenloch'])}")
    print(f"  mit Einbaubreite:   {sum(1 for e in eintraege if e['einbaubreite'])}")
    print(f"  rechenfertig:       {fertig}")
    print("  Bauarten: " + ", ".join(f"{a} {n}" for a, n in arten.most_common()))
    if arten.get(KEIN_LAUFRAD):
        print(f"  davon {arten[KEIN_LAUFRAD]} Tretlager-Getriebe – nicht einspeichbar")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
