"""Querschnitt durch den Nabenbereich – zeigt Speichenwinkel und Mittigkeit.

Die Skizze ist **durchgehend maßstäblich**, waagerecht wie senkrecht. Weil ein
ganzes Laufrad bei diesem Maßstab meterhoch wäre, zeigt sie nur den Ausschnitt
um die Nabe: Achse, Nabenkörper, beide Flansche und den Anfang der Speichen.
Die Speichen laufen mit ihrem echten Winkel nach oben zur Felge.

Gezeichnet wird die in die Radebene abgewickelte Speiche, deshalb ist die
senkrechte Bezugsstrecke nicht ``R − r``, sondern die Projektion
``√(R² + r² − 2·R·r·cos α)``. Nur so ergibt sich der echte Speichenwinkel.
"""

from __future__ import annotations

import math

from ..berechnung import sehnenwinkel_seite
from ..formatierung import grad, mm
from ..modelle import Einspeichung, Felge, Nabe
from . import zeichnung as zg

RAND_SEITE = 44
RAND_OBEN = 34
RAND_UNTEN = 76

NABENKOERPER_MM = 9.0


class Querschnitt(zg.ZeichenFlaeche):
    """Schnitt quer durch den Nabenbereich, von hinten gesehen."""

    def __init__(self) -> None:
        super().__init__(220, 200)
        self._nabe = Nabe()
        self._felge = Felge()
        self._einspeichung = Einspeichung()

    def setze_daten(self, nabe: Nabe, felge: Felge, einspeichung: Einspeichung) -> None:
        self._nabe, self._felge, self._einspeichung = nabe, felge, einspeichung
        self.queue_draw()

    # -------------------------------------------------------------- Geometrie

    def _seite(self, seite: str) -> tuple[float, float, int, int]:
        """``(Flanschradius, Flanschabstand, Kreuzungen, Speichen)`` einer Seite."""
        if seite == "links":
            return (
                self._nabe.flanschdurchmesser_links / 2.0,
                self._nabe.flanschabstand_links,
                self._einspeichung.kreuzungen_links,
                self._einspeichung.speichen_links,
            )
        return (
            self._nabe.flanschdurchmesser_rechts / 2.0,
            self._nabe.flanschabstand_rechts,
            self._einspeichung.kreuzungen_rechts,
            self._einspeichung.speichen_rechts,
        )

    def _projektion(self, seite: str) -> float:
        """Länge der Speiche, projiziert in die Radebene."""
        R = self._felge.erd / 2.0
        r, _, kreuzungen, anzahl = self._seite(seite)
        if anzahl <= 0:
            return max(R - r, 1.0)
        a = math.radians(sehnenwinkel_seite(anzahl, kreuzungen))
        return math.sqrt(max(R * R + r * r - 2.0 * R * r * math.cos(a), 1.0))

    def _richtung(self, seite: str) -> tuple[float, float]:
        """Einheitsvektor der Speiche in der Zeichenebene (y zeigt nach oben)."""
        _, abstand, _, _ = self._seite(seite)
        vorzeichen = -1.0 if seite == "links" else 1.0
        # Waagerechter Weg von der Flanschmitte bis zur Felgenmittelebene.
        quer = self._felge.versatz - vorzeichen * abstand
        laengs = self._projektion(seite)
        strecke = math.hypot(quer, laengs)
        return quer / strecke, -laengs / strecke

    # -------------------------------------------------------------- Zeichnung

    def zeichne(self, ctx, breite: float, hoehe: float, farben: zg.Farben) -> None:
        if self._felge.erd <= 0 or self._einspeichung.speichenzahl <= 0:
            return

        r_links, a_links, _, _ = self._seite("links")
        r_rechts, a_rechts, _, _ = self._seite("rechts")
        r_max = max(r_links, r_rechts, 1.0)

        halbspanne = max(a_links, a_rechts, abs(self._felge.versatz), 5.0) + 8.0
        nutzbreite = breite - 2 * RAND_SEITE
        nutzhoehe = hoehe - RAND_OBEN - RAND_UNTEN
        if nutzbreite < 70 or nutzhoehe < 110:
            return

        # Ein Maßstab für beide Richtungen – nur so stimmen die Winkel. Der
        # Flansch darf höchstens die halbe Höhe belegen, darüber laufen die
        # Speichen aus dem Bild.
        skala = min(nutzbreite / (2 * halbspanne), nutzhoehe * 0.5 / r_max)

        mitte_x = breite / 2.0
        y_achse = hoehe - RAND_UNTEN
        y_oben = RAND_OBEN + 10

        self._mittellinien(ctx, farben, mitte_x, y_oben, y_achse, skala)
        self._nabenkoerper(ctx, farben, mitte_x, y_achse, halbspanne, skala, a_links, a_rechts)

        for seite in ("links", "rechts"):
            self._seite_zeichnen(ctx, farben, seite, mitte_x, y_achse, y_oben, skala)

        self._bemassung(ctx, farben, mitte_x, y_achse, skala, a_links, a_rechts)

        # Kurz gehalten, damit der Text nicht in die Beschriftung der
        # Mittellinie hineinläuft.
        zg.text(ctx, RAND_SEITE - 30, RAND_OBEN - 20,
                f"↑ zur Felge, ERD {mm(self._felge.erd, 0)}",
                farben.schwach, 8.5, anker="links")

    def _nabenkoerper(self, ctx, farben, mitte_x, y_achse, halbspanne, skala,
                      a_links, a_rechts) -> None:
        """Achse und Nabenkörper zwischen den beiden Flanschen."""
        zg.setze(ctx, farben.linie, 2.0)
        zg.linie(ctx, mitte_x - halbspanne * skala, y_achse, mitte_x + halbspanne * skala, y_achse)

        hoehe = NABENKOERPER_MM * skala
        x1 = mitte_x - a_links * skala
        x2 = mitte_x + a_rechts * skala
        zg.setze(ctx, farben.linie, 1.4)
        ctx.rectangle(x1, y_achse - hoehe, x2 - x1, hoehe)
        ctx.stroke()

    def _seite_zeichnen(self, ctx, farben, seite, mitte_x, y_achse, y_oben, skala) -> None:
        r, abstand, _, _ = self._seite(seite)
        vorzeichen = -1.0 if seite == "links" else 1.0
        x_flansch = mitte_x + vorzeichen * abstand * skala
        y_flansch = y_achse - r * skala

        farbe = farben.akzent if seite == "links" else farben.linie

        # Flansch als senkrechter Steg mit Speichenloch an der Spitze.
        zg.setze(ctx, farbe, 2.4)
        zg.linie(ctx, x_flansch, y_achse, x_flansch, y_flansch)
        ctx.set_source_rgba(*farbe)
        ctx.arc(x_flansch, y_flansch, 2.6, 0, 2 * math.pi)
        ctx.fill()

        # Speiche mit echtem Winkel bis zum oberen Bildrand.
        richtung = self._richtung(seite)
        strecke = (y_flansch - y_oben) / -richtung[1] if richtung[1] < 0 else 0.0
        ende = (x_flansch + richtung[0] * strecke, y_flansch + richtung[1] * strecke)

        zg.setze(ctx, farbe, 1.8)
        zg.linie(ctx, x_flansch, y_flansch, *ende)
        ctx.set_source_rgba(*farbe)
        zg.spitze(ctx, ende[0], ende[1], math.atan2(richtung[1], richtung[0]), 7.0)

        self._winkel(ctx, farben, farbe, x_flansch, y_flansch, richtung, strecke, vorzeichen)

    def _winkel(self, ctx, farben, farbe, x, y, richtung, strecke, vorzeichen) -> None:
        """Bogen zwischen Radebene (senkrecht) und Speiche plus Zahlenwert."""
        winkel_speiche = math.atan2(richtung[1], richtung[0])
        senkrecht = -math.pi / 2
        radius = min(max(strecke * 0.45, 26.0), 80.0)

        zg.setze(ctx, farbe, 1.2)
        if winkel_speiche >= senkrecht:
            ctx.arc(x, y, radius, senkrecht, winkel_speiche)
        else:
            ctx.arc_negative(x, y, radius, senkrecht, winkel_speiche)
        ctx.stroke()
        zg.hilfslinie(ctx, farben, x, y, x, y - radius - 10)

        # Der Zahlenwert steht außen neben dem Flansch, sonst liegt er auf der
        # Speiche.
        wert = abs(math.degrees(winkel_speiche - senkrecht))
        zg.text(ctx, x + vorzeichen * (radius * 0.55 + 10), y - radius * 0.75,
                grad(wert), farbe, 9.5,
                anker="rechts" if vorzeichen < 0 else "links", fett=True)

    def _mittellinien(self, ctx, farben, mitte_x, y_oben, y_achse, skala) -> None:
        zg.gestrichelt(ctx, farben.schwach, 1.0, (6.0, 3.0, 2.0, 3.0))
        zg.linie(ctx, mitte_x, y_oben - 14, mitte_x, y_achse + 14)
        ctx.set_dash([])
        zg.text(ctx, mitte_x, y_oben - 18, "Radmitte", farben.schwach, 8.0, anker="oben",
                freistellen=farben.grund)

        versatz = self._felge.versatz
        if abs(versatz) >= 0.05:
            x = mitte_x + versatz * skala
            zg.gestrichelt(ctx, farben.akzent, 1.0, (3.0, 3.0))
            zg.linie(ctx, x, y_oben - 14, x, y_achse)
            ctx.set_dash([])
            zg.text(ctx, x, y_oben - 18, f"Felgenmitte {mm(versatz)}",
                    farben.akzent, 8.0, anker="oben", freistellen=farben.grund)

    def _bemassung(self, ctx, farben, mitte_x, y_achse, skala, a_links, a_rechts) -> None:
        y = y_achse + 28
        x_links = mitte_x - a_links * skala
        x_rechts = mitte_x + a_rechts * skala

        for x in (x_links, x_rechts):
            zg.hilfslinie(ctx, farben, x, y_achse, x, y + 4)
        zg.hilfslinie(ctx, farben, mitte_x, y_achse + 14, mitte_x, y + 4)

        zg.masslinie_waagerecht(ctx, farben, x_links, mitte_x, y, mm(a_links), oben=False)
        zg.masslinie_waagerecht(ctx, farben, mitte_x, x_rechts, y, mm(a_rechts), oben=False)
        zg.text(ctx, mitte_x, y + 32, "Flanschabstand ab Radmitte",
                farben.schwach, 8.0, anker="unten")
