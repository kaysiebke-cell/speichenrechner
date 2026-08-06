"""Ablageorte nach XDG-Standard – von Vorlagen und Einstellungen genutzt."""

from __future__ import annotations

import os
from pathlib import Path

ORDNERNAME = "speichenrechner"


def konfig_verzeichnis() -> Path:
    """``$XDG_CONFIG_HOME/speichenrechner`` bzw. ``~/.config/speichenrechner``."""
    basis = os.environ.get("XDG_CONFIG_HOME")
    wurzel = Path(basis) if basis else Path.home() / ".config"
    return wurzel / ORDNERNAME


def projekt_verzeichnis() -> Path:
    """Wurzel des Projekts – für Icon, Katalogdaten und mitgelieferte Dateien.

    Die Anwendung liegt in ``pc/speichenrechner/``, die gemeinsamen Daten aber
    in ``data/`` neben ``pc/`` und ``app/``: sie versorgen beide Fassungen.
    Deshalb zwei Ebenen nach oben statt einer.
    """
    return Path(__file__).resolve().parents[2]


def icon_pfad() -> Path:
    return projekt_verzeichnis() / "data" / "speichenrechner.svg"
