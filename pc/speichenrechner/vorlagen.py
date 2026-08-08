"""Vorlagen für Naben und Felgen.

Es gibt zwei Sorten mitgelieferter Vorlagen, am Namen erkennbar:

* **(typisch)** – Anhaltswerte für die Bauart, keine Herstellerangaben.
  Nur als Startpunkt gedacht, unbedingt nachmessen.
* Namentlich genannte Naben (Rohloff, SON) – übernommen aus den
  Herstellerangaben, Stand August 2026. Auch die vor dem Bestellen
  gegenprüfen, Hersteller ändern Maße zwischen Baujahren.

Quellen der Herstellerangaben:

* Rohloff SPEEDHUB 500/14: technische Daten von rohloff.de
  (Speichenlochkreis Ø 100 mm, Flanschabstand 58 mm symmetrisch,
  Speichenloch Ø 2,7 mm; A12-148 mm zusätzlich 3 mm asymmetrisch zur
  Scheibenbremsseite)
* SON-Nabendynamos: Datenblätter der Händlerangaben zu SON 28,
  SON 28 Disc 6-Loch und SONdelux
* White Industries ENO und ENO Flip Flop: Herstellerangaben von whiteind.com
  (ENO: Flansch Ø 60 mm, 32 mm ab Mitte je Seite, O.L.D. 135 mm, Gewinde
  1,37 x 24 tpi; Flip Flop: Flansch Ø 48 mm, 32,5 mm ab Mitte je Seite,
  Speichenloch Ø 2,6 mm, eine Seite mit Schraubkranzgewinde). Beide sind
  symmetrisch – sie tragen kein Ritzelpaket, das rechts Platz beansprucht.

Eigene Vorlagen landen in ``~/.config/speichenrechner/vorlagen.json`` und
überschreiben mitgelieferte Einträge mit gleichem Namen nicht, sondern
stehen zusätzlich in der Liste.
"""

from __future__ import annotations

import json
from pathlib import Path

from .modelle import Felge, Nabe
from .pfade import konfig_verzeichnis

VORLAGEN_DATEI = "vorlagen.json"

#: Nabengeometrien: Bauart-Anhaltswerte und Herstellerangaben.
NABEN_VORLAGEN: tuple[Nabe, ...] = (
    Nabe("Vorderrad 100 mm, Felgenbremse (typisch)", 38.0, 38.0, 35.0, 35.0,
         art="Vorderrad"),
    Nabe("Vorderrad 100 mm, Scheibenbremse (typisch)", 45.0, 38.0, 32.0, 22.0,
         art="Vorderrad"),
    Nabe("Vorderrad Boost 110 mm, Scheibe (typisch)", 45.0, 38.0, 37.0, 25.0,
         art="Vorderrad"),
    Nabe("Hinterrad 130 mm, Felgenbremse (typisch)", 45.0, 45.0, 36.0, 19.0,
         art="Hinterrad", aufnahme="Kassette"),
    Nabe("Hinterrad 135 mm, Scheibenbremse (typisch)", 45.0, 45.0, 37.0, 19.0,
         art="Hinterrad", aufnahme="Kassette"),
    Nabe("Hinterrad 142x12 mm, Scheibe (typisch)", 45.0, 45.0, 36.0, 19.0,
         art="Hinterrad", aufnahme="Kassette"),
    Nabe("Hinterrad Boost 148 mm, Scheibe (typisch)", 45.0, 45.0, 39.0, 21.0,
         art="Hinterrad", aufnahme="Kassette"),
    # Schraubkranznabe: rechts nimmt der aufgeschraubte Kranz Platz weg, der
    # Flansch sitzt deshalb ähnlich weit innen wie bei einer Kassettennabe.
    # Anhaltswerte für die Bauart – wie bei allen „(typisch)“-Vorlagen.
    Nabe("Hinterrad Schraubkranz 126 mm (typisch)", 45.0, 45.0, 33.0, 19.0,
         art="Hinterrad", aufnahme="Schraubkranz"),
    # Zwei Naben, die heute noch mit Schraubkranzgewinde 1,375" x 24 TPI gebaut
    # werden – Herstellerangaben, symmetrisch weil sie kein Ritzelpaket tragen.
    Nabe("White Industries ENO (Schraubkranz, 135 mm)", 60.0, 60.0, 32.0, 32.0,
         art="Hinterrad", aufnahme="Schraubkranz"),
    Nabe("White Industries ENO Flip Flop (Schraubkranz)", 48.0, 48.0, 32.5, 32.5, 2.6,
         art="Hinterrad", aufnahme="Schraubkranz"),
    # Rohloff: Lochkreis Ø 100 mm, Flanschabstand 58 mm (± 29 mm), Loch Ø 2,7 mm.
    # Die Ritzel werden aufgeschraubt, nicht auf einen Freilaufkörper gesteckt.
    Nabe("Rohloff SPEEDHUB 500/14 (135/142 mm)", 100.0, 100.0, 29.0, 29.0, 2.7,
         art="Nabenschaltung", aufnahme="Schraubritzel"),
    # A12-148: derselbe Flanschabstand, um 3 mm zur Scheibenbremsseite versetzt.
    Nabe("Rohloff SPEEDHUB 500/14 A12 (148 mm, asym.)", 100.0, 100.0, 32.0, 26.0, 2.7,
         art="Nabenschaltung", aufnahme="Schraubritzel"),
    # SON: Flanschabstände laut Datenblatt, Speichenloch Ø 2,0 mm.
    # Lochkreis Ø 54 mm und Speichenloch Ø 2,8 mm stehen so in der Werkszeichnung
    # von Schmidt. Hier stand vorher Ø 69 – falsch, und um 3 mm zu kurze Speichen.
    Nabe("SON 28 Nabendynamo (Felgenbremse, 100 mm)", 54.0, 54.0, 31.0, 31.0, 2.8,
         art="Dynamo"),
    Nabe("SON 28 Disc 6-Loch Nabendynamo", 59.0, 54.0, 22.5, 25.0, 2.0, art="Dynamo"),
    Nabe("SONdelux Nabendynamo (Felgenbremse)", 54.0, 54.0, 25.0, 25.0, 2.0, art="Dynamo"),
)

#: Typische ERD-Werte je Felgengröße.
FELGEN_VORLAGEN: tuple[Felge, ...] = (
    Felge("28\" / 700C (ETRTO 622), Rennfelge (typisch)", 602.0),
    Felge("28\" / 700C (ETRTO 622), Trekking (typisch)", 596.0),
    Felge("27,5\" (ETRTO 584), MTB (typisch)", 560.0),
    Felge("26\" (ETRTO 559), MTB (typisch)", 536.0),
    Felge("24\" (ETRTO 507), Jugendrad (typisch)", 484.0),
    Felge("20\" (ETRTO 406), Falt-/Lastenrad (typisch)", 384.0),
    Felge("18\" (ETRTO 355), Kinderrad (typisch)", 334.0),
    Felge("16\" (ETRTO 349), Faltrad (typisch)", 328.0),
    Felge("16\" (ETRTO 305), Kinderrad (typisch)", 283.0),
    Felge("12\" (ETRTO 203), Kinderrad (typisch)", 180.0),
)


def _datei() -> Path:
    return konfig_verzeichnis() / VORLAGEN_DATEI


def _lade_roh() -> dict:
    pfad = _datei()
    if not pfad.exists():
        return {"naben": [], "felgen": []}
    try:
        daten = json.loads(pfad.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"naben": [], "felgen": []}
    return {
        "naben": daten.get("naben", []) if isinstance(daten, dict) else [],
        "felgen": daten.get("felgen", []) if isinstance(daten, dict) else [],
    }


def _speichere_roh(daten: dict) -> None:
    pfad = _datei()
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8")


def eigene_naben() -> list[Nabe]:
    return [Nabe.from_dict(eintrag) for eintrag in _lade_roh()["naben"]]


def eigene_felgen() -> list[Felge]:
    return [Felge.from_dict(eintrag) for eintrag in _lade_roh()["felgen"]]


def alle_naben(art: str = "") -> list[Nabe]:
    """Mitgelieferte und eigene Nabenvorlagen in Anzeigereihenfolge.

    Mit ``art`` bleiben nur Vorlagen mit diesem Merkmal übrig – geprüft wird
    gegen Bauart **und** Ritzelaufnahme, genau wie im Nabenkatalog. Eine
    Rohloff-Vorlage steht damit unter „Nabenschaltung“ wie unter
    „Schraubritzel“. Eigene Vorlagen ohne Angaben werden ausgeblendet: ein
    Filter soll die Liste kürzen, sonst wirkt er wirkungslos.
    """
    naben = list(NABEN_VORLAGEN) + eigene_naben()
    if not art:
        return naben
    return [nabe for nabe in naben if art in nabe.merkmale]


def alle_felgen() -> list[Felge]:
    """Mitgelieferte und eigene Felgenvorlagen in Anzeigereihenfolge."""
    return list(FELGEN_VORLAGEN) + eigene_felgen()


def speichere_nabe(nabe: Nabe) -> None:
    """Legt eine eigene Nabenvorlage an oder aktualisiert sie ueber den Namen."""
    daten = _lade_roh()
    daten["naben"] = [e for e in daten["naben"] if e.get("name") != nabe.name]
    daten["naben"].append(nabe.as_dict())
    _speichere_roh(daten)


def speichere_felge(felge: Felge) -> None:
    """Legt eine eigene Felgenvorlage an oder aktualisiert sie ueber den Namen."""
    daten = _lade_roh()
    daten["felgen"] = [e for e in daten["felgen"] if e.get("name") != felge.name]
    daten["felgen"].append(felge.as_dict())
    _speichere_roh(daten)


def loesche_nabe(name: str) -> bool:
    daten = _lade_roh()
    rest = [e for e in daten["naben"] if e.get("name") != name]
    if len(rest) == len(daten["naben"]):
        return False
    daten["naben"] = rest
    _speichere_roh(daten)
    return True


def loesche_felge(name: str) -> bool:
    daten = _lade_roh()
    rest = [e for e in daten["felgen"] if e.get("name") != name]
    if len(rest) == len(daten["felgen"]):
        return False
    daten["felgen"] = rest
    _speichere_roh(daten)
    return True


def ist_eigene_nabe(name: str) -> bool:
    return any(n.name == name for n in eigene_naben())


def ist_eigene_felge(name: str) -> bool:
    return any(f.name == name for f in eigene_felgen())
