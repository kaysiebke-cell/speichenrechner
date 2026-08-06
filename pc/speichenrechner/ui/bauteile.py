"""Erkennbare Bauteil-Zeichnungen: Nabe in der Seitenansicht, Felgenprofil.

Die Nabe wird als **Drehteil-Kontur** gezeichnet: eine einzige Linie über
Achsstummel, Endkappe, Lagersitz, Flansch, Taille und Freilaufkörper und
zurück. So wirken die Flansche angeformt statt angeklebt – anders als bei
aufeinandergesetzten Rechtecken.

**Die Maße folgen den Eingaben**: Flanschabstand und Flansch-Ø sitzen dort,
wo sie eingegeben wurden, die Speichenlöcher liegen auf dem Lochkreis. Die
übrigen Maße (Endkappe, Lagersitz, Taille, Freilauf) haben keine Eingabe und
stehen in :class:`Gestalt`.

Farbe kommt aus dem Theme, nicht aus festen Werten: der Nabenkörper trägt den
Akzent, Freilauf und Achse bleiben neutral. Ein senkrechter Verlauf macht aus
der Fläche ein rundes Bauteil.

Jede Funktion gibt die wichtigen Punkte zurück, damit die aufrufende Skizze
ihre Maßlinien daran anhängen kann.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import cairo

from . import zeichnung as zg


@dataclass(frozen=True)
class NabenPunkte:
    """Anschlusspunkte der gezeichneten Nabe, in Bildkoordinaten."""

    mitte_x: float
    mitte_y: float
    achse_links: float
    achse_rechts: float
    flansch_links: float
    flansch_rechts: float
    flansch_oben: float
    flansch_unten: float


@dataclass(frozen=True)
class Gestalt:
    """Radien der Nabe in mm, für die es keine Eingabe gibt.

    Sie geben dem Bauteil seine Gestalt. Veränderlich sind nur Flanschabstand
    und Flansch-Ø – die kommen aus dem Formular.
    """

    achse: float = 5.0          # Achsstummel
    kappe: float = 8.5          # Endkappe / Kontermutter
    sitz: float = 12.0          # Lagersitz, links mit Rändelung
    bund: float = 13.5          # Bund am Flanschfuß
    rohr: float = 11.0          # Nabenrohr an den Flanschen
    taille: float = 9.5         # engste Stelle in der Mitte
    freilauf: float = 17.0      # Freilaufkörper
    flanschdicke: float = 1.4   # halbe Dicke der Flanschscheibe
    flanschrand: float = 2.5    # wie weit der Flansch über den Lochkreis steht

    # Längen entlang der Achse, jeweils ab Flanschmitte gemessen
    stummel: float = 30.0       # bis zum Achsende links
    kappe_ab: float = 22.0
    sitz_ab: float = 15.0
    bund_ab: float = 7.0
    uebergang: float = 5.0      # bis der Bund ins Rohr übergeht
    freilauf_ab: float = 3.0
    freilauf_bis: float = 30.0
    kappe_rechts: float = 36.0
    stummel_rechts: float = 44.0


GESTALT = Gestalt()

#: Wie weich die Taille abgetastet wird. Mehr Schritte = runder, aber teurer.
TAILLE_SCHRITTE = 14


#: Länge des Gewindestummels für aufgeschraubte Ritzel, in mm.
GEWINDE_LAENGE = 16.0

#: Radius des Gewindestummels – schmaler als ein Freilaufkörper.
GEWINDE_RADIUS = 13.0


def _schale(
    gestalt: Gestalt, schale: str, radius_links: float, radius_rechts: float
) -> tuple[float, float, float]:
    """``(Bund, Rohr, Taille)`` in mm für diese Bauart.

    Bei ``gross`` – Dynamo und Nabenschaltung – füllt die Schale fast den
    Flansch aus; darin sitzt der Generator bzw. das Getriebe. Sonst gelten die
    festen Maße, aber **gedeckelt**: bei einem kleinen Lochkreis darf der
    Nabenkörper nicht dicker werden als der Flansch.
    """
    kleinster = max(min(radius_links, radius_rechts), 1.0)
    if schale == "gross":
        return kleinster * 0.86, kleinster * 0.82, kleinster * 0.76
    deckel = kleinster * 0.80
    return (min(gestalt.bund, deckel),
            min(gestalt.rohr, deckel * 0.88),
            min(gestalt.taille, deckel * 0.76))


def _stationen(
    abstand_links: float,
    abstand_rechts: float,
    radius_links: float,
    radius_rechts: float,
    antrieb: str = "kassette",
    schale: str = "normal",
    gestalt: Gestalt = GESTALT,
) -> list[tuple[float, float]]:
    """Die Nabe als ``(x, Radius)`` in mm, ab der Nabenmitte.

    Genau so zeichnet man ein gedrehtes Teil: eine Kontur mit Absätzen. Die
    Flanschscheiben sind Teil derselben Kontur.

    ``antrieb`` bestimmt, was rechts sitzt – ein Freilaufkörper mit
    Verzahnung (``kassette``), ein Gewindestummel (``gewinde``) oder nichts
    (``keiner``, also eine Vorderradnabe). ``schale`` macht den Nabenkörper
    bei Dynamo und Nabenschaltung dick.
    """
    g = gestalt
    a_l, a_r = abstand_links, abstand_rechts
    r_fl = radius_links + g.flanschrand
    r_fr = radius_rechts + g.flanschrand
    dicke = g.flanschdicke
    bund, rohr, taille = _schale(g, schale, radius_links, radius_rechts)
    sitz = min(g.sitz, bund * 0.92)
    kappe = min(g.kappe, sitz * 0.75)
    achse = min(g.achse, kappe * 0.62)

    stationen = [
        (-a_l - g.stummel, achse), (-a_l - g.kappe_ab, achse),
        (-a_l - g.kappe_ab, kappe), (-a_l - g.sitz_ab, kappe),
        (-a_l - g.sitz_ab, sitz), (-a_l - g.bund_ab, sitz),
        (-a_l - g.bund_ab, bund), (-a_l - dicke, bund),
        (-a_l - dicke, r_fl), (-a_l + dicke, r_fl),
        (-a_l + dicke, bund), (-a_l + g.uebergang, rohr),
    ]

    # Taille als Kosinus abgetastet – ein weicher Bogen statt einer Kante.
    von = -a_l + g.uebergang
    bis = a_r - g.uebergang
    if bis > von:
        for nummer in range(TAILLE_SCHRITTE + 1):
            anteil = nummer / TAILLE_SCHRITTE
            x = von + anteil * (bis - von)
            hub = (math.cos(anteil * 2 * math.pi - math.pi) + 1) / 2
            stationen.append((x, taille + (rohr - taille) * hub))

    stationen += [
        (a_r - g.uebergang, rohr), (a_r - dicke, bund),
        (a_r - dicke, r_fr), (a_r + dicke, r_fr),
        (a_r + dicke, bund), (a_r + g.freilauf_ab, bund),
    ]

    if antrieb == "kassette":
        stationen += [
            (a_r + g.freilauf_ab, g.freilauf), (a_r + g.freilauf_bis, g.freilauf),
            (a_r + g.freilauf_bis, kappe), (a_r + g.kappe_rechts, kappe),
            (a_r + g.kappe_rechts, achse), (a_r + g.stummel_rechts, achse),
        ]
    elif antrieb == "gewinde":
        ende = a_r + g.freilauf_ab + GEWINDE_LAENGE
        stationen += [
            (a_r + g.freilauf_ab, GEWINDE_RADIUS), (ende, GEWINDE_RADIUS),
            (ende, kappe), (ende + 7, kappe),
            (ende + 7, achse), (ende + 15, achse),
        ]
    else:
        # Vorderrad: rechts genauso abgesetzt wie links.
        stationen += [
            (a_r + g.bund_ab, sitz), (a_r + g.sitz_ab, sitz),
            (a_r + g.sitz_ab, kappe), (a_r + g.kappe_ab, kappe),
            (a_r + g.kappe_ab, achse), (a_r + g.stummel, achse),
        ]
    return stationen


def _kontur(ctx, stationen, mitte_x: float, mitte_y: float, skala: float) -> None:
    """Legt die geschlossene Kontur an: oben hin, unten zurück."""
    ctx.new_path()
    ctx.move_to(mitte_x + stationen[0][0] * skala, mitte_y - stationen[0][1] * skala)
    for x_mm, r_mm in stationen[1:]:
        ctx.line_to(mitte_x + x_mm * skala, mitte_y - r_mm * skala)
    for x_mm, r_mm in reversed(stationen):
        ctx.line_to(mitte_x + x_mm * skala, mitte_y + r_mm * skala)
    ctx.close_path()


def _fuellen(ctx, farben: zg.Farben, farbe, mitte_y: float, halbe_hoehe: float,
             staerke: float = 1.0) -> None:
    """Füllt den vorhandenen Pfad deckend und legt den Verlauf darüber.

    Deckend, weil sonst die dunkle Achse durch den Nabenkörper scheint.
    """
    ctx.set_source_rgba(*farben.flaeche)
    ctx.fill_preserve()
    ctx.set_source(farben.verlauf(farbe, mitte_y, halbe_hoehe, staerke))
    ctx.fill_preserve()


def _riffelung(ctx, farben: zg.Farben, x1: float, x2: float, mitte_y: float,
               halb: float, teilung: float) -> None:
    """Rändelung am Lagersitz – viele feine Striche."""
    zg.setze(ctx, farben.getoent(farben.metall, 0.45), 0.8)
    x = x1 + teilung / 2
    while x < x2:
        zg.linie(ctx, x, mitte_y - halb, x, mitte_y + halb)
        x += teilung


def bohrung(ctx, farben: zg.Farben, x: float, y: float, radius: float) -> None:
    """Speichenloch als echte Bohrung: dunkel mit hellem Rand."""
    ctx.arc(x, y, radius, 0, 2 * math.pi)
    ctx.set_source_rgba(farben.flaeche[0] * 0.35, farben.flaeche[1] * 0.35,
                        farben.flaeche[2] * 0.35, 1.0)
    ctx.fill_preserve()
    zg.setze(ctx, farben.getoent(farben.akzent, 0.95), 1.2)
    ctx.stroke()


def _antriebsseite(ctx, farben: zg.Farben, stationen, mitte_x: float, mitte_y: float,
                   skala: float, x_flansch_rechts: float, hoch: float,
                   antrieb: str) -> None:
    """Färbt und zeichnet, was rechts an der Nabe sitzt.

    ``kassette`` = Freilaufkörper mit Längsverzahnung und zwei Umfangsnuten,
    ``gewinde`` = Gewindestummel für aufgeschraubte Ritzel, ``keiner`` = eine
    Vorderradnabe, da ist nichts zu zeichnen.
    """
    if antrieb == "keiner":
        return

    g = GESTALT
    if antrieb == "kassette":
        x1 = x_flansch_rechts + g.freilauf_ab * skala
        x2 = x_flansch_rechts + g.freilauf_bis * skala
        halb = g.freilauf * skala
    else:
        x1 = x_flansch_rechts + g.freilauf_ab * skala
        x2 = x1 + GEWINDE_LAENGE * skala
        halb = GEWINDE_RADIUS * skala

    if x2 - x1 < 4:
        return

    # Neutral einfärben – im CAD-Bild ist die Antriebsseite der graue Teil.
    ctx.save()
    ctx.rectangle(x1, mitte_y - hoch, x2 - x1, 2 * hoch)
    ctx.clip()
    _kontur(ctx, stationen, mitte_x, mitte_y, skala)
    _fuellen(ctx, farben, farben.metall, mitte_y, hoch, staerke=0.75)
    zg.setze(ctx, farben.linie, 1.5)
    ctx.stroke()
    ctx.restore()

    if antrieb == "kassette":
        # Wenige kräftige Längsnuten, dazu zwei Umfangsnuten.
        zg.setze(ctx, farben.getoent(farben.metall, 0.5), 1.1)
        for nummer in range(1, 7):
            x_nut = x1 + (x2 - x1) * nummer / 7.0
            zg.linie(ctx, x_nut, mitte_y - halb * 0.96, x_nut, mitte_y + halb * 0.96)
        zg.setze(ctx, farben.getoent(farben.metall, 0.3), 1.0)
        for anteil in (0.30, 0.62):
            y_nut = mitte_y + halb * (1 - 2 * anteil)
            zg.linie(ctx, x1, y_nut, x2, y_nut)
        return

    # Gewinde: feine Schräglinien oben und unten, wie ein Außengewinde im Schnitt.
    zg.setze(ctx, farben.getoent(farben.metall, 0.55), 1.0)
    teilung = max(3.0, 1.4 * skala)
    schraege = teilung * 0.7
    x = x1 + teilung * 0.4
    while x < x2 - schraege:
        for richtung in (-1, 1):
            y_aussen = mitte_y + richtung * halb
            zg.linie(ctx, x, y_aussen, x + schraege, y_aussen - richtung * halb * 0.30)
        x += teilung


def nabe_seitenansicht(
    ctx,
    farben: zg.Farben,
    x: float,
    y: float,
    breite: float,
    hoehe: float,
    nabe=None,
) -> NabenPunkte:
    """Hinterradnabe von der Seite: Achse, Flansche, Körper, Freilauf.

    Ohne ``nabe`` werden übliche Proportionen gezeichnet. Mit einer
    :class:`~speichenrechner.modelle.Nabe` sitzen die Flansche an ihrer
    tatsächlichen Stelle und haben die tatsächlichen Durchmesser zueinander.
    """
    mitte_y = y + hoehe / 2.0
    mitte_x = x + breite / 2.0
    g = GESTALT

    if nabe is not None and (nabe.flanschabstand_links + nabe.flanschabstand_rechts) > 0:
        a_l, a_r = nabe.flanschabstand_links, nabe.flanschabstand_rechts
        r_l = nabe.flanschdurchmesser_links / 2.0
        r_r = nabe.flanschdurchmesser_rechts / 2.0
        antrieb, schale = nabe.antrieb, nabe.schale
    else:
        a_l, a_r, r_l, r_r = 35.0, 20.0, 22.5, 22.5
        antrieb, schale = "kassette", "normal"

    stationen = _stationen(a_l, a_r, r_l, r_r, antrieb, schale)

    # Maßstab: die ganze Kontur soll mit etwas Luft in die Fläche passen –
    # in der Breite wie in der Höhe, mit demselben Faktor.
    spanne_x = stationen[-1][0] - stationen[0][0]
    spanne_r = max(r_mm for _, r_mm in stationen)
    skala = min(breite / (spanne_x * 1.04), (hoehe / 2.0) / (spanne_r * 1.12))

    # Die Kontur ist nicht mittensymmetrisch; sie wird auf die Fläche zentriert.
    versatz = (stationen[0][0] + stationen[-1][0]) / 2.0 * skala
    mitte_x -= versatz

    x_flansch_links = mitte_x - a_l * skala
    x_flansch_rechts = mitte_x + a_r * skala
    x_achse_links = mitte_x + stationen[0][0] * skala
    x_achse_rechts = mitte_x + stationen[-1][0] * skala
    hoch = spanne_r * skala

    # Achse durchgehend dahinter – dunkel, damit sie als Bohrung wirkt.
    achse = min(g.achse, spanne_r * 0.2)
    ctx.rectangle(x_achse_links, mitte_y - achse * skala,
                  x_achse_rechts - x_achse_links, 2 * achse * skala)
    ctx.set_source_rgba(farben.flaeche[0] * 0.4, farben.flaeche[1] * 0.4,
                        farben.flaeche[2] * 0.4, 1.0)
    ctx.fill_preserve()
    zg.setze(ctx, farben.linie, 1.1)
    ctx.stroke()

    # Nabenkörper: eine Kontur, im Akzent des Themes.
    _kontur(ctx, stationen, mitte_x, mitte_y, skala)
    _fuellen(ctx, farben, farben.bauteil, mitte_y, hoch)
    zg.setze(ctx, farben.linie, 1.5)
    ctx.stroke()

    _antriebsseite(ctx, farben, stationen, mitte_x, mitte_y, skala,
                   x_flansch_rechts, hoch, antrieb)

    # Rändelung am linken Lagersitz
    bund, _, _ = _schale(g, schale, r_l, r_r)
    _riffelung(ctx, farben,
               x_flansch_links - g.sitz_ab * skala, x_flansch_links - g.bund_ab * skala,
               mitte_y, min(g.sitz, bund * 0.92) * skala * 0.94, max(2.0, 0.9 * skala))

    # Speichenlöcher auf dem Lochkreis – der Bezug für den Flansch-Ø.
    loch = max(1.9, 0.95 * skala)
    for x_flansch, radius in ((x_flansch_links, r_l), (x_flansch_rechts, r_r)):
        for richtung in (-1, 1):
            bohrung(ctx, farben, x_flansch, mitte_y + richtung * radius * skala, loch)

    return NabenPunkte(
        mitte_x=mitte_x,
        mitte_y=mitte_y,
        achse_links=x_achse_links,
        achse_rechts=x_achse_rechts,
        flansch_links=x_flansch_links,
        flansch_rechts=x_flansch_rechts,
        flansch_oben=mitte_y - r_l * skala,
        flansch_unten=mitte_y + r_l * skala,
    )


@dataclass(frozen=True)
class Profil:
    """Ein Felgenquerschnitt in Millimetern, gemessen ab dem Nippelsitz.

    Der erste Wert eines Punktes ist die Tiefe (radial nach außen, zum
    Reifen hin), der zweite die Lage quer zur Felge. Die Punkte laufen von
    der einen Felgenwand über das Speichenbett zur anderen.

    ``kammer`` ist die zweite, innere Wand einer Hohlkammerfelge – ohne sie
    ist das Profil einwandig. ``offen`` zeichnet nur die Kontur statt einer
    gefüllten Fläche: so sieht ein einzelnes gekantetes Blech aus.
    """

    aussen: tuple[tuple[float, float], ...]
    kammer: tuple[tuple[float, float], ...] | None = None
    offen: bool = False

    @property
    def tiefe(self) -> float:
        return max(tiefe for tiefe, _ in self.aussen)

    @property
    def halbe_breite(self) -> float:
        return max(abs(quer) for _, quer in self.aussen)


#: Die Profile, die :mod:`speichenrechner.felgenkunde` unterscheidet.
#:
#: Die Formen sind stilisiert, aber in ihren Verhältnissen richtig: eine
#: Aero-Felge ist wirklich dreimal so tief wie eine Flachbettfelge, und ein
#: hakenloses Profil endet oben ohne den einwärts gebogenen Wulsthaken.
PROFILE = {
    # Hohlkammer: zwei Wände, Bremsflanken, Hörner – der Normalfall.
    "hohlkammer": Profil(
        aussen=(
            (0, -7), (3, -10), (14, -11.5), (14, -13.5),
            (22, -13.5), (22, -9.5), (19, -8),
            (19, 8), (22, 9.5), (22, 13.5),
            (14, 13.5), (14, 11.5), (3, 10), (0, 7),
        ),
        kammer=((3.5, -8.5), (12, -9.5), (12, 9.5), (3.5, 8.5)),
    ),
    # Hakenfelge: dasselbe Profil, der Wulsthaken ist hier der Regelfall.
    "haken": Profil(
        aussen=(
            (0, -7), (3, -10), (14, -11.5), (14, -13.5),
            (22, -13.5), (22, -9.0), (18.5, -7.5),
            (18.5, 7.5), (22, 9.0), (22, 13.5),
            (14, 13.5), (14, 11.5), (3, 10), (0, 7),
        ),
        kammer=((3.5, -8.5), (12, -9.5), (12, 9.5), (3.5, 8.5)),
    ),
    # Tubeless-Ready: von außen eine Hohlkammerfelge. Der Unterschied sitzt
    # innen – Mittelkanal und Haltewulst für den Reifenfuß.
    "tubeless": Profil(
        aussen=(
            (0, -7), (3, -10), (14, -11.5), (14, -13.5),
            (22, -13.5), (22, -9.5), (19, -8), (20, -5.5), (17.5, -2.5),
            (17.5, 2.5), (20, 5.5), (19, 8), (22, 9.5), (22, 13.5),
            (14, 13.5), (14, 11.5), (3, 10), (0, 7),
        ),
        kammer=((3.5, -8.5), (12, -9.5), (12, 9.5), (3.5, 8.5)),
    ),
    # Hakenlos: die Wand läuft gerade aus, kein einwärts gebogener Haken.
    "hakenlos": Profil(
        aussen=(
            (0, -7), (3, -10), (14, -11.5), (19, -12), (22, -11.5),
            (22, -8), (19, -8),
            (19, 8), (22, 8), (22, 11.5),
            (19, 12), (14, 11.5), (3, 10), (0, 7),
        ),
        kammer=((3.5, -8.5), (12, -9.5), (12, 9.5), (3.5, 8.5)),
    ),
    # V-Profil: schräge Seitenwände vom schmalen Bett zur breiten Bremsflanke.
    "v-profil": Profil(
        aussen=(
            (0, -6.5), (18, -12), (18, -13.5),
            (24, -13.5), (24, -9.5), (21, -8),
            (21, 8), (24, 9.5), (24, 13.5),
            (18, 13.5), (18, 12), (0, 6.5),
        ),
        kammer=((3, -7.5), (16.5, -10.5), (16.5, 10.5), (3, 7.5)),
    ),
    # Aero: hohes Profil, sonst wie die Hohlkammer aufgebaut.
    "aero": Profil(
        aussen=(
            (0, -5), (30, -11.5), (30, -13.5),
            (38, -13.5), (38, -9.5), (35, -8),
            (35, 8), (38, 9.5), (38, 13.5),
            (30, 13.5), (30, 11.5), (0, 5),
        ),
        kammer=((3, -6), (28, -10.5), (28, 10.5), (3, 6)),
    ),
    # Flachbett: ein einziges gekantetes Blech, flacher Boden.
    "flachbett": Profil(
        aussen=(
            (14, -13), (12, -12), (2, -10), (0, -6),
            (0, 6), (2, 10), (12, 12), (14, 13),
        ),
        offen=True,
    ),
    # Schlauchreifenfelge: flaches Bett, oben ausgehöhlt für den Reifen.
    "schlauch": Profil(
        aussen=(
            (0, -9), (2, -11), (10, -12), (13, -11.5),
            (10, -7), (9, 0), (10, 7),
            (13, 11.5), (10, 12), (2, 11), (0, 9),
        ),
    ),
}

#: Fällt der Felgentyp weg, wird die Hohlkammer gezeichnet.
PROFIL_STANDARD = "hohlkammer"


def profil_masse(profil: str = "") -> tuple[float, float]:
    """``(Tiefe, halbe Breite)`` eines Profils in mm – für den Maßstab."""
    gewaehlt = PROFILE.get(profil) or PROFILE[PROFIL_STANDARD]
    return gewaehlt.tiefe, gewaehlt.halbe_breite


def felgenprofil(
    ctx, farben: zg.Farben, x_nippelsitz: float, mitte_y: float,
    nach_aussen: int, skala: float, profil: str = "", oesen: int = 0,
) -> None:
    """Ein Felgenprofil im Schnitt.

    ``x_nippelsitz`` ist der Punkt, auf den sich der ERD bezieht;
    ``nach_aussen`` ist ``-1`` für die linke und ``+1`` für die rechte
    Felgenhälfte. ``profil`` wählt die Bauform (siehe :data:`PROFILE`),
    ``oesen`` ist 0 (ohne), 1 (einfach genietet) oder 2 (doppelt genietet).
    """
    gewaehlt = PROFILE.get(profil) or PROFILE[PROFIL_STANDARD]

    def punkt(tiefe: float, quer: float) -> tuple[float, float]:
        """``tiefe`` = radial nach außen, ``quer`` = in Richtung Achse."""
        return (x_nippelsitz + nach_aussen * tiefe * skala, mitte_y + quer * skala)

    # Eine Felge ist Blech, keine gefüllte Fläche. Deshalb wird die Kontur als
    # Strich in Wandstärke gezeichnet: einmal dunkel als Kante, darüber schmaler
    # und hell als Blech. Das ergibt ein dünnwandiges Profil, ohne dass für
    # jede Bauform eine zweite Punktliste nötig wäre.
    def blech(punkte, geschlossen: bool, wand: float) -> None:
        for farbe, breite in ((farben.linie, wand),
                              (farben.getoent(farben.bauteil, 0.75), max(wand - 1.7, 0.7))):
            zg.setze(ctx, farbe, breite)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.move_to(*punkte[0])
            for stelle in punkte[1:]:
                ctx.line_to(*stelle)
            if geschlossen:
                ctx.close_path()
            ctx.stroke()

    wandstaerke = max(1.7 * skala, 2.6)
    blech(tuple(punkt(*wert) for wert in gewaehlt.aussen), not gewaehlt.offen, wandstaerke)

    if gewaehlt.kammer:
        blech(tuple(punkt(*wert) for wert in gewaehlt.kammer), True, wandstaerke * 0.72)

    if oesen:
        _oese(ctx, farben, punkt, gewaehlt, oesen)

    # Nippelsitz als Bohrung – der Bezugspunkt des ERD
    bohrung(ctx, farben, x_nippelsitz, mitte_y, max(2.4, 0.9 * skala))


def _oese(ctx, farben: zg.Farben, punkt, profil: Profil, stufe: int) -> None:
    """Die Öse im Speichenbett – bei doppelter Nietung auch an der zweiten Wand.

    Sie sitzt dort, wo der Nippel aufliegt, und stützt sich bei „doppelt
    genietet“ zusätzlich auf der inneren Kammerwand ab.
    """
    zg.setze(ctx, farben.linie, 1.4)
    for tiefe in (-0.4, 1.2):
        zg.linie(ctx, *punkt(tiefe, -3.2), *punkt(tiefe, 3.2))
    for quer in (-3.2, 3.2):
        zg.linie(ctx, *punkt(-0.4, quer), *punkt(1.2, quer))

    if stufe < 2 or not profil.kammer:
        return

    # Zweite Auflage: die Öse reicht bis an die innere Wand.
    tiefe_kammer = profil.kammer[0][0]
    for quer in (-2.6, 2.6):
        zg.linie(ctx, *punkt(1.2, quer), *punkt(tiefe_kammer, quer))
    zg.linie(ctx, *punkt(tiefe_kammer, -4.0), *punkt(tiefe_kammer, 4.0))
