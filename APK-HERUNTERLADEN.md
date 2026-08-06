# Speichenrechner aufs Handy

Zwei Wege. Der erste braucht keine Installation, der zweite gibt eine richtige
App im Menü.

## 1. Über den Browser (kein Download nötig)

**https://kaysiebke-cell.github.io/speichenrechner/**

Seite öffnen, dann im Menü des Browsers **„Zum Startbildschirm hinzufügen"**.
Danach startet sie wie eine App – Vollbild, ohne Adresszeile – und rechnet
**auch ohne Empfang** weiter, weil sie sich beim ersten Aufruf komplett auf dem
Gerät ablegt.

## 2. Als APK herunterladen

Die APK wird bei jedem Push von GitHub gebaut:

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
git tag v1.4.0
git push origin v1.4.0
```

Danach liegt sie unter
[Releases](https://github.com/kaysiebke-cell/speichenrechner/releases).

## Was die App darf

**Nichts.** Die APK verlangt keine einzige Berechtigung: kein Netz, keine
Dateien, keine Standortdaten. Der Rechner steckt vollständig in der App, und
gerechnet wird auf dem Gerät.

## Wie sie gebaut wird

Es gibt keine zweite Fassung der Web-Dateien. `android/app/build.gradle` kopiert
`public/` vor dem Bauen in die App-Assets, und `MainActivity.kt` lädt sie über
den `WebViewAssetLoader` unter einer https-Adresse – nicht über `file://`, sonst
verweigert der WebView die ES-Module.

Was in `public/` liegt, ist damit gleichzeitig die Browser-Fassung und der
Inhalt der App.
