"""Aufsicht auf das Laufrad: das Speichenbild.

Gezeichnet wird das Rad von der Seite – Felge, Nabenflansch und der Verlauf
aller Speichen beider Seiten. Eine Speiche ist hervorgehoben, dazu der
Sehnenwinkel an der Nabe: daran lässt sich die Kreuzungszahl ablesen.
"""

from __future__ import annotations

import math

from ..formatierung import grad
from ..modelle import Einspeichung, Felge, Nabe
from . import zeichnung as zg

RAND = 16


class Speichenbild(zg.ZeichenFlaeche):
    """Kreuzungsmuster beider Seiten übereinander."""

    def __init__(self) -> None:
        super().__init__(200, 190)
        self._nabe = Nabe()
        self._felge = Felge()
        self._einspeichung = Einspeichung()

    def setze_daten(self, nabe: Nabe, felge: Felge, einspeichung: Einspeichung) -> None:
        self._nabe, self._felge, self._einspeichung = nabe, felge, einspeichung
        self.queue_draw()

    # ------------------------------------------------------------- Zeichnung

    def zeichne(self, ctx, breite: float, hoehe: float, farben: zg.Farben) -> None:
        R = self._felge.erd / 2.0
        if R <= 0 or self._einspeichung.speichenzahl <= 0:
            return

        radius_px = min(breite, hoehe) / 2.0 - RAND
        if radius_px <= 20:
            return
        skala = radius_px / R

        ctx.save()
        ctx.translate(breite / 2.0, hoehe / 2.0)

        self._felge_zeichnen(ctx, farben, radius_px)
        self._seite_zeichnen(ctx, farben, skala, R, "rechts")
        self._seite_zeichnen(ctx, farben, skala, R, "links")
        self._nabe_zeichnen(ctx, farben, skala)
        self._hervorheben(ctx, farben, skala, R)

        ctx.restore()
        self._legende(ctx, farben, breite, hoehe)

    def _felge_zeichnen(self, ctx, farben: zg.Farben, radius_px: float) -> None:
        zg.setze(ctx, farben.linie, 3.0)
        ctx.arc(0, 0, radius_px, 0, 2 * math.pi)
        ctx.stroke()

    def _nabe_zeichnen(self, ctx, farben: zg.Farben, skala: float) -> None:
        for durchmesser in (self._nabe.flanschdurchmesser_links,
                            self._nabe.flanschdurchmesser_rechts):
            zg.setze(ctx, farben.linie, 1.5)
            ctx.arc(0, 0, max(durchmesser / 2.0 * skala, 2.0), 0, 2 * math.pi)
            ctx.stroke()

    def _seitendaten(self, seite: str) -> tuple[float, int]:
        if seite == "links":
            return self._nabe.flanschdurchmesser_links / 2.0, self._einspeichung.kreuzungen_links
        return self._nabe.flanschdurchmesser_rechts / 2.0, self._einspeichung.kreuzungen_rechts

    def _speiche(self, skala: float, R: float, seite: str, nummer: int) -> tuple:
        """Anfangs- und Endpunkt einer Speiche in Bildkoordinaten."""
        anzahl = self._einspeichung.speichenzahl // 2
        flansch_r, kreuzungen = self._seitendaten(seite)
        schritt = 2 * math.pi / anzahl
        alpha = math.radians(kreuzungen * 720.0 / self._einspeichung.speichenzahl)
        versatz = 0.0 if seite == "links" else schritt / 2.0

        winkel_nabe = nummer * schritt + versatz
        # Ziehende und schiebende Speichen laufen abwechselnd gegenläufig.
        richtung = 1 if nummer % 2 == 0 else -1
        winkel_felge = winkel_nabe + richtung * alpha

        return (
            (flansch_r * skala * math.cos(winkel_nabe), flansch_r * skala * math.sin(winkel_nabe)),
            (R * skala * math.cos(winkel_felge), R * skala * math.sin(winkel_felge)),
            winkel_nabe,
            winkel_felge,
        )

    def _seite_zeichnen(self, ctx, farben: zg.Farben, skala: float, R: float, seite: str) -> None:
        anzahl = self._einspeichung.speichenzahl // 2
        if anzahl <= 0:
            return
        # Die hervorgehobene Speiche soll sich abheben, deshalb laufen die
        # übrigen Speichen mit reduzierter Deckkraft.
        grund = farben.akzent if seite == "links" else farben.linie
        farbe = (grund[0], grund[1], grund[2], 0.55 if seite == "links" else 0.3)
        zg.setze(ctx, farbe, 1.2)
        for nummer in range(anzahl):
            (nx, ny), (fx, fy), _, _ = self._speiche(skala, R, seite, nummer)
            ctx.move_to(nx, ny)
            ctx.line_to(fx, fy)
            ctx.stroke()

    def _hervorheben(self, ctx, farben: zg.Farben, skala: float, R: float) -> None:
        """Eine linke Speiche dick zeichnen und den Sehnenwinkel bemaßen."""
        flansch_r, kreuzungen = self._seitendaten("links")
        (nx, ny), (fx, fy), winkel_nabe, winkel_felge = self._speiche(skala, R, "links", 0)

        zg.setze(ctx, farben.akzent, 3.0)
        zg.linie(ctx, nx, ny, fx, fy)

        if kreuzungen == 0:
            return

        # Radien zu Anfang und Ende, dazwischen der Winkelbogen.
        zg.hilfslinie(ctx, farben, 0, 0, fx, fy)
        zg.hilfslinie(ctx, farben, 0, 0, nx, ny)

        # Bogen deutlich außerhalb des Flansches, sonst liegt die Beschriftung
        # auf der Nabe.
        bogen = max(R * skala * 0.26, flansch_r * skala * 1.6)
        zg.setze(ctx, farben.akzent, 1.4)
        if winkel_felge >= winkel_nabe:
            ctx.arc(0, 0, bogen, winkel_nabe, winkel_felge)
        else:
            ctx.arc_negative(0, 0, bogen, winkel_nabe, winkel_felge)
        ctx.stroke()

        mitte = (winkel_nabe + winkel_felge) / 2.0
        zg.text(ctx, (bogen + 18) * math.cos(mitte), (bogen + 18) * math.sin(mitte),
                grad(abs(math.degrees(winkel_felge - winkel_nabe))), farben.akzent, 9.0, fett=True)

    def _legende(self, ctx, farben: zg.Farben, breite: float, hoehe: float) -> None:
        eintraege = (
            (f"links · {self._einspeichung.kreuzungen_links}-fach", farben.akzent),
            (f"rechts · {self._einspeichung.kreuzungen_rechts}-fach", farben.schwach),
        )
        y = hoehe - RAND - 12
        for beschriftung, farbe in eintraege:
            zg.setze(ctx, farbe, 3.0)
            zg.linie(ctx, RAND, y, RAND + 18, y)
            zg.text(ctx, RAND + 24, y, beschriftung, farben.text, 8.5, anker="links")
            y += 14
