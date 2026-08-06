#!/usr/bin/env python3
"""Erzeugt ``public/js/daten.js`` aus den JSON-Daten in ``data/``.

Aufruf::

    python3 werkzeuge/webdaten_erzeugen.py

Warum überhaupt erzeugen? Die Handy-Fassung braucht Nabenkatalog und
Felgentypen **im Ordner public/**, denn nur der wird von GitHub Pages
ausgeliefert und nur der landet in den Assets der Android-App. Die Daten dort
ein zweites Mal zu pflegen, wäre der Anfang vom Auseinanderdriften.

Deshalb bleibt ``data/`` die einzige Quelle, und daraus entsteht **eine**
Datei: ein JavaScript-Modul mit denselben Angaben. Das hat drei Vorteile
gegenüber einem ``fetch`` auf die JSON-Dateien:

* es lädt sofort mit der Seite, auch ohne Netz und ohne Service-Worker-Trick,
* es funktioniert auch unter ``file://`` – wichtig für die Android-App,
* eine Datei weniger, die beim Ausliefern vergessen werden kann.

Dass die erzeugte Datei zum Stand von ``data/`` passt, prüft
``tests/test_webdaten.py``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))          # für werkzeuge.*
sys.path.insert(0, str(WURZEL / "pc"))   # für speichenrechner.*

ZIEL = WURZEL / "app" / "public" / "js" / "daten.js"

#: Felder, die die Handy-Fassung von einer Nabe braucht. Der Rest der Tabelle
#: (Achstyp, Bremsaufnahme …) bleibt weg: er wird dort nicht angezeigt und
#: würde die Datei nur größer machen.
NABENFELDER = (
    "hersteller", "modell", "art", "lochzahl", "einbaubreite", "bremse",
    "speichenloch", "flanschabstand", "flanschdurchmesser", "freilauf", "quelle",
)

#: Felder eines Felgentyps.
FELGENFELDER = (
    "name", "kategorie", "material", "beschreibung", "einsatz", "oesung", "kindergroessen",
)


def _lade(name: str) -> dict:
    pfad = WURZEL / "data" / name
    if not pfad.exists():
        return {}
    return json.loads(pfad.read_text(encoding="utf-8"))


def _naben() -> list[dict]:
    """Naben aus der Tabelle und aus den Nachträgen, in einer Liste."""
    saetze = list(_lade("naben_katalog.json").get("naben", []))
    saetze += list(_lade("naben_zusatz.json").get("naben", []))

    naben = []
    bekannt = set()
    for satz in saetze:
        if not satz.get("modell"):
            continue
        schluessel = (satz.get("hersteller", ""), satz["modell"])
        if schluessel in bekannt:
            continue        # die Tabelle kommt zuerst und gewinnt
        bekannt.add(schluessel)
        naben.append({feld: satz.get(feld, "") for feld in NABENFELDER})
    return naben


def _felgen() -> tuple[list[dict], list[str]]:
    daten = _lade("felgen_katalog.json")
    typen = [
        {feld: satz.get(feld, "") for feld in FELGENFELDER}
        for satz in daten.get("felgen", [])
        if satz.get("name")
    ]
    return typen, list(daten.get("fussnoten", []))


def _vorlagen() -> list[dict]:
    """Die mitgelieferten Vorlagen – dieselben wie in der PC-Anwendung."""
    from speichenrechner import vorlagen as v

    naben = [
        {
            "name": n.name,
            "flanschdurchmesser_links": n.flanschdurchmesser_links,
            "flanschdurchmesser_rechts": n.flanschdurchmesser_rechts,
            "flanschabstand_links": n.flanschabstand_links,
            "flanschabstand_rechts": n.flanschabstand_rechts,
            "speichenloch": n.speichenloch,
            "art": n.art,
            "aufnahme": n.aufnahme,
        }
        for n in v.NABEN_VORLAGEN
    ]
    felgen = [{"name": f.name, "erd": f.erd, "versatz": f.versatz} for f in v.FELGEN_VORLAGEN]
    return naben, felgen


def erzeugen() -> str:
    naben = _naben()
    felgentypen, fussnoten = _felgen()
    nabenvorlagen, felgenvorlagen = _vorlagen()

    def block(name: str, wert) -> str:
        return f"export const {name} = {json.dumps(wert, ensure_ascii=False, indent=0)};\n\n"

    kopf = (
        "// Erzeugt von werkzeuge/webdaten_erzeugen.py – nicht von Hand ändern.\n"
        "//\n"
        "// Quelle sind die JSON-Dateien in data/. Wer hier etwas ändert, verliert\n"
        "// es beim nächsten Lauf des Werkzeugs; die Tabelle und naben_zusatz.json\n"
        "// sind die Quelle der Wahrheit.\n\n"
    )
    return (
        kopf
        + block("NABEN", naben)
        + block("FELGENTYPEN", felgentypen)
        + block("FELGEN_FUSSNOTEN", fussnoten)
        + block("NABEN_VORLAGEN", nabenvorlagen)
        + block("FELGEN_VORLAGEN", felgenvorlagen)
    )


def main() -> int:
    inhalt = erzeugen()
    ZIEL.write_text(inhalt, encoding="utf-8")
    naben = _naben()
    felgen, fussnoten = _felgen()
    nabenvorlagen, felgenvorlagen = _vorlagen()
    print(f"{ZIEL.relative_to(WURZEL)} – {len(inhalt) / 1024:.0f} KB")
    print(f"  Naben            {len(naben)}")
    print(f"  Felgentypen      {len(felgen)} (+{len(fussnoten)} Fußnote)")
    print(f"  Nabenvorlagen    {len(nabenvorlagen)}")
    print(f"  Felgenvorlagen   {len(felgenvorlagen)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
