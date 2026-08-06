# Speichenrechner

Speichenlängen für Fahrradlaufräder berechnen. Zwei Fassungen, ein Repo:

* **PC** – eine GTK-3-Anwendung in Python für Linux Mint (Cinnamon), in
  `speichenrechner/`. Sie bringt bewusst kein eigenes Farbschema mit: Schrift,
  Farben, Icons und die Hell/Dunkel-Variante kommen aus den
  System-Einstellungen, sie passt sich also dem eingestellten Mint-Theme an.
* **Handy** – eine Web-Fassung in `public/`, die ohne Netz läuft und sich auf
  dem Startbildschirm ablegen lässt. Siehe [Handy-Version](#handy-version).

![Speichenrechner im dunklen Mint-Theme](data/screenshot.png)

## Installation

Voraussetzung ist PyGObject mit GTK 3 – auf Linux Mint ist beides normalerweise
schon vorhanden. Falls nicht:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0
```

Menüeintrag und Schreibtisch-Icon anlegen (ohne `sudo`, nur für den aktuellen
Benutzer):

```bash
./install.sh
```

Danach liegt der Speichenrechner im Menü unter *Zubehör*, zusätzlich als
anklickbares Icon auf dem Schreibtisch. Wieder entfernen:

```bash
./install.sh --entfernen
```

Direkt starten geht auch ohne Installation:

```bash
python3 speichenrechner.py
```

### Wenn nichts passiert

Erst den Selbsttest laufen lassen – er startet keine Oberfläche, sondern meldet,
was fehlt:

```bash
python3 speichenrechner.py --pruefen
```

Der Speichenrechner ist eine **Einzelinstanz-Anwendung**: Läuft schon ein
Fenster – auch minimiert oder auf einer anderen Arbeitsfläche –, holt ein
zweiter Start nur dieses nach vorn, es öffnet sich kein neues. Nachsehen mit:

```bash
pgrep -af speichenrechner.py
```

Für eine Fehlermeldung im Klartext hilft der Start aus dem Terminal:

```bash
python3 /home/kaysiebke/Downloads/Speichenrechner/speichenrechner.py
```

### Wo das Icon liegt

`./install.sh` legt drei Dinge an:

| Was | Wo |
|---|---|
| Verknüpfung auf dem Schreibtisch | `~/Desktop/de.speichenrechner.Speichenrechner.desktop` |
| Eintrag im Menü unter *Zubehör* | `~/.local/share/applications/de.speichenrechner.Speichenrechner.desktop` |
| Icon-Grafik | `~/.local/share/icons/hicolor/scalable/apps/de.speichenrechner.Speichenrechner.svg` |

Erscheint die Verknüpfung nicht auf dem Schreibtisch, muss Cinnamon den
Schreibtisch neu zeichnen – ab- und wieder anmelden genügt, oder:

```bash
nemo-desktop --quit && (nemo-desktop &)
```

## Bedienung

1. **Nabe** – Flanschdurchmesser und Flanschabstand je Seite eintragen. Der
   Flanschabstand wird von der Nabenmitte bis zur Flanschmitte gemessen. Über
   *Flanschabstand aus Einbaubreite …* lassen sich stattdessen die leichter
   messbaren Maße ab Kontermutter eingeben – und Werte aus fremden
   Nabendatenbanken, siehe [Werte aus fremden Datenbanken](#werte-aus-fremden-datenbanken).
2. **Felge** – ERD eintragen (effektiver Felgendurchmesser von Nippelsitz zu
   Nippelsitz, **nicht** der Reifensitz). Bei asymmetrischen Felgen zusätzlich
   den Versatz: minus = Speichenbett nach links, plus = nach rechts. Darunter
   steht der **Felgentyp** – siehe [Felgentypen](#felgentypen).
3. **Einspeichung** – Speichenzahl, Verteilung und Kreuzungen. 0 Kreuzungen
   bedeutet radial. Bei „2:1“ trägt die rechte Seite doppelt so viele Speichen.
4. **Speichen** – Bauart, Zielspannung, Kopflage und Straightpull. Über den
   Stift-Knopf lassen sich Abschnittsmaße und E-Modul frei einstellen.
5. **Nippel und Korrektur** – Unterlegscheiben, Nippel-Verkürzung und Weitung.
   Der Haken zieht die Summe aus Dehnung, Weitung und Nippel-Verkürzung von der
   Bestelllänge ab.

Das Ergebnis erscheint sofort: gerundete Länge je Seite, der exakte Wert, der
Speichenwinkel, was zu bestellen ist, das Spannungsverhältnis, Dehnung, Gewicht
und Speichenton. Plausibilitätsprobleme (unmögliche Kreuzungszahl, ungewöhnlicher
ERD, große Seitendifferenz) werden als Hinweis eingeblendet, dazu kommt eine
fachliche Einschätzung zu Speichenwinkel und Spannungsverhältnis.

Wer nicht weiß, was genau zu messen ist, klickt das Augen-Symbol neben der
Überschrift **Nabe** oder **Felge** – oder direkt auf den Reiter **Messen**. Die
**Übersicht** zeigt alle drei Maße in einem Bild – die klassische Skizze mit
`a` (Flanschabstand ab Nabenmitte), `d` (Flansch-Lochkreis) und `D` (ERD).
Daneben liegt für jedes Maß eine eigene Skizze mit erkennbaren Bauteilen: Nabe
von der Seite für Flansch-Ø und Flanschabstand, zwei Felgenprofile im Schnitt
für den ERD. Die
Maßlinien tragen die **tatsächlich eingegebenen Werte**, und die gezeichnete
Nabe übernimmt die Verhältnisse: ein Hinterrad zeigt seinen kurzen rechten
Abstand auch als kurzen Abstand. Klickt man in ein Eingabefeld, schaltet die
Ansicht von selbst auf das passende Maß.

Die Nabe entsteht als **Drehteil-Kontur** – eine Linie über Achsstummel,
Endkappe, Lagersitz, Flansch, Taille und Freilaufkörper und zurück. Deshalb
sind die Flansche angeformt und nicht angeklebt. Die Felge ist entsprechend
Blech: Kontur in Wandstärke gezeichnet, mit Öse am Nippelsitz. Die Farben
kommen aus dem Theme – der Nabenkörper trägt den Akzent, Freilauf und Achse
bleiben neutral, ein senkrechter Verlauf macht daraus ein rundes Bauteil. Feste
Farbwerte gibt es nicht, damit jedes Theme passt.

**Gezeichnet wird, was gewählt ist.** Bauart und Ritzelaufnahme kommen aus der
Vorlage oder dem Nabenkatalog und bestimmen die Form:

| Bauart / Aufnahme | Antriebsseite | Nabenschale |
|---|---|---|
| Vorderrad | nichts, rechts wie links abgesetzt | schlank |
| Dynamo | nichts | dick – darin sitzt der Generator |
| Hinterrad + Kassette / Steckritzel / Steckzahnkranz | Freilaufkörper mit Längsverzahnung | schlank |
| Hinterrad + Schraubkranz / Schraubritzel / Singlespeed | Gewindestummel | schlank |
| Nabenschaltung | Gewindestummel – **nie** ein Kassettenkörper | dick – darin sitzt das Getriebe |

Bei einer Getriebenabe sitzt das Ritzel auf einem kurzen Stummel, auch wenn die
Tabelle „Steckritzel“ nennt; ein Kassettenkörper wäre dort falsch. Die
Nabenschale ist gedeckelt: bei kleinem Lochkreis wird der Körper nie dicker als
der Flansch, sonst verschwände der Flansch darin.

Auf die Speichenlänge hat das **keinen** Einfluss – die hängt allein an der
Geometrie. Ein Test hält das fest.

Über die Kopfleiste lässt sich das Ergebnis in die Zwischenablage kopieren oder
als Textdatei sichern, über das Menü die aktuelle Skizze als PNG, PDF oder SVG
exportieren. Häufig gebrauchte Naben und Felgen lassen sich als eigene Vorlage
speichern; die zuletzt eingegebenen Werte stehen beim nächsten Start wieder da.

### Aufteilung des Fensters

Links stehen die Eingaben in zwei Reitern – **Laufrad** (Nabe, Felge,
Einspeichung) und **Speichen** (Bauart, Nippel, Korrektur). So bleibt das
Nötigste auf einem Blick, ohne dass das Fenster in die Höhe wächst.

Rechts liegen die Ergebnisse; Länge, Bestellmenge und Warnungen sind immer
sichtbar, der Rest steckt in Reitern:

| Reiter | Was er zeigt |
|---|---|
| **Speichenbild** | Aufsicht aufs Rad: Kreuzungsmuster beider Seiten, eine Speiche hervorgehoben, dazu der Sehnenwinkel an der Nabe |
| **Querschnitt** | Maßstäblicher Ausschnitt am Nabenbereich: Flanschabstände, Nabenkörper und die Speichen mit ihrem echten Winkel |
| **Messen** | Übersicht mit `a`, `d`, `D` plus je eine Skizze pro Maß, alle mit den eingegebenen Werten – folgt dem Eingabefeld, in dem man gerade steht |
| **Vergleich** | Tabelle über 0- bis 4-fach gekreuzt – was eine andere Kreuzungszahl an Länge und Winkel ausmacht |
| **Spannung** | Spannungsverhältnis der Seiten, Dehnung, Speichenton und Gewicht |
| **Bewertung** | fachliche Einschätzung zu Winkel, Spannung und Kreuzungszahl |

Beide Spalten lassen sich rollen und schrumpfen, die Trennlinie richtet sich
nach dem Platzbedarf der Eingabefelder.

![Querschnitt](data/querschnitt.png)

### Nabenkatalog

Die Auswahlliste im Abschnitt **Nabe** enthält neben den Vorlagen auch 218
Modelle von 14 Herstellern (Hope, SON, Shimano, Rohloff, SRAM,
Sturmey-Archer, Enviolo, Pinion, Shutter Precision, Supernova, Kindernay,
Classified, Effigear, Fichtel & Sachs) – kein zweites Fenster, kein Menü.

Darüber stehen zwei Filter – **Nabenart** und **Hersteller** –, die die Liste
kurz halten. Sie gelten für **alles** in der Liste, auch für die mitgelieferten
Vorlagen: bei „Kassette“ verschwinden Dynamos und Getriebenaben, bei einem
gewählten Hersteller bleiben nur dessen Modelle. Die Herstellerliste passt sich der gewählten Art an: bei „Dynamo“
stehen dort nur die sechs Hersteller, die auch Dynamos führen. Passt die
bisherige Herstellerwahl nicht mehr zur neuen Art, springt sie auf „alle
Hersteller“ zurück.

**Bauart und Ritzelaufnahme sind zwei verschiedene Dinge** und stehen
nebeneinander in derselben Liste. Eine Nabe taucht unter jedem ihrer Merkmale
auf: eine Rohloff unter *Nabenschaltung* wie unter *Schraubritzel*, ein
SON-Dynamo unter *Dynamo* wie unter *Vorderrad*.

| Merkmal | Naben | Hersteller |
|---|---|---|
| Vorderrad | 90 | Hope, SON, Shimano, Shutter Precision, SRAM, Sturmey-Archer, Supernova |
| Nabenschaltung | 73 | Classified, Enviolo, Fichtel & Sachs, Kindernay, Rohloff, Shimano, SRAM, Sturmey-Archer |
| Dynamo | 69 | SON, Shimano, Shutter Precision, SRAM, Sturmey-Archer, Supernova |
| Hinterrad | 40 | Hope, Shimano |
| Kassette | 34 | Classified, Hope, Kindernay, Shimano, SRAM |
| Schraubritzel | 26 | Rohloff |
| Steckritzel | 17 | Shimano, Sturmey-Archer |
| Steckzahnkranz | 9 | Enviolo |
| Schraubkranz | 6 | Hope, Sturmey-Archer |
| Singlespeed | 5 | Hope |

Die Bauart kommt aus dem Tabellenblatt, die Ritzelaufnahme aus der Spalte
*Kassetten-/Freilaufkörper-Typ*.

**Tretlager-Getriebe stehen nicht in der Nabenauswahl.** Die Tabelle trennt sie
im Blatt *Nabenschaltung* mit der Zeile „folgende Systeme sind KEINE
einspeichbaren Laufradnaben, sondern Tretlager-Getriebe“ ab; die 15 Pinion- und
Effigear-Systeme dahinter haben kein Speichenloch. Im Katalog bleiben sie
erhalten und sind im Fenster *Nabentabelle* zu sehen – nur eben nicht dort, wo
man eine Nabe zum Einspeichen wählt.

> Was die Tabelle nicht führt, kann kein Filter zeigen. Von Shimano, SRAM und
> Sturmey-Archer stehen dort nur Dynamo- und Nabenschaltungsblätter – deren
> gewöhnliche Naben mit Schraubkranz fehlen also. Über *Menü → Nabentabelle
> bearbeiten … → Nabe hinzufügen* lassen sie sich ergänzen, ohne die
> Excel-Datei anzufassen.

Der Freilauftyp steht auch in der Auswahlliste, gekürzt auf die Standards –
aus „Shimano HG (9–11-fach), Shimano Micro Spline (12-fach) und SRAM XD“ wird
`HG · Micro Spline · XD`. Gesucht wird über den vollen Text, `micro spline`
findet also alle passenden Naben.

> Dass unter *Kassette* und *Vorderrad* nur Hope steht, liegt an der Tabelle:
> sie führt von Shimano, SRAM und Sturmey-Archer ausschließlich Dynamo- und
> Nabenschaltungsblätter, keine gewöhnlichen Naben. Kommt ein Blatt mit
> Shimano-Kassettennaben dazu, tauchen sie ohne weiteres Zutun unter
> *Kassette* auf.

Die Liste ist **eintippbar**: „son disc“ oder „boost“ filtert sofort, egal an
welcher Stelle im Namen der Begriff steht. Jede Zeile zeigt Modell,
Einbaubreite, Lochzahl und Bremsaufnahme.

**72 Naben sind rechenfertig** – sie führen auch Flanschabstand und Flansch-Ø
und stehen deshalb oben in der Liste, gekennzeichnet mit „✓ mit Flanschmaßen“.
Ein Klick genügt, die Länge steht sofort da.

Bei den übrigen setzt der Rechner Speichenloch-Ø und Lochzahl, merkt sich die
Einbaubreite für die Umrechnung „Flanschabstand aus Einbaubreite …“ und trägt
den Modellnamen in den Ergebnisbericht ein; Flanschabstand und Flansch-Ø
bleiben dort nachzutragen.

> Auch die Katalogwerte vor dem Bestellen gegenprüfen. Hersteller ändern Maße
> zwischen Baujahren, und ein Tippfehler in der Tabelle fällt beim Rechnen
> nicht auf.

### Nabentabelle nachtragen

Fehlt bei einer Nabe etwas, lässt es sich in der Anwendung nachtragen:
**Menü → Nabentabelle bearbeiten …**. Das Fenster zeigt den Katalog mit
denselben Spalten wie die Excel-Tabelle; jede Zelle ist anklickbar und
änderbar. Der Haken *nur ohne Flanschmaße* zeigt genau die Naben, bei denen
zum Rechnen noch etwas fehlt.

Über *Nabe hinzufügen …* lassen sich auch Naben anlegen, die in der Tabelle
ganz fehlen – Hersteller, Modell und Bauart angeben, den Rest in der Tabelle
nachtragen.

Gespeichert wird **nicht** in die Excel-Datei, sondern als Nachtrag in
`~/.config/speichenrechner/naben_ergaenzungen.json`. Damit bleibt die Tabelle
die Quelle: Erweiterst du sie und erzeugst den Katalog neu, gehen die in der
Anwendung eingetragenen Werte nicht verloren. *Als CSV sichern …* legt den
Stand als Semikolon-CSV ab, um ihn in die Tabelle zurückzuholen;
*Nachträge verwerfen* stellt den Stand der Tabelle wieder her.

Die Schreibweisen sind dieselben wie in der Tabelle – Editor und Konverter
benutzen dieselbe Auswertung aus `speichenrechner/tabelle.py`, sie können also
nicht auseinanderlaufen.

Der Katalog wird aus `daten_quelle_naben.xlsx` erzeugt:

```bash
python3 werkzeuge/katalog_erzeugen.py daten_quelle_naben.xlsx
```

Danach prüfen, ob alles richtig ankam:

```bash
python3 werkzeuge/katalog_pruefen.py daten_quelle_naben.xlsx
```

Die Prüfung vergleicht jede Zelle der Tabelle mit dem Katalog und meldet
fehlende Zeilen, nicht auswertbare Angaben und widersprüchliche Einordnungen –
etwa eine Vorderradnabe mit Ritzelaufnahme. Rückgabewert 1, wenn etwas
gefunden wurde.

Ein Blatt je Nabenart (Nabendynamo, Nabenschaltung, Vorderradnabe,
Hinterradnabe) mit den Spalten *Hersteller, Modell, Lochzahl, Einbaubreite /
OLD, Achstyp, Bremsaufnahme, Speichenloch-Ø, Flanschabstand, Flansch-Ø /
Lochkreis, Kassetten-/Freilaufkörper-Typ*.

Die Spalten werden **über ihre Überschriften** zugeordnet, nicht über feste
Positionen – eine umsortierte oder erweiterte Tabelle bricht damit nicht.
Blätter wie *Nabe mit Kassette* sind Querlisten: die dort erneut aufgeführten
Naben werden zusammengeführt, nicht doppelt aufgenommen, und das Blatt gilt
als Hinweis auf die Ritzelaufnahme, falls die Freilaufspalte schweigt. Die beiden Flanschspalten versteht der Konverter in
mehreren Schreibweisen:

| Eintrag | wird gelesen als |
|---|---|
| `47,5 (22,5/25)` | links 22,5 mm, rechts 25 mm – die Klammer gewinnt |
| `33/20` | links 33 mm, rechts 20 mm |
| `58 (symmetrisch)` | Gesamtabstand → 29 mm je Seite |
| `Ø100` | 100 mm links wie rechts |
| `59/54` | links 59 mm, rechts 54 mm |
| `k. A.`, `entfällt` | unbekannt, bleibt leer |
| `42/42 (18-24L) bzw. 38/38 (32/36L)` | mehrdeutig – wird **nicht** übernommen |

Beim Flanschabstand gilt eine einzelne Zahl als Maß über **beide** Flansche
und wird halbiert; beim Durchmesser gilt sie für beide Seiten.

### Felgentypen

Im Abschnitt **Felge** steht unter ERD und Versatz der **Felgentyp** – 17
Bauformen aus `daten_quelle_felgen.xlsx`, aufgeteilt in *Bauform*, *Material*
und *Einsatzbereich*. Die Klappliste darüber schränkt auf eine Kategorie ein,
wie beim Nabenkatalog.

Der Typ ändert die Speichenlänge **nicht**. Er ändert drei andere Dinge:

* Unter der Auswahl steht, was die Tabelle über ihn sagt – Beschreibung,
  Werkstoff, Ösung, Einsatzbereich, verfügbare Kindergrößen.
* Die Messskizze **D – ERD** zeichnet das Profil dieser Bauform: eine
  Aero-Felge ist hoch, eine Flachbettfelge flach und einwandig, eine hakenlose
  Felge endet ohne Wulsthaken, eine geöste Felge zeigt ihre Öse am Nippelsitz.
* Der Rechner sagt etwas dazu: eine einwandige Felge ohne Ösen bekommt den
  Hinweis auf Unterlegscheiben, Carbon den Verweis auf die Herstellerangabe,
  Stahl die Warnung vor zu hoher Spannung.

Für die Spannung gilt als Anhaltswert:

| Werkstoff | übliche Speichenspannung |
|---|---|
| Stahl | 500–800 N |
| Aluminium | 800–1100 N |
| Carbon | 900–1200 N |
| Titan | keine Faustregel – Einzelstücke |

Nennt ein Typ zwei Werkstoffe („Aluminium/Stahl“), begrenzt der schwächere.
Liegt die eingestellte Zielspannung außerhalb, erscheint das als Warnung.

> Diese Spannen sind Anhaltswerte für den Fall, dass nichts anderes bekannt
> ist. **Die Angabe des Felgenherstellers geht immer vor.**

Erzeugt wird die Liste wie der Nabenkatalog aus der Tabelle:

```bash
python3 werkzeuge/felgen_erzeugen.py daten_quelle_felgen.xlsx
```

Die Hinweiszeile am Ende der Tabelle ist kein Felgentyp; sie wird als Fußnote
übernommen und steht in der Anwendung unter der Auswahl. Ob alles richtig
ankam, prüft `tests/test_felgenkunde.py`: der Test liest die Tabelle noch
einmal ein und vergleicht sie Zelle für Zelle mit dem erzeugten Katalog.

### Vorlagen

Es gibt zwei Sorten mitgelieferter Nabenvorlagen, am Namen erkennbar:

* **(typisch)** – Anhaltswerte für die Bauart, keine Herstellerangaben. Nur als
  Startpunkt gedacht.
* Namentlich genannte Naben – aus den Herstellerangaben übernommen (Stand
  August 2026):

  | Vorlage | Flanschdurchmesser l/r | Flanschabstand l/r | Speichenloch |
  |---|---|---|---|
  | Rohloff SPEEDHUB 500/14 (135/142 mm) | 100 / 100 mm | 29 / 29 mm | 2,7 mm |
  | Rohloff SPEEDHUB 500/14 A12 (148 mm, asym.) | 100 / 100 mm | 32 / 26 mm | 2,7 mm |
  | SON 28 Nabendynamo (Felgenbremse, 100 mm) | 69 / 69 mm | 31 / 31 mm | 2,0 mm |
  | SON 28 Disc 6-Loch Nabendynamo | 59 / 54 mm | 22,5 / 25 mm | 2,0 mm |
  | SONdelux Nabendynamo (Felgenbremse) | 54 / 54 mm | 25 / 25 mm | 2,0 mm |
  | White Industries ENO (Schraubkranz, 135 mm) | 60 / 60 mm | 32 / 32 mm | – |
  | White Industries ENO Flip Flop (Schraubkranz) | 48 / 48 mm | 32,5 / 32,5 mm | 2,6 mm |

  Rohloff gibt Speichenlochkreis Ø 100 mm, Flanschabstand 58 mm symmetrisch
  (A12-148: 3 mm zur Scheibenbremsseite versetzt) und Speichenloch Ø 2,7 mm an;
  die SON-Werte stammen aus den Datenblättern der jeweiligen Nabe. Die beiden
  White-Industries-Naben haben ein Schraubkranzgewinde 1,375″ × 24 TPI und sind
  symmetrisch – sie tragen kein Ritzelpaket, das rechts Platz braucht. Wo der
  Hersteller den Speichenloch-Ø nicht angibt, steht „–“ und die Vorgabe 2,6 mm
  greift.

> Auch die Herstellerwerte vor dem Bestellen gegenprüfen – Maße ändern sich
> zwischen Baujahren, und der ERD der Felge muss ohnehin nachgemessen werden.

Vorlagen tragen wie Katalognaben **Bauart und Ritzelaufnahme** und stehen im
Filter unter beidem: die Rohloff-Vorlage unter *Nabenschaltung* wie unter
*Schraubritzel*. Vorher galt das nur für den Katalog, obwohl der Filter-Tooltip
es für beides versprach.

### Nachgetragene Naben

`data/naben_zusatz.json` enthält Naben, die **nicht** aus der Herstellertabelle
stammen. Eine eigene Datei, damit die Tabelle die Tabelle bleibt:
`katalog_erzeugen.py` überschreibt nur `naben_katalog.json`, `naben_zusatz.json`
bleibt liegen. Steht ein Modell in beidem, gewinnt die Tabelle.

Jede Zeile nennt ihre Herkunft, und die ist in der Auswahlliste zu sehen:

| in der Liste | Bedeutung |
|---|---|
| **nachgetragen** | Maße aus einer benannten Quelle – Herstellerseite oder Nabendatenbank |
| **ungeprüft** | Modellbezeichnung ohne belegte Maße; Flanschmaße fehlen und müssen nachgemessen werden |

Aktuell drin: eine Shimano RX100 FH-A550 (rechenfertig, Maße umgerechnet aus
einer Nabendatenbank), drei Phil-Wood-Naben mit Gewinde 1,370 × 24 tpi (je ein
Maß fehlt) und acht OEM-Schraubkranznaben von Joytech, Quando, Formula und KT
(nur Modell, Einbaubreite und Lochzahl). Prüfregeln dazu stehen in
`tests/test_katalog.py`: was „ungeprüft“ heißt, darf keine Flanschmaße tragen,
und halbe Angaben dürfen nicht als rechenfertig gelten.

Die Prüfung `katalog_pruefen.py` lässt diese Naben außen vor – sie fehlen in der
Tabelle mit Absicht.

### Werte aus fremden Datenbanken

Es gibt Nabendatenbanken mit Flanschmaßen – spokelengthcalculator.com führt
über 900 Naben. **Deren „flange offset“ ist aber ab Kontermutter gemessen, nicht
ab der Nabenmitte.** Die Seite definiert es selbst als „the distance from the
lock nut to the centre of the flange“ und rechnet `flange offset = OLD/2 − Wl`.

Solche Werte gehören in den Dialog *Flanschabstand aus Einbaubreite …*, nicht
direkt in das Feld Flanschabstand. Sonst rechnet die App still falsch:

| Nabe | dort angegeben | ab Nabenmitte |
|---|---|---|
| Hope Pro 4 Vorderrad, 100 mm | 30 / 16,99 | 20 / 33,0 |
| Hope Pro 4 Hinterrad, 135 mm | 34,5 / 48,5 | 33,0 / 19,0 |
| Shimano RX100 FH-A550, 126 mm | 25,7 / 42,3 | 37,3 / 20,7 |

Die Probe, an der die Verwechslung auffällt: ab Nabenmitte gelesen ergäbe die
Hope Pro 4 einen Flanschabstand von 83 mm in einer 135-mm-Nabe, mit der
Antriebsseite weiter außen als die Bremsseite. Beim Hinterrad muss die
Antriebsseite immer **innen** liegen. Die drei Beispiele stehen als Tests in
`tests/test_berechnung.py`.

## Handy-Version

In `public/` liegt eine Web-Fassung: eine Seite, ein Stylesheet, zwei
JavaScript-Dateien. **Kein Bauschritt, keine Abhängigkeiten, nichts von einem
fremden Server** – dieselbe Regel wie bei der PC-Anwendung. Ein Service Worker
legt die ganze Anwendung in den Cache, damit sie ohne Empfang rechnet; in der
Werkstatt ist das der Normalfall.

Zum Ansehen genügt ein Ordner-Server:

```bash
python3 -m http.server 8765 --directory public
```

Auf dem Handy läuft sie über GitHub Pages (`.github/workflows/pages.yml`
veröffentlicht `public/` bei jedem Push auf `main`). Dort dann
„Zum Startbildschirm hinzufügen“ – danach startet sie wie eine App, im
Vollbild und ohne Adresszeile.

Die Farben folgen der Geräteeinstellung über `prefers-color-scheme`, hell wie
dunkel – wie am PC das Mint-Theme.

### Dieselbe Rechnung zweimal – und wie sie zusammenbleibt

Die Formeln gibt es in Python (`speichenrechner/berechnung.py`) und in
JavaScript (`public/js/rechnen.js`). Zwei Fassungen driften auseinander, wenn
nichts sie zusammenhält. Das Band dazwischen sind gemeinsame Prüfwerte:

```bash
python3 werkzeuge/pruefwerte_erzeugen.py   # Python rechnet 14 Fälle vor
node werkzeuge/pruefwerte_js.mjs           # JavaScript muss dieselben Zahlen liefern
```

`data/pruefwerte.json` enthält Eingaben und erwartete Ergebnisse – Längen,
Speichen- und Felgenwinkel, Sehnenwinkel, Lochabstand, Spannungsverhältnis –
für symmetrische und unsymmetrische Naben, radial bis 4-fach, 2:1-Verteilung,
Felgenversatz, ein 12-Zoll-Kinderrad und den Spokomat-Abgleich. Das sind 224
Einzelwerte. Beide Fassungen müssen sie auf neun Stellen gleich treffen.

`.github/workflows/tests.yml` fährt bei jedem Push alles zusammen: die
Python-Tests, die Katalogprüfung gegen die Herstellertabelle und den Abgleich
der JavaScript-Rechnung. Die Prüfwerte werden dabei neu erzeugt und müssen
unverändert bleiben – so fällt auf, wenn jemand nur eine der beiden Seiten
anfasst.

### Was noch fehlt

Der jetzige Stand ist ein Gerüst: Eingaben, Längen, Kennwerte und die
dringendsten Hinweise. Nicht dabei sind Nabenkatalog und Felgentypen (die
JSON-Daten liegen schon bereit und lassen sich unverändert übernehmen), die
Skizzen und der Tabellen-Editor.

## Rechenweg

Nabenmitte im Ursprung, Radebene = xy-Ebene, Achse entlang z:

```
L = √(R² + r² + w² − 2·R·r·cos α) − d/2
```

| Größe | Bedeutung |
|-------|-----------|
| `R`   | ERD / 2 |
| `r`   | Flanschdurchmesser / 2 |
| `w`   | Flanschabstand ab Nabenmitte (bei asymmetrischer Felge um den Versatz korrigiert) |
| `α`   | Sehnenwinkel an der Nabe: `Kreuzungen · 720° / Speichenzahl` |
| `d`   | Speichenlochdurchmesser im Flansch |

Bei ungleicher Verteilung (2:1) zählt die Speichenzahl **einer** Flanschseite:
`α = Kreuzungen · 360° / Speichen dieser Seite`.

Der Speichenwinkel gegen die Radebene ist `arcsin(w / L_geometrisch)`. Aus dem
axialen Kräftegleichgewicht `m_l · T_l · sin(a_l) = m_r · T_r · sin(a_r)` folgt
das angezeigte Spannungsverhältnis.

### Speiche unter Spannung

Die Geometrie liefert die Länge im **gespannten** Laufrad. Ungespannt ist die
Speiche kürzer, denn unter Zug längt sie sich:

```
ΔL = F/E · Σ (lᵢ / Aᵢ)
```

Gerechnet wird abschnittsweise – verdicktes Kopfteil, verdickter unterer Teil,
dünnes Mittelteil – mit `E ≈ 180 000 N/mm²` für nichtrostenden Speichendraht.
Dazu kommen die Weitung von Flansch und Speichenbogen (rund 0,1 mm) und
optional eine Zugabe für längere Nippel. Zusammen ergibt das die Bestelllänge:

```
Bestelllänge = L − ΔL − Weitung − Nippel-Zugabe
```

Der Speichenton folgt der Saitenformel `f = 1/(2·L) · √(F/µ)` mit `µ = ρ·A`.
Er gilt für die frei schwingende Speiche; am eingespeichten Rad klingt nur der
Abschnitt zwischen letzter Kreuzung und Nippel, der ist kürzer und klingt höher.
Ein Tensiometer bleibt genauer.

### Weitere Korrekturen

| Größe | Wirkung |
|---|---|
| Unterlegscheiben unter dem Nippel | rücken den Nippelsitz nach außen → wirksamer ERD + 2 × Dicke |
| Straightpull | kein Bogen am Lochrand → kein Abzug `d/2`, keine Bogenweitung |
| Kopflage „alle innen/außen“ | verschiebt den Ansatzpunkt um ± halbe Flanschdicke |
| Nippel-Verkürzung | Herstellerangabe für längere Nippel, wird abgezogen |

Zusätzlich ausgegeben werden der **Winkel an der Felge**
`β = arcsin(r · sin α / p)` – er sagt, wie schräg die Speiche im Felgenloch
steht –, der **Lochabstand am Flansch** `π · d / m` und die **Drahtspannung**
`F / A_Mitte`.

### Abgleich mit Spokomat

Gegen ein durchgerechnetes Beispiel geprüft (siehe `tests/test_speiche.py`):

| Größe | Spokomat | Speichenrechner |
|---|---|---|
| Speichenlänge links / rechts | 263,51 / 263,28 mm | 263,51 / 263,28 mm |
| Lateraler Winkel | 7,9° / 4,84° | 7,86° / 4,81° |
| Winkel β an der Felge | 5,9° / 4,9° | 5,86° / 4,93° |
| δ = α + β | 73,4° / 72,4° | 73,4° / 72,4° |
| Spannungsanteil links | 61,27 % | 61,38 % |
| Steifigkeit Mittelteil | 1788,1 N/mm | 1787,9 N/mm |
| Längung der Enden | 0,05 mm | 0,05 mm |
| Korrigierte Länge | 262,98 / 262,45 mm | 262,96 / 262,43 mm |

Die verbleibenden 0,02 mm sind der dortige Abzug für den **Reifen-Luftdruck**:
ein aufgepumpter Reifen staucht die Felge und senkt die Speichenspannung. Das
ist bewusst nicht nachgebildet, weil der Wert von Felge und Reifen abhängt und
sich nicht allgemein angeben lässt. Die dortige Datenbank mit über 1000
Felgen- und Nabenmodellen ist ebenfalls nicht übernommen: hier stehen
stattdessen 218 Naben im [Nabenkatalog](#nabenkatalog), 17
[Felgentypen](#felgentypen) und die ERD-Vorlagen der gängigen Größen; eigene
Naben und Felgen lassen sich als Vorlage speichern.

## Aufbau

Die Funktionen liegen in getrennten, kurzen Modulen:

```
speichenrechner.py           Startskript
speichenrechner/
  modelle.py                 Datenklassen: Nabe, Felge, Einspeichung, Speichen …
  berechnung.py              Geometrie, ohne GUI-Abhängigkeit
  speiche.py                 Bauart, Dehnung, Gewicht, Speichenton
  vorlagen.py                mitgelieferte und eigene Vorlagen
  katalog.py                 Nabenmodelle vieler Hersteller
  felgenkunde.py             Felgentypen: Profil, Ösung, Werkstoff, Spannung
  tabelle.py                 Schreibweisen der Herstellertabelle auswerten
  einstellungen.py           zuletzt benutzte Werte
  bericht.py                 Ergebnis als Text
  formatierung.py            Zahlen in deutscher Schreibweise
  pfade.py                   Ablageorte nach XDG-Standard
  ui/
    anwendung.py             Gtk.Application
    hauptfenster.py          Fenster, Kopfleiste, Verdrahtung
    eingabe.py               linke Spalte (Formular)
    ergebnis.py              rechte Spalte (Anzeige)
    zeichnung.py             Zeichen-Werkzeugkasten, PNG/PDF/SVG-Export
    schema.py                Speichenbild (Aufsicht aufs Rad)
    querschnitt.py           Querschnitt durch den Nabenbereich
    vergleich.py             Tabelle über die Kreuzungszahlen
    bauteile.py              Nabe und Felgenprofil als Zeichnung
    messen.py                bemaßte Skizzen mit den echten Werten
    bauart_dialog.py         Speichenmaße und E-Modul
    tabellen_fenster.py      Nabentabelle zum Nachtragen
    vorlagen_leiste.py       Vorlagen wählen, speichern, löschen
    nabe_hilfe.py            Umrechnung ab Kontermutter
    vorlagen_dialog.py       Namensabfrage beim Speichern
    stil.py                  Theme-Anbindung, minimales CSS
    widgets.py               wiederverwendbare Bau-Helfer
daten_quelle_naben.xlsx      Herstellertabelle – Quelle des Nabenkatalogs
daten_quelle_felgen.xlsx     Felgentabelle – Quelle der Felgentypen
public/                      Handy-Version – ohne Bauschritt, ohne Fremdcode
  index.html                 eine Seite, Ergebnis oben
  css/stil.css               folgt hell/dunkel des Geräts
  js/rechnen.js              dieselben Formeln wie berechnung.py
  js/app.js                  Formular lesen, rechnen, anzeigen
  sw.js                      Service Worker: läuft ohne Netz
  manifest.json              Startbildschirm-Eintrag, Icons
werkzeuge/
  katalog_erzeugen.py        erzeugt den Nabenkatalog aus der Tabelle
  katalog_pruefen.py         vergleicht Katalog und Tabelle Zelle für Zelle
  felgen_erzeugen.py         erzeugt die Felgentypen aus der Tabelle
  pruefwerte_erzeugen.py     rechnet die Prüffälle in Python vor
  pruefwerte_js.mjs          hält die JavaScript-Rechnung darauf fest
data/
  naben_katalog.json         218 Naben von 14 Herstellern (aus der Tabelle)
  naben_zusatz.json          12 nachgetragene Naben mit Quellenangabe
  pruefwerte.json            14 Prüffälle, 224 Werte – Band zwischen PC und Handy
  felgen_katalog.json        17 Felgentypen in drei Kategorien
  speichenrechner.svg        Anwendungs-Icon
  screenshot.png             Bildschirmfoto für diese Datei
  querschnitt.png            Beispiel-Export einer Skizze
  …desktop.in                Vorlage für den Menüeintrag
tests/
  test_berechnung.py         Tests der Mathematik (laufen ohne GTK)
  test_vorlagen.py           Tests der Vorlagen und der Formatierung
  test_speiche.py            Dehnung, Gewicht, Ton und Abgleich mit Spokomat
  test_katalog.py            Katalog einlesen und durchsuchen
  test_felgenkunde.py        Felgentypen, Profile und Abgleich mit der Tabelle
```

Eigene Vorlagen und die zuletzt benutzten Werte liegen in
`~/.config/speichenrechner/`.

## Tests

```bash
python3 -m unittest discover -s tests      # PC-Anwendung
node werkzeuge/pruefwerte_js.mjs           # Handy-Rechnung gegen dieselben Werte
```

Die Tests, die GTK brauchen, überspringen sich selbst, wenn keines da ist –
so läuft dieselbe Sammlung auch auf einem Rechner ohne Oberfläche.
