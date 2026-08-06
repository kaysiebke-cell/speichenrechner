"""Speichern und Laden der zuletzt benutzten Eingaben.

Beim nächsten Start steht damit wieder das Laufrad in der Maske, an dem
zuletzt gerechnet wurde.
"""

from __future__ import annotations

import json

from .modelle import Einspeichung, Felge, Nabe, Speichensatz
from .pfade import konfig_verzeichnis

EINSTELLUNGEN_DATEI = "einstellungen.json"


def _datei():
    return konfig_verzeichnis() / EINSTELLUNGEN_DATEI


def lade() -> tuple[Nabe, Felge, Einspeichung, Speichensatz, float]:
    """Liefert ``(nabe, felge, einspeichung, speichen, rundungsschritt)``.

    Fehlt oder fällt die Datei aus, kommen die Vorgabewerte zurück.
    """
    standard = (Nabe(), Felge(), Einspeichung(), Speichensatz(), 1.0)
    pfad = _datei()
    if not pfad.exists():
        return standard

    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return standard
    if not isinstance(daten, dict):
        return standard

    try:
        nabe = Nabe.from_dict(daten.get("nabe", {}))
        felge = Felge.from_dict(daten.get("felge", {}))
        einspeichung = Einspeichung.from_dict(daten.get("einspeichung", {}))
        speichen = Speichensatz.from_dict(daten.get("speichen", {}))
        schritt = float(daten.get("rundungsschritt", 1.0))
    except (TypeError, ValueError):
        return standard

    return nabe, felge, einspeichung, speichen, schritt


def speichere(
    nabe: Nabe,
    felge: Felge,
    einspeichung: Einspeichung,
    speichen: Speichensatz,
    schritt: float,
) -> None:
    """Schreibt den aktuellen Stand; Fehler werden bewusst geschluckt."""
    pfad = _datei()
    inhalt = {
        "nabe": nabe.as_dict(),
        "felge": felge.as_dict(),
        "einspeichung": einspeichung.as_dict(),
        "speichen": speichen.as_dict(),
        "rundungsschritt": schritt,
    }
    try:
        pfad.parent.mkdir(parents=True, exist_ok=True)
        pfad.write_text(json.dumps(inhalt, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass
