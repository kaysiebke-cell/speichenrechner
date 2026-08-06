"""Reiter „Messen“: die bemaßten Skizzen im Hauptfenster.

Kein eigener Dialog, sondern Teil der Ergebnisspalte – und an die Eingaben
gekoppelt: die Maßlinien tragen die tatsächlich eingegebenen Werte, und die
Nabe zeigt ihre wirklichen Verhältnisse. Wer in ein Eingabefeld klickt,
bekommt automatisch die passende Skizze.
"""

from __future__ import annotations

import math

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .. import felgenkunde
from ..formatierung import mm
from ..modelle import Felge, Nabe
from . import bauteile, widgets
from . import zeichnung as zg


class _Messbild(zg.ZeichenFlaeche):
    """Gemeinsame Basis: kennt Nabe und Felge, zeichnet mit echten Werten."""

    def __init__(self) -> None:
        super().__init__(240, 190)
        self._nabe = Nabe()
        self._felge = Felge()

    def setze_daten(self, nabe: Nabe, felge: Felge) -> None:
        self._nabe, self._felge = nabe, felge
        self.queue_draw()


class UebersichtBild(_Messbild):
    """Alle drei Maße in einem Bild – die klassische Speichenrechner-Skizze.

    Senkrecht ist **nicht** maßstäblich: sonst verschwände die Nabe neben dem
    Felgendurchmesser. Der Lochkreis sitzt auf einem festen Anteil der Höhe,
    die Nippel am Rand. Waagerecht folgen die Flansche ihren echten Abständen.
    """

    RAND_OBEN = 34
    RAND_UNTEN = 26
    LOCHKREIS_ANTEIL = 0.30      # wo der Flansch-Lochkreis sitzt

    def zeichne(self, ctx, breite, hoehe, farben: zg.Farben) -> None:
        # Feste, schmale Ränder: die senkrechten Maßlinien stehen darin, ihre
        # Beschriftung sitzt darüber – so läuft nichts aus dem Bild.
        rand_links = 52.0
        rand_rechts = 52.0
        if breite < rand_links + rand_rechts + 110 or hoehe < 180:
            return

        mitte_x = (rand_links + breite - rand_rechts) / 2.0
        mitte_y = (self.RAND_OBEN + hoehe - self.RAND_UNTEN) / 2.0
        halbe_hoehe = mitte_y - self.RAND_OBEN

        y_nippel_oben = mitte_y - halbe_hoehe
        y_nippel_unten = mitte_y + halbe_hoehe
        y_loch_oben = mitte_y - halbe_hoehe * self.LOCHKREIS_ANTEIL
        y_loch_unten = mitte_y + halbe_hoehe * self.LOCHKREIS_ANTEIL

        # Waagerecht folgen die Flansche ihren tatsächlichen Abständen.
        spanne = self._nabe.flanschabstand_links + self._nabe.flanschabstand_rechts
        platz = (breite - rand_links - rand_rechts) * 0.34
        skala_x = platz / spanne if spanne > 0 else 1.0
        x_flansch_links = mitte_x - self._nabe.flanschabstand_links * skala_x
        x_flansch_rechts = mitte_x + self._nabe.flanschabstand_rechts * skala_x

        self._mittellinie(ctx, farben, mitte_x, y_nippel_oben, y_nippel_unten)
        self._nabe_zeichnen(ctx, farben, mitte_y, x_flansch_links, x_flansch_rechts,
                            y_loch_oben, y_loch_unten)
        for x_flansch in (x_flansch_links, x_flansch_rechts):
            for y_loch, y_nippel in ((y_loch_oben, y_nippel_oben),
                                     (y_loch_unten, y_nippel_unten)):
                self._speiche(ctx, farben, x_flansch, y_loch, mitte_x, y_nippel)

        self._bemassung(ctx, farben, breite, mitte_x, mitte_y, rand_links, rand_rechts,
                        x_flansch_links, y_loch_oben, y_loch_unten,
                        y_nippel_oben, y_nippel_unten)

        zg.text(ctx, mitte_x, hoehe - 6,
                "senkrecht verkürzt – sonst wäre die Nabe ein Punkt",
                farben.schwach, 7.5, anker="oben")

    def _mittellinie(self, ctx, farben, mitte_x, y_oben, y_unten) -> None:
        zg.gestrichelt(ctx, farben.schwach, 1.0, (6.0, 3.0, 2.0, 3.0))
        zg.linie(ctx, mitte_x, y_oben - 16, mitte_x, y_unten + 16)
        ctx.set_dash([])

    def _nabe_zeichnen(self, ctx, farben, mitte_y, x_links, x_rechts,
                       y_loch_oben, y_loch_unten) -> None:
        """Achse, Nabenkörper und die beiden Flansche mit ihren Löchern.

        Hier steht die Nabe **nicht** maßstäblich – senkrecht ist verkürzt,
        sonst wäre sie neben dem Felgendurchmesser ein Punkt. Deshalb bleibt es
        bei einfachen Formen; Farben und Bohrungen sind aber dieselben wie in
        den maßstäblichen Ansichten.
        """
        rand = (y_loch_unten - y_loch_oben) * 0.10
        koerper = (y_loch_unten - y_loch_oben) * 0.30

        # Achse
        ctx.rectangle(x_links - 26, mitte_y - 5, x_rechts - x_links + 52, 10)
        ctx.set_source_rgba(farben.flaeche[0] * 0.4, farben.flaeche[1] * 0.4,
                            farben.flaeche[2] * 0.4, 1.0)
        ctx.fill_preserve()
        zg.setze(ctx, farben.linie, 1.2)
        ctx.stroke()

        # Nabenkörper im Akzent des Themes
        ctx.rectangle(x_links, mitte_y - koerper, x_rechts - x_links, 2 * koerper)
        ctx.set_source_rgba(*farben.flaeche)
        ctx.fill_preserve()
        ctx.set_source(farben.verlauf(farben.bauteil, mitte_y, koerper))
        ctx.fill_preserve()
        zg.setze(ctx, farben.linie, 1.4)
        ctx.stroke()

        for x_flansch in (x_links, x_rechts):
            hoch = (y_loch_unten - y_loch_oben) / 2 + rand
            ctx.rectangle(x_flansch - 5, y_loch_oben - rand, 10, 2 * hoch)
            ctx.set_source_rgba(*farben.flaeche)
            ctx.fill_preserve()
            ctx.set_source(farben.verlauf(farben.bauteil, mitte_y, hoch, 1.25))
            ctx.fill_preserve()
            zg.setze(ctx, farben.linie, 1.4)
            ctx.stroke()
            for y_loch in (y_loch_oben, y_loch_unten):
                bauteile.bohrung(ctx, farben, x_flansch, y_loch, 3.0)

    def _speiche(self, ctx, farben, x_flansch, y_loch, x_nippel, y_nippel) -> None:
        """Speiche vom Flanschloch zum Nippel, mit angedeutetem Nippel."""
        zg.setze(ctx, farben.linie, 1.6)
        zg.linie(ctx, x_flansch, y_loch, x_nippel, y_nippel)

        richtung = 1 if y_nippel > y_loch else -1
        ctx.rectangle(x_nippel - 4, y_nippel - richtung * 12, 8, richtung * 12)
        ctx.set_source_rgba(*farben.flaeche)
        ctx.fill_preserve()
        ctx.set_source(farben.verlauf(farben.bauteil, y_nippel - richtung * 6, 8))
        ctx.fill_preserve()
        zg.setze(ctx, farben.linie, 1.2)
        ctx.stroke()
        bauteile.bohrung(ctx, farben, x_nippel, y_nippel, 3.0)

    def _bemassung(self, ctx, farben, breite, mitte_x, mitte_y, rand_links, rand_rechts,
                   x_flansch_links, y_loch_oben, y_loch_unten,
                   y_nippel_oben, y_nippel_unten) -> None:
        # a – Flanschabstand ab Nabenmitte, waagerecht über der Nabe
        y_a = mitte_y - (y_loch_unten - y_loch_oben) * 0.62 - 14
        zg.masslinie_waagerecht(ctx, farben, x_flansch_links, mitte_x, y_a,
                                f"a = {mm(self._nabe.flanschabstand_links)}")

        # d – Lochkreis des linken Flansches
        x_d = rand_links * 0.52
        for y in (y_loch_oben, y_loch_unten):
            zg.hilfslinie(ctx, farben, x_d, y, x_flansch_links, y)
        zg.masslinie_senkrecht(ctx, farben, y_loch_oben, y_loch_unten, x_d, "")
        zg.text(ctx, x_d + 6, y_loch_oben - 12,
                f"d = {mm(self._nabe.flanschdurchmesser_links)}",
                farben.text, 8.5, anker="links")

        # D – ERD
        x_gross = breite - rand_rechts * 0.52
        for y in (y_nippel_oben, y_nippel_unten):
            zg.hilfslinie(ctx, farben, mitte_x, y, x_gross, y)
        zg.masslinie_senkrecht(ctx, farben, y_nippel_oben, y_nippel_unten, x_gross, "")
        zg.text(ctx, x_gross - 6, y_nippel_oben - 12,
                f"D = {mm(self._felge.erd)}", farben.text, 8.5, anker="rechts")


class FlanschDurchmesserBild(_Messbild):
    """Nabe von der Seite mit dem Maß über die Speichenlöcher."""

    def zeichne(self, ctx, breite, hoehe, farben: zg.Farben) -> None:
        rand_x = min(max(breite * 0.16, 60.0), 110.0)
        if breite < 2 * rand_x + 90 or hoehe < 120:
            return

        punkte = bauteile.nabe_seitenansicht(
            ctx, farben, rand_x, hoehe * 0.08, breite - 2 * rand_x, hoehe * 0.66, self._nabe
        )

        for y in (punkte.flansch_oben, punkte.flansch_unten):
            zg.hilfslinie(ctx, farben, rand_x - 40, y, breite - rand_x + 16, y)

        # Der Wert steht **über** der Maßlinie, nicht daneben: neben einer
        # Maßlinie so weit links lief der Text aus dem Bild heraus.
        zg.masslinie_senkrecht(
            ctx, farben, punkte.flansch_oben, punkte.flansch_unten, rand_x - 28, "",
        )
        zg.text(ctx, rand_x - 28, punkte.flansch_oben - 14,
                f"Flansch-Ø links\n{mm(self._nabe.flanschdurchmesser_links)}",
                farben.schwach, 8.0, anker="oben")

        zg.text(ctx, breite - rand_x + 16, punkte.mitte_y,
                f"rechts\n{mm(self._nabe.flanschdurchmesser_rechts)}",
                farben.schwach, 8.0, anker="links")

        zg.text(ctx, breite / 2.0, hoehe - 8,
                "Von Lochmitte zu Lochmitte – nicht über die Flanschkante.",
                farben.schwach, 8.0, anker="oben")


class FlanschAbstandBild(_Messbild):
    """Dieselbe Nabe mit den Abständen ab Nabenmitte."""

    def zeichne(self, ctx, breite, hoehe, farben: zg.Farben) -> None:
        rand_x = min(max(breite * 0.10, 40.0), 80.0)
        if breite < 2 * rand_x + 90 or hoehe < 130:
            return

        # Etwas mehr Höhe als die Breite verlangt: eine dicke Getriebenabe ist
        # fast quadratisch und wird sonst klein gezeichnet.
        punkte = bauteile.nabe_seitenansicht(
            ctx, farben, rand_x, hoehe * 0.20, breite - 2 * rand_x, hoehe * 0.60, self._nabe
        )

        y_mass = hoehe * 0.15
        for x in (punkte.flansch_links, punkte.mitte_x, punkte.flansch_rechts):
            zg.hilfslinie(ctx, farben, x, y_mass - 6, x, punkte.mitte_y)

        zg.masslinie_waagerecht(ctx, farben, punkte.flansch_links, punkte.mitte_x,
                                y_mass, mm(self._nabe.flanschabstand_links))
        zg.masslinie_waagerecht(ctx, farben, punkte.mitte_x, punkte.flansch_rechts,
                                y_mass, mm(self._nabe.flanschabstand_rechts))
        zg.text(ctx, punkte.mitte_x, y_mass - 26, "ab Nabenmitte",
                farben.schwach, 8.0, anker="oben")

        einbaubreite = self._nabe.flanschabstand_links + self._nabe.flanschabstand_rechts
        y_breite = hoehe - 46
        for x in (punkte.achse_links, punkte.achse_rechts):
            zg.hilfslinie(ctx, farben, x, punkte.mitte_y, x, y_breite + 6)
        zg.masslinie_waagerecht(
            ctx, farben, punkte.achse_links, punkte.achse_rechts, y_breite,
            f"Flanschabstand gesamt {mm(einbaubreite)}", oben=False,
        )

        zg.text(ctx, breite / 2.0, hoehe - 8,
                "Beide Maße ab der Nabenmitte – nicht ab der Endkappe.",
                farben.schwach, 8.0, anker="oben")


class ErdBild(_Messbild):
    """Zwei Felgenprofile im Schnitt mit dem ERD dazwischen.

    Welches Profil gezeichnet wird, sagt der gewählte Felgentyp: eine
    Aero-Felge ist hier hoch, eine Flachbettfelge flach und einwandig, und
    eine geöste Felge zeigt ihre Öse am Nippelsitz.
    """

    def zeichne(self, ctx, breite, hoehe, farben: zg.Farben) -> None:
        if breite < 220 or hoehe < 130:
            return

        typ = felgenkunde.finde(self._felge.typ)
        profil = typ.profil if typ else ""
        oesen = typ.oesen_stufe if typ else 0
        tiefe, halbe_breite = bauteile.profil_masse(profil)

        mitte_y = hoehe * 0.44
        abstand = breite * 0.19
        # Maßstab am Hohlkammerprofil als Bezug: alle Profile bleiben
        # untereinander vergleichbar, nur ein größeres wird kleiner gezeichnet,
        # damit es ins Bild passt. Sonst füllte eine flache Schlauchreifenfelge
        # dasselbe Bild wie eine hohe Aero-Felge.
        bezug_tiefe, bezug_breite = bauteile.profil_masse()
        skala = min(breite * 0.23 / max(tiefe, bezug_tiefe),
                    hoehe * 0.30 / max(halbe_breite, bezug_breite))

        x_links = breite / 2.0 - abstand
        x_rechts = breite / 2.0 + abstand

        bauteile.felgenprofil(ctx, farben, x_links, mitte_y, -1, skala, profil, oesen)
        bauteile.felgenprofil(ctx, farben, x_rechts, mitte_y, +1, skala, profil, oesen)

        y_mass = mitte_y + (halbe_breite + 1.0) * skala + 22
        for x in (x_links, x_rechts):
            zg.hilfslinie(ctx, farben, x, mitte_y, x, y_mass + 6)
        zg.masslinie_waagerecht(ctx, farben, x_links, x_rechts, y_mass,
                                f"ERD {mm(self._felge.erd)}", oben=False)

        y_zeiger = mitte_y - (halbe_breite - 2.0) * skala - 10
        zg.hilfslinie(ctx, farben, x_links, mitte_y, x_links + 22, y_zeiger)
        zg.text(ctx, x_links + 26, y_zeiger, "Nippelsitz", farben.schwach, 8.0, anker="links")

        if abs(self._felge.versatz) >= 0.05:
            zg.text(ctx, breite / 2.0, mitte_y,
                    f"Versatz {mm(self._felge.versatz)}", farben.akzent, 8.5)

        if typ is not None:
            zg.text(ctx, breite / 2.0, 14, typ.name, farben.schwach, 8.5, anker="unten")

        zg.text(ctx, breite / 2.0, hoehe - 8,
                "Von Nippelsitz zu Nippelsitz – nicht bis zum Reifensitz.",
                farben.schwach, 8.0, anker="oben")


class MessAnsicht(Gtk.Box):
    """Umschaltbare Messskizzen für die Ergebnisspalte."""

    #: Schlüssel der Eingabefelder, die auf eine Skizze zeigen.
    ZUORDNUNG = {
        "uebersicht": "Übersicht: a, d und D",
        "flansch": "d – Flansch-Ø",
        "abstand": "a – Flanschabstand",
        "erd": "D – ERD",
    }

    def __init__(self) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(widgets.RAND)

        self.stapel = Gtk.Stack()
        self.stapel.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        self.bilder = {
            "uebersicht": UebersichtBild(),
            "flansch": FlanschDurchmesserBild(),
            "abstand": FlanschAbstandBild(),
            "erd": ErdBild(),
        }
        for schluessel, bild in self.bilder.items():
            self.stapel.add_titled(bild, schluessel, self.ZUORDNUNG[schluessel])

        # Eine Klappliste statt Umschalter-Knöpfen: GTK macht die Knöpfe eines
        # StackSwitchers gleich breit, das trieb die Mindestbreite der ganzen
        # Ergebnisspalte über 400 Pixel.
        self.auswahl = Gtk.ComboBoxText()
        for schluessel, beschriftung in self.ZUORDNUNG.items():
            self.auswahl.append(schluessel, beschriftung)
        self.auswahl.set_active_id("uebersicht")
        self.auswahl.connect("changed", self._auswahl_geaendert)
        self.pack_start(self.auswahl, False, False, 0)
        self.pack_start(self.stapel, True, True, 0)

    def _auswahl_geaendert(self, combo: Gtk.ComboBoxText) -> None:
        schluessel = combo.get_active_id()
        if schluessel:
            self.stapel.set_visible_child_name(schluessel)

    def setze_daten(self, nabe: Nabe, felge: Felge) -> None:
        for bild in self.bilder.values():
            bild.setze_daten(nabe, felge)

    def zeige(self, schluessel: str) -> None:
        """Schaltet auf die Skizze zum angeklickten Eingabefeld."""
        if schluessel in self.bilder:
            self.auswahl.set_active_id(schluessel)

    def aktuelles_bild(self) -> zg.ZeichenFlaeche | None:
        kind = self.stapel.get_visible_child()
        return kind if isinstance(kind, zg.ZeichenFlaeche) else None
