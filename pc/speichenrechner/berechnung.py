"""Mathematik des Speichenrechners – bewusst ohne GUI-Abhängigkeit.

Modell
------
Nabenmitte im Ursprung, Radebene = xy-Ebene, Achse entlang z.

* Flanschloch:  ``(r, 0, w)``          mit r = Flanschradius, w = Flanschabstand
* Felgenloch:   ``(R·cos a, R·sin a, 0)`` mit R = ERD/2

Daraus folgt die klassische Speichenformel::

    L = sqrt(R² + r² + w² - 2·R·r·cos a) - d/2

``a`` ist der Sehnenwinkel an der Nabe. Sitzen auf einer Flanschseite ``m``
Speichen, liegen benachbarte Löcher dieser Seite ``360°/m`` auseinander; bei
``k`` Kreuzungen überspannt die Speiche ``a = k · 360°/m``. Im Normalfall
(gleiche Verteilung) ist ``m = n/2`` und damit ``a = k · 720°/n``.

``d`` ist der Durchmesser des Speichenlochs im Flansch; die halbe
Lochbreite wird abgezogen, weil die Speiche am Lochrand anliegt.
"""

from __future__ import annotations

import math

from .formatierung import grad, zahl
from . import felgenkunde, speiche
from .modelle import (
    Einspeichung, Ergebnis, Felge, Nabe, SeitenErgebnis, Speichensatz,
)

#: Erlaubte Rundungsschritte für die Speichenlänge (mm).
RUNDUNGSSCHRITTE = (1.0, 0.5, 2.0)

#: Bis zu wie vielen Kreuzungen der Vergleich rechnet.
VERGLEICH_MAXIMUM = 4


def sehnenwinkel_seite(speichen_seite: int, kreuzungen: int) -> float:
    """Sehnenwinkel in Grad aus der Speichenzahl **einer** Flanschseite."""
    if speichen_seite <= 0:
        raise ValueError("Auf jeder Seite muss mindestens eine Speiche sitzen.")
    return kreuzungen * 360.0 / speichen_seite


def sehnenwinkel(speichenzahl: int, kreuzungen: int) -> float:
    """Sehnenwinkel in Grad bei gleicher Verteilung auf beide Seiten."""
    if speichenzahl <= 0:
        raise ValueError("Die Speichenzahl muss größer als 0 sein.")
    return sehnenwinkel_seite(speichenzahl // 2, kreuzungen)


def speichenlaenge(
    erd: float,
    flanschdurchmesser: float,
    flanschabstand: float,
    speichenzahl: int,
    kreuzungen: int,
    speichenloch: float = 2.6,
    speichen_seite: int | None = None,
) -> float:
    """Exakte Speichenlänge in mm (ungerundet).

    ``speichen_seite`` überschreibt die Speichenzahl dieser Flanschseite –
    nötig bei ungleicher Verteilung (2:1).
    """
    if erd <= 0:
        raise ValueError("Der ERD muss größer als 0 sein.")
    if flanschdurchmesser <= 0:
        raise ValueError("Der Flanschdurchmesser muss größer als 0 sein.")
    if kreuzungen < 0:
        raise ValueError("Die Kreuzungszahl darf nicht negativ sein.")

    R = erd / 2.0
    r = flanschdurchmesser / 2.0
    w = abs(flanschabstand)
    if speichen_seite is None:
        a = math.radians(sehnenwinkel(speichenzahl, kreuzungen))
    else:
        a = math.radians(sehnenwinkel_seite(speichen_seite, kreuzungen))

    quadrat = R * R + r * r + w * w - 2.0 * R * r * math.cos(a)
    return math.sqrt(max(quadrat, 0.0)) - speichenloch / 2.0


def speichenwinkel(
    erd: float,
    flanschdurchmesser: float,
    flanschabstand: float,
    speichenzahl: int,
    kreuzungen: int,
    speichen_seite: int | None = None,
) -> float:
    """Speichenwinkel (bracing angle) gegen die Radebene, in Grad.

    Je größer dieser Winkel, desto seitensteifer wird das Laufrad.
    """
    R = erd / 2.0
    r = flanschdurchmesser / 2.0
    w = abs(flanschabstand)
    if speichen_seite is None:
        a = math.radians(sehnenwinkel(speichenzahl, kreuzungen))
    else:
        a = math.radians(sehnenwinkel_seite(speichen_seite, kreuzungen))

    geometrisch = math.sqrt(max(R * R + r * r + w * w - 2.0 * R * r * math.cos(a), 0.0))
    if geometrisch <= 0.0:
        return 0.0
    return math.degrees(math.asin(min(w / geometrisch, 1.0)))


def felgenwinkel(
    erd: float, flanschdurchmesser: float, kreuzungen: int, speichen_seite: int
) -> float:
    """Winkel an der Felge zwischen Speiche und Felgenradius, in Grad.

    Bestimmt, wie schräg die Speiche im Felgenloch steht. Bei großen Werten
    muss das Speichenloch entsprechend gebohrt sein, sonst knickt der Nippel.
    """
    R = erd / 2.0
    r = flanschdurchmesser / 2.0
    a = math.radians(sehnenwinkel_seite(speichen_seite, kreuzungen))
    projektion = math.sqrt(max(R * R + r * r - 2.0 * R * r * math.cos(a), 0.0))
    if projektion <= 0:
        return 0.0
    return math.degrees(math.asin(min(r * math.sin(a) / projektion, 1.0)))


def lochabstand(flanschdurchmesser: float, speichen_seite: int) -> float:
    """Bogenabstand benachbarter Speichenlöcher eines Flansches, in mm."""
    if speichen_seite <= 0:
        return 0.0
    return math.pi * flanschdurchmesser / speichen_seite


def _kopfversatz(nabe: Nabe, speichen: Speichensatz | None) -> float:
    """Verschiebung des Ansatzpunktes durch eine einseitige Kopflage.

    Im Normalfall wechseln sich Köpfe innen und außen ab, dann hebt sich der
    Versatz auf und es bleibt bei der Flanschmitte.
    """
    if speichen is None or speichen.straightpull:
        return 0.0
    if speichen.kopf == "innen":
        return nabe.flanschdicke / 2.0
    if speichen.kopf == "außen":
        return -nabe.flanschdicke / 2.0
    return 0.0


def runden(laenge: float, schritt: float = 1.0) -> float:
    """Rundet auf den nächsten verfügbaren Speichenlängen-Schritt."""
    if schritt <= 0:
        return laenge
    return round(laenge / schritt) * schritt


def erd_aus_messung(messlaenge: float, nippelueberstand: float = 0.0) -> float:
    """Hilfsrechnung: ERD aus einer Messung mit zwei eingedrehten Speichen.

    ``messlaenge`` ist der Abstand zwischen den beiden Nippelsitzen, gemessen
    mit zwei gegenüberliegenden Speichen; ``nippelueberstand`` berücksichtigt
    einen bewusst stehen gelassenen Überstand je Seite.
    """
    return messlaenge + 2.0 * nippelueberstand


def flanschabstand_aus_einbaubreite(
    einbaubreite: float, abstand_links: float, abstand_rechts: float
) -> tuple[float, float]:
    """Rechnet Messungen ab Kontermutter in Abstände ab Nabenmitte um.

    ``abstand_links``/``abstand_rechts`` sind die Abstände von der jeweiligen
    Außenseite (Kontermutter/Endkappe) bis zur Flanschmitte.
    """
    mitte = einbaubreite / 2.0
    return mitte - abstand_links, mitte - abstand_rechts


def uebliche_kreuzungen(speichen_seite: int) -> int:
    """Gängige Kreuzungszahl für eine Flanschseite mit ``m`` Speichen.

    Faustregel aus dem Laufradbau: die Speiche soll den Flansch möglichst
    tangential verlassen, ohne dass der Bogen überdehnt wird. Das ergibt
    3-fach ab 16 Speichen je Seite, darunter entsprechend weniger.
    """
    if speichen_seite >= 16:
        return 3
    if speichen_seite >= 12:
        return 3
    if speichen_seite >= 9:
        return 2
    return 1


# --------------------------------------------------------------- Beurteilung


def _hinweise(
    nabe: Nabe,
    felge: Felge,
    einspeichung: Einspeichung,
    links: SeitenErgebnis,
    rechts: SeitenErgebnis,
    speichen: Speichensatz | None = None,
) -> list[str]:
    """Sammelt Plausibilitäts-Hinweise zur Eingabe."""
    meldungen: list[str] = []

    if einspeichung.verteilung == "2:1":
        if einspeichung.speichenzahl % 3 != 0:
            meldungen.append(
                f"Für eine 2:1-Einspeichung muss die Speichenzahl durch 3 teilbar "
                f"sein – {einspeichung.speichenzahl} ist es nicht."
            )
    elif einspeichung.speichenzahl % 4 != 0:
        meldungen.append(
            "Die Speichenzahl ist nicht durch 4 teilbar – die Seiten lassen sich "
            "nicht gleichmäßig aufteilen."
        )

    for seite, ergebnis in (("links", links), ("rechts", rechts)):
        if ergebnis.sehnenwinkel >= 180.0:
            meldungen.append(
                f"{seite.capitalize()}: {ergebnis.kreuzungen}-fach gekreuzt ist bei "
                f"{ergebnis.speichen} Speichen auf dieser Seite geometrisch nicht möglich."
            )
        elif ergebnis.kreuzungen > ergebnis.speichen / 4:
            meldungen.append(
                f"{seite.capitalize()}: {ergebnis.kreuzungen}-fach ist bei "
                f"{ergebnis.speichen} Speichen auf dieser Seite sehr hoch – die "
                "Speichen laufen dann sehr flach am Flansch aus."
            )
        if ergebnis.kreuzungen == 0:
            meldungen.append(
                f"{seite.capitalize()}: radial eingespeicht – nur bei dafür "
                "freigegebenen Naben zulässig (kein Drehmoment)."
            )

    # Die Untergrenze deckt 12-Zoll-Kinderräder mit ab (ERD um 180 mm).
    if felge.erd < 150 or felge.erd > 700:
        meldungen.append(
            f"Der ERD von {zahl(felge.erd, 0)} mm liegt außerhalb des üblichen "
            "Bereichs (etwa 170–640 mm). Bitte nachmessen."
        )

    if nabe.flanschabstand_links <= 0 or nabe.flanschabstand_rechts <= 0:
        meldungen.append(
            "Ein Flanschabstand ist 0 oder negativ – gemessen wird ab der "
            "Nabenmitte bis zur Flanschmitte."
        )

    # Gewarnt wird nur, wenn tatsächlich zwei verschiedene Speichen zu
    # bestellen sind. Runden beide Seiten auf dieselbe Länge, gibt es nichts
    # zu vertauschen – dann steht das als Einordnung weiter unten.
    unterschied = abs(links.laenge - rechts.laenge)
    if unterschied >= 0.05 and links.laenge_gerundet != rechts.laenge_gerundet:
        meldungen.append(
            f"Links und rechts unterscheiden sich um {zahl(unterschied)} mm – "
            "die Speichen nicht vertauschen."
        )

    # Passt die gewählte Bauform nicht zu Spannung oder Radgröße, gehört das
    # zu den Warnungen – nicht zur Einordnung weiter unten.
    typ = felgenkunde.finde(felge.typ)
    if typ is not None:
        meldungen.extend(typ.warnungen(felge.erd, speichen.spannung if speichen else 0.0))

    return meldungen


def _bewertungen(
    felge: Felge,
    einspeichung: Einspeichung,
    links: SeitenErgebnis,
    rechts: SeitenErgebnis,
    spannung_links: float,
    spannung_rechts: float,
    speichen: Speichensatz | None = None,
) -> list[str]:
    """Ordnet das Ergebnis fachlich ein – Orientierung, keine harte Regel."""
    meldungen: list[str] = []

    flacher = min(links.speichenwinkel, rechts.speichenwinkel)
    if flacher < 3.0:
        meldungen.append(
            f"Der flachere Speichenwinkel liegt bei {grad(flacher)} – das ist sehr "
            "flach. Solche Laufräder reagieren empfindlich auf Seitenkräfte."
        )
    elif flacher < 4.5:
        meldungen.append(
            f"Der flachere Speichenwinkel liegt bei {grad(flacher)} – für ein "
            "Hinterrad mit Kassette normal, viel Seitensteifigkeit ist davon "
            "nicht zu erwarten."
        )
    else:
        meldungen.append(
            f"Der flachere Speichenwinkel liegt bei {grad(flacher)} – das ist ein "
            "guter Wert für ein seitensteifes Laufrad."
        )

    schwaecher = min(spannung_links, spannung_rechts)
    if schwaecher < 50.0:
        meldungen.append(
            f"Die schwächere Seite käme nur auf {schwaecher:.0f} % der Spannung. "
            "Unter etwa 50 % lockern sich diese Speichen im Betrieb leicht – eine "
            "asymmetrische Felge oder eine 2:1-Einspeichung hilft dagegen."
        )
    elif schwaecher < 70.0:
        meldungen.append(
            f"Die schwächere Seite liegt bei {schwaecher:.0f} % der Spannung – "
            "typisch für ein Hinterrad und noch unkritisch."
        )
    else:
        meldungen.append(
            f"Beide Seiten liegen mit {schwaecher:.0f} % zu 100 % dicht beieinander – "
            "das Laufrad lässt sich gleichmäßig spannen."
        )

    # Was die Bauform der Felge fürs Einspeichen bedeutet – Ösung, Werkstoff,
    # Profil. Steht kein Felgentyp fest, bleibt der Abschnitt weg.
    typ = felgenkunde.finde(felge.typ)
    if typ is not None:
        meldungen.extend(typ.hinweise())
        bereich = typ.spannungsbereich
        if bereich and speichen is not None:
            meldungen.append(
                f"Für {typ.name} sind {bereich[0]:.0f} bis {bereich[1]:.0f} N "
                "üblich – Anhaltswerte, die Angabe des Felgenherstellers geht vor."
            )

    for seite, ergebnis in (("Links", links), ("Rechts", rechts)):
        empfohlen = uebliche_kreuzungen(ergebnis.speichen)
        if ergebnis.kreuzungen != empfohlen and ergebnis.sehnenwinkel < 180.0:
            meldungen.append(
                f"{seite}: bei {ergebnis.speichen} Speichen auf dieser Seite ist "
                f"{empfohlen}-fach die gängige Wahl; {ergebnis.kreuzungen}-fach "
                "funktioniert, ist aber die Ausnahme."
            )

    if speichen is not None and links.dehnung > 0:
        if speichen.korrektur_anwenden:
            meldungen.append(
                f"Von der Bestelllänge sind {zahl(links.korrektur, 2)} mm abgezogen: "
                f"{zahl(links.dehnung, 2)} mm Dehnung bei {links.spannung:.0f} N"
                + ("" if speichen.straightpull
                   else f", {zahl(speichen.weitung, 2)} mm Weitung von Flansch und Bogen")
                + (f", {zahl(speichen.nippel_verkuerzung, 2)} mm für die Nippel"
                   if speichen.nippel_verkuerzung else "")
                + "."
            )
        else:
            meldungen.append(
                f"Unter Spannung längt sich diese Speiche um etwa "
                f"{zahl(links.dehnung, 2)} mm, dazu weiten sich Flansch und Bogen. "
                "Klassische Rechner lassen das weg; über „Korrektur anwenden“ "
                "lässt es sich berücksichtigen."
            )

    if speichen is not None and rechts.drahtspannung > 0:
        hoechste = max(links.drahtspannung, rechts.drahtspannung)
        meldungen.append(
            f"Im dünnsten Querschnitt herrschen bis zu {zahl(hoechste, 0)} N/mm². "
            "Gezogener Speichendraht hält deutlich mehr aus – die verbindliche "
            "Grenze steht im Datenblatt der Speiche, oft ist ohnehin die Felge "
            "der begrenzende Teil."
        )

    if speichen is not None and speichen.unterlegscheibe > 0:
        meldungen.append(
            f"Die Unterlegscheiben von {zahl(speichen.unterlegscheibe, 1)} mm erhöhen "
            f"den wirksamen ERD um {zahl(2 * speichen.unterlegscheibe, 1)} mm; das ist "
            "in den Längen enthalten."
        )

    enger = min(links.lochabstand, rechts.lochabstand)
    if 0 < enger < 5.0:
        meldungen.append(
            f"Die Speichenlöcher sitzen nur {zahl(enger)} mm auseinander – bei so "
            "engem Lochkreis stoßen die Speichenköpfe leicht aneinander."
        )

    gesamt = links.speichen * links.gewicht + rechts.speichen * rechts.gewicht
    if gesamt > 0:
        meldungen.append(
            f"Die Speichen wiegen zusammen etwa {zahl(gesamt, 0)} g – ohne Nippel, "
            "Kopf und Gewinde gerechnet."
        )

    unterschied = abs(links.laenge - rechts.laenge)
    if unterschied >= 0.05 and links.laenge_gerundet == rechts.laenge_gerundet:
        meldungen.append(
            f"Rechnerisch unterscheiden sich die Seiten um {zahl(unterschied)} mm, "
            f"gerundet ergeben beide {zahl(links.laenge_gerundet)} mm – es ist "
            "also ein einziger Satz Speichen, links und rechts gleich."
        )

    abweichung = max(
        abs(links.laenge - links.laenge_gerundet), abs(rechts.laenge - rechts.laenge_gerundet)
    )
    if abweichung > 0.6:
        meldungen.append(
            f"Gerundet wird um bis zu {zahl(abweichung)} mm. Wenn du die Wahl hast: "
            "lieber die kürzere Speiche nehmen, dann steht sie nicht über den Nippel hinaus."
        )

    return meldungen


# ---------------------------------------------------------------- Berechnung


def berechne(
    nabe: Nabe,
    felge: Felge,
    einspeichung: Einspeichung,
    schritt: float = 1.0,
    speichen: Speichensatz | None = None,
) -> Ergebnis:
    """Berechnet beide Seiten eines Laufrads inklusive Hinweisen.

    Ohne ``speichen`` bleibt es bei der reinen Geometrie. Mit Speichensatz
    kommen Spannung je Seite, elastische Dehnung und Speichenton dazu – und
    auf Wunsch die um die Dehnung korrigierte Bestelllänge.
    """
    # Unterlegscheiben unter dem Nippel verschieben den Nippelsitz nach außen,
    # der wirksame ERD wächst also um zweimal ihre Dicke.
    erd = felge.erd + 2.0 * (speichen.unterlegscheibe if speichen else 0.0)

    # Straightpull-Speichen haben keinen Bogen, der sich am Lochrand anlegt.
    loch = 0.0 if (speichen and speichen.straightpull) else nabe.speichenloch

    # Sitzen alle Köpfe auf derselben Flanschseite, verschiebt sich der
    # Ansatzpunkt um die halbe Flanschdicke.
    kopfversatz = _kopfversatz(nabe, speichen)

    # Asymmetrische Felge: das Speichenbett wandert nach rechts, damit
    # vergrößert sich der wirksame Abstand links und verkleinert sich rechts.
    wirksam_links = nabe.flanschabstand_links + felge.versatz + kopfversatz
    wirksam_rechts = nabe.flanschabstand_rechts - felge.versatz + kopfversatz

    seiten = {}
    for seite, durchmesser, abstand, kreuzungen, anzahl in (
        ("links", nabe.flanschdurchmesser_links, wirksam_links,
         einspeichung.kreuzungen_links, einspeichung.speichen_links),
        ("rechts", nabe.flanschdurchmesser_rechts, wirksam_rechts,
         einspeichung.kreuzungen_rechts, einspeichung.speichen_rechts),
    ):
        laenge = speichenlaenge(
            erd, durchmesser, abstand, einspeichung.speichenzahl,
            kreuzungen, loch, speichen_seite=anzahl,
        )
        seiten[seite] = SeitenErgebnis(
            seite=seite,
            laenge=laenge,
            laenge_gerundet=runden(laenge, schritt),
            speichenwinkel=speichenwinkel(
                erd, durchmesser, abstand, einspeichung.speichenzahl,
                kreuzungen, speichen_seite=anzahl,
            ),
            kreuzungen=kreuzungen,
            speichen=anzahl,
            sehnenwinkel=sehnenwinkel_seite(anzahl, kreuzungen),
            felgenwinkel=felgenwinkel(erd, durchmesser, kreuzungen, anzahl),
            lochabstand=lochabstand(durchmesser, anzahl),
        )

    links, rechts = seiten["links"], seiten["rechts"]
    spannung_links, spannung_rechts = _spannungsanteile(links, rechts)

    if speichen is not None:
        _speichen_eintragen(links, rechts, speichen, spannung_links, spannung_rechts, schritt)

    return Ergebnis(
        links=links,
        rechts=rechts,
        spannung_links_prozent=spannung_links,
        spannung_rechts_prozent=spannung_rechts,
        hinweise=_hinweise(nabe, felge, einspeichung, links, rechts, speichen),
        bewertungen=_bewertungen(
            felge, einspeichung, links, rechts, spannung_links, spannung_rechts, speichen
        ),
    )


def _spannungsanteile(links: SeitenErgebnis, rechts: SeitenErgebnis) -> tuple[float, float]:
    """Spannungsanteile beider Seiten in Prozent.

    Axiales Kräftegleichgewicht: die Summe der Seitenkräfte muss null sein.
    Bei ungleicher Speichenzahl zählt die Seite mit mehr Speichen stärker::

        m_l · T_l · sin(a_l) = m_r · T_r · sin(a_r)

    Die stärker gespannte Seite wird auf 100 % gesetzt.
    """
    hebel_links = links.speichen * math.sin(math.radians(links.speichenwinkel))
    hebel_rechts = rechts.speichen * math.sin(math.radians(rechts.speichenwinkel))
    if hebel_links <= 0 or hebel_rechts <= 0:
        return 100.0, 100.0
    if hebel_links <= hebel_rechts:
        return 100.0, 100.0 * hebel_links / hebel_rechts
    return 100.0 * hebel_rechts / hebel_links, 100.0


def _speichen_eintragen(
    links: SeitenErgebnis,
    rechts: SeitenErgebnis,
    speichen: Speichensatz,
    spannung_links: float,
    spannung_rechts: float,
    schritt: float,
) -> None:
    """Ergänzt Spannung, Dehnung, Ton und ggf. die korrigierte Bestelllänge."""
    bauart = speiche.bauart_nach_name(speichen.bauart, speichen.eigene_bauart)
    # Ohne Bogen gibt es auch keine Bogenweitung.
    weitung = 0.0 if speichen.straightpull else speichen.weitung

    for ergebnis, anteil in ((links, spannung_links), (rechts, spannung_rechts)):
        ergebnis.spannung = speichen.spannung * anteil / 100.0
        ergebnis.dehnung = speiche.dehnung(
            bauart, ergebnis.laenge, ergebnis.spannung, speichen.e_modul
        )
        ergebnis.drahtspannung = speiche.drahtspannung(bauart, ergebnis.spannung)
        ergebnis.frequenz = speiche.frequenz(bauart, ergebnis.laenge, ergebnis.spannung)
        ergebnis.gewicht = speiche.masse(bauart, ergebnis.laenge)
        ergebnis.korrektur = ergebnis.dehnung + weitung + speichen.nippel_verkuerzung
        if speichen.korrektur_anwenden:
            ergebnis.laenge_gerundet = runden(ergebnis.laenge - ergebnis.korrektur, schritt)


def kreuzungsvergleich(
    nabe: Nabe,
    felge: Felge,
    einspeichung: Einspeichung,
    schritt: float = 1.0,
    maximum: int = VERGLEICH_MAXIMUM,
    speichen: Speichensatz | None = None,
) -> list[tuple[int, Ergebnis]]:
    """Rechnet dasselbe Laufrad für 0 bis ``maximum`` Kreuzungen durch.

    Praktisch, um vor dem Bestellen zu sehen, wie viel eine andere
    Kreuzungszahl an Speichenlänge ausmacht.
    """
    ergebnisse = []
    for kreuzungen in range(0, maximum + 1):
        variante = Einspeichung(
            speichenzahl=einspeichung.speichenzahl,
            kreuzungen_links=kreuzungen,
            kreuzungen_rechts=kreuzungen,
            verteilung=einspeichung.verteilung,
        )
        ergebnisse.append((kreuzungen, berechne(nabe, felge, variante, schritt, speichen)))
    return ergebnisse
