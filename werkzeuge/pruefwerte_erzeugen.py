#!/usr/bin/env python3
"""Erzeugt ``data/pruefwerte.json`` – gemeinsame Prüfwerte für PC und Handy.

Aufruf::

    python3 werkzeuge/pruefwerte_erzeugen.py

Die Rechnung gibt es zweimal: in Python für die PC-Anwendung und in JavaScript
für die Handy-Version. Zwei Fassungen derselben Formeln driften auseinander,
wenn nichts sie zusammenhält. Deshalb rechnet **Python** die Fälle vor und
schreibt Eingaben samt Ergebnis in eine Datei; die JavaScript-Seite muss
dieselben Zahlen liefern (``werkzeuge/pruefwerte_js.mjs``).

Die Fälle sind bewusst gemischt: symmetrisch und unsymmetrisch, radial bis
4-fach, 2:1-Verteilung, Felgenversatz, kleine Kinderräder und der Abgleich
gegen Spokomat.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))          # für werkzeuge.*
sys.path.insert(0, str(WURZEL / "pc"))   # für speichenrechner.*

from speichenrechner import berechnung  # noqa: E402
from speichenrechner.modelle import Einspeichung, Felge, Nabe  # noqa: E402

#: Ein Fall ist ``(Name, Nabe, Felge, Einspeichung, Rundungsschritt)``.
FAELLE = (
    ("Vorderrad symmetrisch 32/3-fach",
     Nabe("v", 38.0, 38.0, 38.0, 38.0, 2.4), Felge("f", 600.0), Einspeichung(32, 3, 3), 1.0),
    ("Hinterrad unsymmetrisch 32/3-fach",
     Nabe("h", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0), Einspeichung(32, 3, 3), 1.0),
    ("radial 24/0-fach",
     Nabe("r", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 602.0), Einspeichung(24, 0, 0), 1.0),
    ("4-fach 36 Speichen",
     Nabe("k", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 596.0), Einspeichung(36, 4, 4), 1.0),
    ("gemischte Kreuzung 32, links 3 rechts 2",
     Nabe("m", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0), Einspeichung(32, 3, 2), 1.0),
    ("2:1-Verteilung 24 Speichen",
     Nabe("z", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0),
     Einspeichung(24, 2, 2, "2:1"), 1.0),
    ("Felgenversatz nach links",
     Nabe("o", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0, -3.0), Einspeichung(32, 3, 3), 1.0),
    ("Rohloff symmetrisch 32/3-fach",
     Nabe("ro", 100.0, 100.0, 29.0, 29.0, 2.7), Felge("f", 596.0), Einspeichung(32, 3, 3), 1.0),
    ("SON 28 mit 16-Zoll-Felge",
     Nabe("son", 54.0, 54.0, 28.0, 26.5, 2.0), Felge("f", 328.0), Einspeichung(32, 3, 3), 1.0),
    ("12-Zoll-Kinderrad 28/2-fach",
     Nabe("kind", 38.0, 38.0, 30.0, 30.0, 2.4), Felge("f", 180.0), Einspeichung(28, 2, 2), 1.0),
    ("Rundung auf 0,5 mm",
     Nabe("h", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0), Einspeichung(32, 3, 3), 0.5),
    ("Rundung auf 2 mm",
     Nabe("h", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 600.0), Einspeichung(32, 3, 3), 2.0),
    # Abgleich mit Spokomat: dieselben Eingaben wie in tests/test_speiche.py.
    ("Spokomat-Abgleich 36/3-fach",
     Nabe("sp", 45.0, 45.0, 35.0, 20.0, 2.6), Felge("f", 602.0), Einspeichung(36, 3, 3), 1.0),
    ("Schraubkranznabe White Industries ENO",
     Nabe("eno", 60.0, 60.0, 32.0, 32.0), Felge("f", 602.0), Einspeichung(36, 3, 3), 1.0),
)

#: So viele Stellen müssen übereinstimmen. Enger als das ist bei Fließkomma
#: über zwei Sprachen hinweg nicht sinnvoll.
STELLEN = 9


def _satz(name, nabe, felge, einspeichung, schritt) -> dict:
    ergebnis = berechnung.berechne(nabe, felge, einspeichung, schritt)
    return {
        "name": name,
        "eingabe": {
            "flanschdurchmesser_links": nabe.flanschdurchmesser_links,
            "flanschdurchmesser_rechts": nabe.flanschdurchmesser_rechts,
            "flanschabstand_links": nabe.flanschabstand_links,
            "flanschabstand_rechts": nabe.flanschabstand_rechts,
            "speichenloch": nabe.speichenloch,
            "erd": felge.erd,
            "versatz": felge.versatz,
            "speichenzahl": einspeichung.speichenzahl,
            "kreuzungen_links": einspeichung.kreuzungen_links,
            "kreuzungen_rechts": einspeichung.kreuzungen_rechts,
            "verteilung": einspeichung.verteilung,
            "schritt": schritt,
        },
        "erwartet": {
            "laenge_links": round(ergebnis.links.laenge, STELLEN),
            "laenge_rechts": round(ergebnis.rechts.laenge, STELLEN),
            "bestell_links": ergebnis.links.laenge_gerundet,
            "bestell_rechts": ergebnis.rechts.laenge_gerundet,
            "speichenwinkel_links": round(ergebnis.links.speichenwinkel, STELLEN),
            "speichenwinkel_rechts": round(ergebnis.rechts.speichenwinkel, STELLEN),
            "felgenwinkel_links": round(ergebnis.links.felgenwinkel, STELLEN),
            "felgenwinkel_rechts": round(ergebnis.rechts.felgenwinkel, STELLEN),
            "sehnenwinkel_links": round(ergebnis.links.sehnenwinkel, STELLEN),
            "sehnenwinkel_rechts": round(ergebnis.rechts.sehnenwinkel, STELLEN),
            "lochabstand_links": round(ergebnis.links.lochabstand, STELLEN),
            "lochabstand_rechts": round(ergebnis.rechts.lochabstand, STELLEN),
            "speichen_links": ergebnis.links.speichen,
            "speichen_rechts": ergebnis.rechts.speichen,
            "spannung_links_prozent": round(ergebnis.spannung_links_prozent, STELLEN),
            "spannung_rechts_prozent": round(ergebnis.spannung_rechts_prozent, STELLEN),
        },
    }


def _katalog() -> dict:
    """Die ausgewerteten Angaben jeder Nabe und jedes Felgentyps.

    Nicht nur ein paar Stichproben: die Schreibweisen der Herstellertabelle
    sind über Jahre gewachsen (``47,5 (22,5/25)``, ``58 (symmetrisch)``,
    ``Ø100``, ``entfällt (Singlespeed, kein Freilauf)``). Wenn die
    JavaScript-Fassung eine davon anders liest als Python, steht in der
    Handy-Fassung eine falsche Nabe – deshalb wird **jede** geprüft.
    """
    from speichenrechner import felgenkunde, katalog

    naben = []
    for eintrag in katalog.lade().naben:
        naben.append({
            "schluessel": eintrag.schluessel,
            "flanschabstaende": list(eintrag.flanschabstaende or ()) or None,
            "flanschdurchmesser_paar": list(eintrag.flanschdurchmesser_paar or ()) or None,
            "speichenloch_mm": eintrag.speichenloch_mm,
            "lochzahlen": eintrag.lochzahlen,
            "einbaubreiten": eintrag.einbaubreiten,
            "aufnahme": eintrag.aufnahme,
            "merkmale": list(eintrag.merkmale),
            "hat_flanschmasse": eintrag.hat_flanschmasse,
            "einspeichbar": eintrag.einspeichbar,
            "bezeichnung": eintrag.bezeichnung,
        })

    felgen = []
    for typ in felgenkunde.lade().typen:
        bereich = typ.spannungsbereich
        felgen.append({
            "name": typ.name,
            "materialien": list(typ.materialien),
            "oesen_stufe": typ.oesen_stufe,
            "spannungsbereich": list(bereich) if bereich else None,
            "nur_ab_20_zoll": typ.nur_ab_20_zoll,
        })

    return {
        "naben": naben,
        "felgen": felgen,
        "arten": [list(paar) for paar in katalog.lade().arten_mit_anzahl()],
        "hersteller": [list(paar) for paar in katalog.lade().hersteller_mit_anzahl()],
    }


def erzeugen() -> dict:
    return {
        "hinweis": ("Von werkzeuge/pruefwerte_erzeugen.py aus der Python-Rechnung "
                    "erzeugt. Die JavaScript-Fassung muss dieselben Zahlen liefern."),
        "stellen": STELLEN,
        "faelle": [_satz(*fall) for fall in FAELLE],
        "katalog": _katalog(),
    }


def main() -> int:
    ziel = Path(__file__).resolve().parent.parent / "data" / "pruefwerte.json"
    daten = erzeugen()
    ziel.write_text(json.dumps(daten, indent=1, ensure_ascii=False), encoding="utf-8")
    k = daten["katalog"]
    print(f"{len(daten['faelle'])} Rechenfälle, {len(k['naben'])} Naben und "
          f"{len(k['felgen'])} Felgentypen → {ziel}")
    for satz in daten["faelle"]:
        erwartet = satz["erwartet"]
        print(f"  {satz['name']:44} {erwartet['bestell_links']:6.1f} / "
              f"{erwartet['bestell_rechts']:6.1f} mm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
