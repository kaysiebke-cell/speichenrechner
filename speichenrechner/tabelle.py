"""Auswertung der Herstellertabelle – Schreibweisen in Zahlen übersetzen.

Die Tabelle ist von Hand gepflegt, entsprechend vielfältig sind die Angaben:
``47,5 (22,5/25)``, ``58 (symmetrisch)``, ``Ø100``, ``33/20``, ``k. A.``.
Hier steht die Auswertung **einmal** – der Konverter benutzt sie beim Einlesen
der Tabelle, das Bearbeitungsfenster beim Nachtragen. So können beide gar
nicht auseinanderlaufen.
"""

from __future__ import annotations

import re

#: Werte, die „nichts bekannt“ bedeuten.
LEER = {"", "k. a.", "k.a.", "—", "-", "n/a", "entfällt", "entfaellt"}

#: Angaben, die von der Lochzahl abhängen und deshalb offen bleiben.
MEHRDEUTIG = ("bzw", "je nach", "abhängig")


def ist_leer(text: str) -> bool:
    schlicht = (text or "").strip().lower()
    return schlicht in LEER or schlicht.startswith("k. a.") or schlicht.startswith("k.a.")


def zahlen(text: str) -> list[float]:
    """Alle Zahlen aus einer Angabe, Komma wie Punkt als Dezimaltrennzeichen."""
    if ist_leer(text):
        return []
    return [float(t.replace(",", ".")) for t in re.findall(r"\d+(?:[.,]\d+)?", text)]


def ganze_zahlen(text: str, von: int = 8, bis: int = 64) -> list[int]:
    """Lochzahlen aus ``20/24/28/32/36`` – nur plausible Werte."""
    return [int(z) for z in zahlen(text) if von <= z <= bis and float(int(z)) == z]


def masse(text: str, von: float = 50.0, bis: float = 250.0) -> list[float]:
    """Einbaubreiten aus ``135/145 (OLD)`` – nur plausible Werte."""
    return [z for z in zahlen(text) if von <= z <= bis]


def erste_zahl(text: str) -> float | None:
    werte = zahlen(text)
    return werte[0] if werte else None


def seitenwerte(text: str, ist_abstand: bool) -> tuple[float, float] | None:
    """Liest Angaben wie ``47,5 (22,5/25)``, ``33/20``, ``58 (symmetrisch)``.

    Bei ``ist_abstand`` gilt eine **einzelne** Zahl als Maß über beide Flansche
    und wird halbiert; beim Durchmesser gilt sie für beide Seiten. Angaben, die
    von der Lochzahl abhängen, bleiben absichtlich offen.
    """
    if ist_leer(text):
        return None
    if any(wort in text.lower() for wort in MEHRDEUTIG):
        return None

    sauber = text.replace("*", "").replace("Ø", " ").strip()

    # Das Paar in Klammern ist die genauere Angabe: „50 (25/25)“
    klammer = re.search(r"\(([^)]*)\)", sauber)
    if klammer:
        paar = zahlen(klammer.group(1))
        if len(paar) >= 2:
            return paar[0], paar[1]
        davor = zahlen(sauber[: klammer.start()])
        if davor:
            return _aufteilen(davor[0], ist_abstand)
        return None

    werte = zahlen(sauber)
    if len(werte) >= 2:
        return werte[0], werte[1]
    if len(werte) == 1:
        return _aufteilen(werte[0], ist_abstand)
    return None


def _aufteilen(wert: float, ist_abstand: bool) -> tuple[float, float]:
    return (wert / 2, wert / 2) if ist_abstand else (wert, wert)
