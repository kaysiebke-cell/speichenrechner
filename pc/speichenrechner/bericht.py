"""Ergebnis als Text – für Zwischenablage und Textdatei."""

from __future__ import annotations

from .formatierung import grad, mm, zahl
from .modelle import VERTEILUNGEN, Einspeichung, Ergebnis, Felge, Nabe, Speichensatz
from .speiche import note

BREITE = 52


def _abschnitt(titel: str) -> list[str]:
    return ["", titel, "-" * BREITE]


def als_text(
    nabe: Nabe,
    felge: Felge,
    einspeichung: Einspeichung,
    ergebnis: Ergebnis,
    speichen: Speichensatz | None = None,
) -> str:
    """Formatiert die komplette Berechnung als lesbaren Fließtext."""
    zeilen = ["Speichenrechner – Ergebnis", "=" * BREITE]

    zeilen += _abschnitt("Zu bestellen")
    zeilen += [f"  {eintrag}" for eintrag in ergebnis.einkaufsliste]

    zeilen += _abschnitt("Laufrad")
    zeilen += [
        f"  Nabe                 {nabe.name}",
        f"    Flanschdurchmesser links {mm(nabe.flanschdurchmesser_links)} | "
        f"rechts {mm(nabe.flanschdurchmesser_rechts)}",
        f"    Flanschabstand     links {mm(nabe.flanschabstand_links)} | "
        f"rechts {mm(nabe.flanschabstand_rechts)}",
        f"    Speichenloch       {mm(nabe.speichenloch)}",
        f"  Felge                {felge.name}",
        f"    ERD                {mm(felge.erd)}",
        f"    Versatz            {mm(felge.versatz)}",
    ]
    if felge.typ:
        zeilen.append(f"    Typ                {felge.typ}")
    zeilen += [
        f"  Einspeichung         {einspeichung.speichenzahl} Speichen, "
        f"{VERTEILUNGEN.get(einspeichung.verteilung, einspeichung.verteilung)}",
        f"    links              {einspeichung.speichen_links} Speichen, "
        f"{einspeichung.kreuzungen_links}-fach",
        f"    rechts             {einspeichung.speichen_rechts} Speichen, "
        f"{einspeichung.kreuzungen_rechts}-fach",
    ]

    zeilen += _abschnitt("Speichenlängen")
    for seite, bezeichnung in ((ergebnis.links, "Links "), (ergebnis.rechts, "Rechts")):
        zeilen += [
            f"  {bezeichnung}  {mm(seite.laenge_gerundet)}   (exakt {mm(seite.laenge, 2)})",
            f"    {seite.speichen} Speichen, {seite.kreuzungen}-fach gekreuzt",
            f"    Speichenwinkel {grad(seite.speichenwinkel)}, "
            f"Winkel an der Felge {grad(seite.felgenwinkel)}, "
            f"Lochabstand am Flansch {mm(seite.lochabstand)}",
        ]

    if speichen is not None:
        zeilen += _abschnitt("Speichen")
        zeilen += [
            f"  Bauart               {speichen.bauart}"
            + ("  (Straightpull)" if speichen.straightpull else ""),
            f"  E-Modul              {zahl(speichen.e_modul, 0)} N/mm²",
        ]
        for seite, bezeichnung in ((ergebnis.links, "links "), (ergebnis.rechts, "rechts")):
            zeilen.append(
                f"  {bezeichnung}               {seite.spannung:.0f} N, "
                f"Dehnung {mm(seite.dehnung, 2)}, "
                f"Ton {seite.frequenz:.0f} Hz ({note(seite.frequenz)}), "
                f"{zahl(seite.gewicht, 1)} g, "
                f"{zahl(seite.drahtspannung, 0)} N/mm² im Draht"
            )
        if speichen.korrektur_anwenden:
            zeilen.append(
                f"  Von der Bestelllänge abgezogen: Dehnung, Weitung "
                f"{mm(speichen.weitung, 2)}, Nippel {mm(speichen.nippel_verkuerzung, 1)}."
            )

    zeilen += _abschnitt("Spannungsverhältnis")
    zeilen += [
        f"  links {ergebnis.spannung_links_prozent:.0f} %   |   "
        f"rechts {ergebnis.spannung_rechts_prozent:.0f} %"
    ]

    if ergebnis.bewertungen:
        zeilen += _abschnitt("Einschätzung")
        zeilen += [f"  • {eintrag}" for eintrag in ergebnis.bewertungen]

    if ergebnis.hinweise:
        zeilen += _abschnitt("Hinweise")
        zeilen += [f"  ! {hinweis}" for hinweis in ergebnis.hinweise]

    zeilen += [
        "",
        "Angaben ohne Gewähr – vor dem Bestellen ERD und Nabenmaße nachmessen.",
    ]
    return "\n".join(zeilen)
