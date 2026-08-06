"""Zahlen in deutscher Schreibweise – ein Komma als Dezimaltrennzeichen.

Liegt bewusst in einem eigenen Modul, damit Berechnung, Bericht und Anzeige
dieselbe Schreibweise benutzen.
"""

from __future__ import annotations


def zahl(wert: float, stellen: int = 1) -> str:
    """``292.92`` → ``"292,92"``."""
    return f"{wert:.{stellen}f}".replace(".", ",")


def mm(wert: float, stellen: int = 1) -> str:
    """``292.92`` → ``"292,9 mm"``."""
    return f"{zahl(wert, stellen)} mm"


def grad(wert: float, stellen: int = 1) -> str:
    """``6.83`` → ``"6,8°"``."""
    return f"{zahl(wert, stellen)}°"
