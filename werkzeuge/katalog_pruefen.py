#!/usr/bin/env python3
"""Vergleicht den erzeugten Katalog Zelle für Zelle mit der Herstellertabelle.

Aufruf::

    python3 werkzeuge/katalog_pruefen.py daten_quelle_naben.xlsx

Meldet, was beim Einlesen verlorenging oder falsch ankam:

* Zeilen der Tabelle, die im Katalog fehlen (und umgekehrt)
* Zellen, deren Text nicht übernommen wurde
* Angaben, die der Rechner nicht auswerten konnte, obwohl etwas dasteht
* Einordnungen, die unplausibel wirken – etwa eine Vorderradnabe mit
  Ritzelaufnahme oder eine Hinterradnabe ganz ohne

Rückgabewert 1, wenn etwas gefunden wurde. Damit fällt auf, wenn eine
erweiterte Tabelle anders gelesen wird als gedacht.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from speichenrechner import katalog as nabenkatalog  # noqa: E402
from speichenrechner import tabelle  # noqa: E402
from werkzeuge.katalog_erzeugen import einlesen  # noqa: E402

#: Bauarten ohne Ritzel – dort wäre eine Aufnahme ein Widerspruch.
OHNE_RITZEL = {"Vorderrad", "Dynamo"}


def _vergleiche_bestand(tabellensaetze, katalog) -> list[str]:
    aus_tabelle = {f"{s['hersteller']}|{s['modell']}" for s in tabellensaetze}
    # Selbst angelegte und nachgetragene Naben stehen absichtlich nicht in der
    # Tabelle – sie kommen aus dem Bearbeitungsfenster bzw. aus
    # data/naben_zusatz.json und sind dort mit Quelle vermerkt.
    im_katalog = {e.schluessel for e in katalog.naben if e.aus_tabelle}

    meldungen = []
    for schluessel in sorted(aus_tabelle - im_katalog):
        meldungen.append(f"fehlt im Katalog: {schluessel}")
    for schluessel in sorted(im_katalog - aus_tabelle):
        meldungen.append(f"steht im Katalog, aber nicht in der Tabelle: {schluessel}")
    return meldungen


def _vergleiche_zellen(tabellensaetze, katalog) -> list[str]:
    nach_schluessel = {e.schluessel: e for e in katalog.naben}
    felder = [feld for feld, _ in nabenkatalog.SPALTEN]

    meldungen = []
    for satz in tabellensaetze:
        eintrag = nach_schluessel.get(f"{satz['hersteller']}|{satz['modell']}")
        if eintrag is None or eintrag.ergaenzt or not eintrag.aus_tabelle:
            continue  # fehlt schon oben bzw. wurde bewusst überschrieben
        for feld in felder:
            erwartet = satz.get(feld, "")
            vorhanden = getattr(eintrag, feld)
            if erwartet != vorhanden:
                meldungen.append(
                    f"{eintrag.schluessel} · {feld}: Tabelle {erwartet!r} → "
                    f"Katalog {vorhanden!r}"
                )
    return meldungen


def _pruefe_auswertung(katalog) -> list[str]:
    """Text da, aber keine Zahl herausbekommen – meist ein Tippfehler."""
    meldungen = []
    for eintrag in katalog.naben:
        if not eintrag.aus_tabelle:
            continue   # nachgetragen, mit Quellenangabe – nicht Sache der Tabelle
        proben = (
            ("Flanschabstand", eintrag.flanschabstand, eintrag.flanschabstaende),
            ("Flansch-Ø", eintrag.flanschdurchmesser, eintrag.flanschdurchmesser_paar),
            ("Speichenloch", eintrag.speichenloch, eintrag.speichenloch_mm),
            ("Lochzahl", eintrag.lochzahl, eintrag.lochzahlen or None),
            ("Einbaubreite", eintrag.einbaubreite, eintrag.einbaubreiten or None),
        )
        for name, text, wert in proben:
            if text and wert is None and not any(w in text.lower() for w in tabelle.MEHRDEUTIG):
                meldungen.append(f"{eintrag.schluessel} · {name}: {text!r} nicht auswertbar")
    return meldungen


def _pruefe_einordnung(katalog) -> list[str]:
    meldungen = []
    for eintrag in katalog.naben:
        if not eintrag.einspeichbar:
            continue  # Tretlager-Getriebe haben weder Flansch noch Ritzel
        merkmale = set(eintrag.merkmale)
        if merkmale & OHNE_RITZEL and eintrag.aufnahme:
            meldungen.append(
                f"{eintrag.schluessel}: {eintrag.art} mit Ritzelaufnahme "
                f"{eintrag.aufnahme!r} – widersprüchlich"
            )
        if eintrag.art == "Hinterrad" and not eintrag.aufnahme and eintrag.freilauf:
            meldungen.append(
                f"{eintrag.schluessel}: Hinterrad ohne erkannte Ritzelaufnahme – "
                f"Freilaufspalte sagt {eintrag.freilauf[:48]!r}"
            )
        if not eintrag.merkmale:
            meldungen.append(f"{eintrag.schluessel}: keinem Merkmal zugeordnet")
    return meldungen


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2

    tabellensaetze = einlesen(Path(argv[1]))
    nabenkatalog.neu_laden()
    katalog = nabenkatalog.lade()

    print(f"Tabelle: {len(tabellensaetze)} Zeilen · Katalog: {len(katalog.naben)} Naben")

    gruppen = (
        ("Bestand", _vergleiche_bestand(tabellensaetze, katalog)),
        ("Zellen", _vergleiche_zellen(tabellensaetze, katalog)),
        ("Auswertung", _pruefe_auswertung(katalog)),
        ("Einordnung", _pruefe_einordnung(katalog)),
    )

    gesamt = 0
    for titel, meldungen in gruppen:
        print(f"\n{titel}: {len(meldungen)} Auffälligkeiten")
        for meldung in meldungen[:25]:
            print(f"  {meldung}")
        if len(meldungen) > 25:
            print(f"  … und {len(meldungen) - 25} weitere")
        gesamt += len(meldungen)

    print(f"\n{'Nichts gefunden.' if gesamt == 0 else f'{gesamt} Auffälligkeiten insgesamt.'}")
    return 0 if gesamt == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
