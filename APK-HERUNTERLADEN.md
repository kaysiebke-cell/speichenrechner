# Speichenrechner aufs Handy

**➡️ [speichenrechner.apk herunterladen](https://github.com/kaysiebke-cell/speichenrechner/releases/latest/download/speichenrechner.apk)**
(3,3 MB) — das ist der bequemste Weg: antippen, installieren, fertig. Android
fragt beim ersten Mal nach **„Aus dieser Quelle installieren"**, weil die APK mit
dem Debug-Schlüssel signiert und nicht über den Play Store verteilt ist.

Das ist der Weg. Darunter steht nur noch, was zu tun ist, wenn die
Installation hakt.

## Wenn die Installation hakt

Android blockt Installationen aus fremden Quellen zunächst. Beim Antippen der
APK erscheint „Aus Sicherheitsgründen …“; dort auf **Einstellungen** und den
Schalter für den Browser bzw. die Dateien-App umlegen. Danach nochmal antippen.

Bleibt es dabei, hilft der Weg über den Browser – da ist keine Installation
nötig:

## Ohne Installation: über das Netz

**https://kaysiebke-cell.github.io/speichenrechner/**

Seite öffnen, dann im Menü des Browsers **„Zum Startbildschirm hinzufügen"**.
Danach startet sie wie eine App – Vollbild, ohne Adresszeile – und rechnet
**auch ohne Empfang** weiter, weil sie sich beim ersten Aufruf komplett auf dem
Gerät ablegt.

## 2. Als APK aus einem Actions-Lauf

Die fertige APK hängt am [Release](https://github.com/kaysiebke-cell/speichenrechner/releases)
– das ist der einfache Weg. Wer die APK zu einem bestimmten Stand braucht,
holt sie direkt aus dem Lauf:

1. **[Actions](https://github.com/kaysiebke-cell/speichenrechner/actions/workflows/android.yml)**
   öffnen.
2. Den obersten Lauf mit grünem Haken anklicken.
3. Ganz unten unter **Artifacts** auf **`Speichenrechner-APK`** klicken – das
   lädt eine ZIP-Datei mit der APK darin.
4. ZIP entpacken, APK auf dem Handy öffnen.

Am Handy fragt Android beim ersten Mal nach der Erlaubnis
**„Aus dieser Quelle installieren"** – die APK ist mit dem Debug-Schlüssel
signiert, nicht über den Play Store verteilt.

### Feste Fassungen mit Release

Ein Tag erzeugt zusätzlich ein Release, an dem die APK direkt hängt – ohne ZIP
und ohne Anmeldung bei GitHub:

```bash
git tag v1.5.0
git push origin v1.5.0
```

Danach liegt sie unter
[Releases](https://github.com/kaysiebke-cell/speichenrechner/releases).
Der Ablauf hängt die APK als `speichenrechner.apk` an – unter genau dem Namen,
den die Download-Links oben erwarten – und die Einzeldatei gleich dazu.

**Wichtig:** Erst der Tag erzeugt eine neue APK zum Herunterladen. Ein Push
allein baut zwar eine, aber nur als Artifact unter „Actions"; der Link oben
zeigt weiter auf die Fassung des letzten Tags.

## Was die App darf

**Nichts.** Die APK verlangt keine einzige Berechtigung: kein Netz, keine
Dateien, keine Standortdaten. Der Rechner steckt vollständig in der App, und
gerechnet wird auf dem Gerät.

## Wie sie gebaut wird

Es gibt keine zweite Fassung der Web-Dateien. `app/android/app/build.gradle` kopiert
`app/public/` vor dem Bauen in die App-Assets, und `MainActivity.kt` lädt sie über
den `WebViewAssetLoader` unter einer https-Adresse – nicht über `file://`, sonst
verweigert der WebView die ES-Module.

Was in `app/public/` liegt, ist damit gleichzeitig die Browser-Fassung und der
Inhalt der App.
