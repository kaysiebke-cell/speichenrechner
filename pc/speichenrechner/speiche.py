"""Die Speiche selbst: Bauart, Dehnung unter Spannung, Gewicht und Ton.

Die reine Geometrie sagt, wie lang die Speiche im **gespannten** Laufrad sein
muss. Verkauft wird sie aber ungespannt, und unter Zug längt sie sich:

    ΔL = F/E · Σ (lᵢ / Aᵢ)

Eine konifizierte Speiche wird dafür in drei Abschnitte zerlegt – verdicktes
Kopfteil, verdickter unterer Teil und dünnes Mittelteil. Im Mittelteil steckt
der weitaus größte Anteil der Dehnung.

``E`` ist der Elastizitätsmodul. Für nichtrostenden Speichendraht (18/8) wird
im Laufradbau mit rund **180 000 N/mm²** gerechnet, spürbar weniger als bei
gewöhnlichem Baustahl.

Der Speichenton folgt der Saitenformel::

    f = 1/(2·L) · √(F / µ)      mit  µ = ρ · A

Er gilt für eine frei schwingende Saite. Am eingespeichten Rad schwingt nur der
Abschnitt zwischen der letzten Kreuzung und dem Nippel – der klingt höher. Der
Wert taugt zum Vergleich der Speichen untereinander, ein Tensiometer bleibt
genauer.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

#: Elastizitätsmodul nichtrostender Speichen in N/mm².
E_MODUL = 180_000.0

#: Dichte Stahl in kg/m³ bzw. g/mm³.
DICHTE = 7850.0
DICHTE_G_MM3 = 7.85e-3

#: Übliche Speichenspannung in N (Richtwert für die stärker gespannte Seite).
SPANNUNG_STANDARD = 1000.0

#: Übliche Weitung von Nabenflansch und Speichenbogen unter Last, in mm.
WEITUNG_STANDARD = 0.1

#: Name der frei einstellbaren Bauart.
EIGENE_BAUART = "eigene Maße …"

#: Deutsche Notennamen – H statt B.
NOTEN = ("c", "cis", "d", "dis", "e", "f", "fis", "g", "gis", "a", "ais", "h")


@dataclass(frozen=True)
class Bauart:
    """Eine Speichenbauart, zerlegt in ihre drei Abschnitte.

    ``laenge_kopf``/``laenge_unten`` sind die verdickten Enden, der Rest der
    Speiche hat den Mittelquerschnitt. ``flaeche_mitte_direkt`` überschreibt
    die Berechnung aus dem Durchmesser – nötig bei flachen Messerspeichen.
    """

    name: str
    durchmesser_kopf: float
    durchmesser_unten: float
    durchmesser_mitte: float
    laenge_kopf: float = 15.0
    laenge_unten: float = 20.0
    flaeche_mitte_direkt: float | None = None

    @staticmethod
    def _flaeche(durchmesser: float) -> float:
        return math.pi / 4.0 * durchmesser**2

    @property
    def flaeche_kopf(self) -> float:
        return self._flaeche(self.durchmesser_kopf)

    @property
    def flaeche_unten(self) -> float:
        return self._flaeche(self.durchmesser_unten)

    @property
    def flaeche_mitte(self) -> float:
        if self.flaeche_mitte_direkt is not None:
            return self.flaeche_mitte_direkt
        return self._flaeche(self.durchmesser_mitte)


#: Gängige Bauarten. Die Abschnittslängen sind Näherungen – Hersteller weichen ab.
BAUARTEN: tuple[Bauart, ...] = (
    Bauart("2,0 mm durchgehend (14 G)", 2.0, 2.0, 2.0, 0.0, 0.0),
    Bauart("2,0/1,8/2,0 doppelt konifiziert", 2.0, 2.0, 1.8),
    Bauart("2,0/1,7/2,0 doppelt konifiziert", 2.0, 2.0, 1.7),
    Bauart("2,0/1,7/1,8 dreifach konifiziert", 2.0, 1.8, 1.7),
    Bauart("2,0/1,5/2,0 sehr leicht", 2.0, 2.0, 1.5),
    Bauart("1,8/1,6/1,8 dünn", 1.8, 1.8, 1.6),
    Bauart("Messerspeiche flach, ≈ 2,3 × 1,2 mm", 2.0, 2.0, 0.0, 15.0, 20.0, 2.2),
)


#: Startwerte der frei einstellbaren Bauart (entspricht 2,0/1,7/1,8).
EIGENE_VORGABE = {
    "durchmesser_kopf": 2.0,
    "durchmesser_unten": 1.8,
    "durchmesser_mitte": 1.7,
    "laenge_kopf": 15.0,
    "laenge_unten": 20.0,
}


def bauart_nach_name(name: str, eigene: dict | None = None) -> Bauart:
    """Sucht eine Bauart; ``eigene`` liefert die frei eingestellten Maße."""
    if name == EIGENE_BAUART:
        werte = dict(EIGENE_VORGABE)
        werte.update(eigene or {})
        return Bauart(EIGENE_BAUART, **werte)
    for bauart in BAUARTEN:
        if bauart.name == name:
            return bauart
    return BAUARTEN[0]



def abschnitte(bauart: Bauart, laenge: float) -> tuple[tuple[float, float], ...]:
    """Zerlegt die Speiche in ``(Länge, Querschnitt)``-Abschnitte."""
    enden = bauart.laenge_kopf + bauart.laenge_unten
    if enden >= max(laenge - 10.0, 0.0):
        # Sehr kurze Speiche: Enden anteilig kürzen, damit nichts negativ wird.
        anteil = max(laenge - 10.0, 0.0) / enden if enden > 0 else 0.0
        kopf = bauart.laenge_kopf * anteil
        unten = bauart.laenge_unten * anteil
    else:
        kopf, unten = bauart.laenge_kopf, bauart.laenge_unten

    mitte = max(laenge - kopf - unten, 0.0)
    return (
        (kopf, bauart.flaeche_kopf),
        (unten, bauart.flaeche_unten),
        (mitte, bauart.flaeche_mitte),
    )


def dehnung(bauart: Bauart, laenge: float, spannung: float, e_modul: float = E_MODUL) -> float:
    """Elastische Längung in mm bei ``spannung`` in Newton."""
    if laenge <= 0 or spannung <= 0 or e_modul <= 0:
        return 0.0
    nachgiebigkeit = sum(
        teillaenge / flaeche
        for teillaenge, flaeche in abschnitte(bauart, laenge)
        if flaeche > 0
    )
    return spannung / e_modul * nachgiebigkeit


def drahtspannung(bauart: Bauart, spannung: float) -> float:
    """Zugspannung im dünnsten Querschnitt in N/mm².

    Gängiger Speichendraht hält deutlich über 1000 N/mm² aus; der Wert dient
    dem Vergleich, die Grenze steht im Datenblatt der Speiche.
    """
    if bauart.flaeche_mitte <= 0:
        return 0.0
    return spannung / bauart.flaeche_mitte


def masse(bauart: Bauart, laenge: float) -> float:
    """Ungefähres Gewicht einer Speiche in Gramm.

    Gerechnet wird das reine Drahtvolumen – Kopf, Bogen und Gewinde sind nicht
    enthalten, der wahre Wert liegt einige Zehntel Gramm darüber.
    """
    if laenge <= 0:
        return 0.0
    volumen = sum(teillaenge * flaeche for teillaenge, flaeche in abschnitte(bauart, laenge))
    return volumen * DICHTE_G_MM3


def frequenz(bauart: Bauart, freie_laenge: float, spannung: float) -> float:
    """Grundfrequenz der frei schwingenden Speiche in Hz.

    Maßgeblich ist der dünnste Querschnitt, denn dort liegt der größte Teil der
    schwingenden Länge.
    """
    if freie_laenge <= 0 or spannung <= 0:
        return 0.0
    flaeche_m2 = bauart.flaeche_mitte * 1e-6
    if flaeche_m2 <= 0:
        return 0.0
    masse_je_meter = DICHTE * flaeche_m2
    laenge_m = freie_laenge / 1000.0
    return 1.0 / (2.0 * laenge_m) * math.sqrt(spannung / masse_je_meter)


def note(hertz: float) -> str:
    """Nächstgelegener Notenname, z. B. ``"g¹"`` – leer bei ungültiger Frequenz."""
    if hertz <= 0:
        return ""
    halbtoene = round(12.0 * math.log2(hertz / 440.0)) + 69  # MIDI-Nummer
    name = NOTEN[halbtoene % 12]
    oktave = halbtoene // 12 - 1

    # Deutsche Schreibweise: große Oktave in Versalien, ab c¹ mit Strichen.
    if oktave <= 3:
        striche = "͵" * max(3 - oktave, 0)
        return f"{name.upper()}{striche}"
    striche = "¹²³⁴⁵⁶"[min(oktave - 4, 5)]
    return f"{name}{striche}"
