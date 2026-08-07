#!/usr/bin/env python3
"""Startet die PC-Anwendung – von der Wurzel des Projekts aus.

Die Anwendung selbst liegt in ``pc/``, seit PC- und Handy-Fassung getrennte
Ordner haben. Damit der gewohnte Aufruf weiter geht, bleibt dieses Skript hier
liegen und reicht nur durch:

    python3 speichenrechner.py            # von hier
    python3 pc/speichenrechner.py         # dasselbe, direkt

Dasselbe gilt für alte Verknüpfungen und Menüeinträge, die noch auf diesen Pfad
zeigen: sie funktionieren weiter.
"""

import runpy
import sys
from pathlib import Path

ECHTES_SKRIPT = Path(__file__).resolve().parent / "pc" / "speichenrechner.py"

if not ECHTES_SKRIPT.exists():
    sys.exit(f"{ECHTES_SKRIPT} fehlt – ist der Ordner pc/ vorhanden?")

# run_name="__main__", damit sich das Skript verhält wie direkt aufgerufen.
runpy.run_path(str(ECHTES_SKRIPT), run_name="__main__")
