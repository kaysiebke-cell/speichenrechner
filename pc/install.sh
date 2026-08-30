#!/usr/bin/env bash
#
# Legt Menüeintrag und Icon für den Speichenrechner an (nur für den
# aktuellen Benutzer, kein sudo nötig).
#
#   ./install.sh              Menüeintrag + Desktop-Icon anlegen
#   ./install.sh --entfernen  beides wieder entfernen
#   ./install.sh --ohne-pruefung
#                             anlegen, ohne vorher auf GTK zu prüfen. Für
#                             Rechner ohne Oberfläche – der Prüflauf legt den
#                             Eintrag probeweise an, und dort gibt es kein GTK.
#
set -euo pipefail

APP_ID="de.speichenrechner.Speichenrechner"
# Ohne GTK läuft die Anwendung nicht – deshalb wird vor dem Anlegen geprüft.
# Wer den Eintrag trotzdem will, schaltet die Prüfung ab; siehe oben.
PRUEFEN=ja
PROJEKT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Die gemeinsamen Daten (Icon, Menüvorlage) liegen neben pc/ und app/.
WURZEL="$(cd "$PROJEKT/.." && pwd)"

ANWENDUNGEN="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
ICONS="${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor/scalable/apps"
DESKTOP_DATEI="$ANWENDUNGEN/$APP_ID.desktop"
ICON_DATEI="$ICONS/$APP_ID.svg"

# Der Ordner "Schreibtisch"/"Desktop" heißt je nach Sprache anders.
schreibtisch() {
    if command -v xdg-user-dir >/dev/null 2>&1; then
        xdg-user-dir DESKTOP
    else
        echo "$HOME/Desktop"
    fi
}

entfernen() {
    rm -f "$DESKTOP_DATEI" "$ICON_DATEI"
    local tisch
    tisch="$(schreibtisch)"
    rm -f "$tisch/$APP_ID.desktop"
    aktualisieren
    echo "Speichenrechner: Menüeintrag und Icon entfernt."
}

aktualisieren() {
    command -v update-desktop-database >/dev/null 2>&1 &&
        update-desktop-database "$ANWENDUNGEN" >/dev/null 2>&1 || true
    command -v gtk-update-icon-cache >/dev/null 2>&1 &&
        gtk-update-icon-cache -f -t "${XDG_DATA_HOME:-$HOME/.local/share}/icons/hicolor" \
            >/dev/null 2>&1 || true
}

pruefe_abhaengigkeiten() {
    if ! python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk" \
        >/dev/null 2>&1; then
        echo "Fehlende Abhängigkeit: PyGObject/GTK 3." >&2
        echo "Bitte installieren mit:" >&2
        echo "  sudo apt install python3-gi gir1.2-gtk-3.0" >&2
        exit 1
    fi
}

installieren() {
    if [ "$PRUEFEN" = ja ]; then
        pruefe_abhaengigkeiten
    fi

    chmod +x "$PROJEKT/speichenrechner.py"

    mkdir -p "$ANWENDUNGEN" "$ICONS"
    install -m 644 "$PROJEKT/data/speichenrechner.svg" "$ICON_DATEI"

    # Der Pfad steht in Anführungszeichen: liegt das Projekt in einem
    # Ordner mit Leerzeichen, zerlegt der Starter die Zeile sonst dort
    # und sucht eine Datei, die es nicht gibt.
    sed -e "s|@EXEC@|python3 \"$PROJEKT/speichenrechner.py\"|" \
        -e "s|@ICON@|$APP_ID|" \
        "$PROJEKT/data/$APP_ID.desktop.in" > "$DESKTOP_DATEI"
    chmod 644 "$DESKTOP_DATEI"

    aktualisieren

    # Zusätzlich ein anklickbares Icon auf dem Schreibtisch.
    local tisch
    tisch="$(schreibtisch)"
    if [ -d "$tisch" ]; then
        install -m 755 "$DESKTOP_DATEI" "$tisch/$APP_ID.desktop"
        # Cinnamon/Nemo starten nur als vertrauenswürdig markierte Verknüpfungen.
        command -v gio >/dev/null 2>&1 &&
            gio set "$tisch/$APP_ID.desktop" metadata::trusted true >/dev/null 2>&1 || true
        echo "Icon auf dem Schreibtisch angelegt: $tisch/$APP_ID.desktop"
    fi

    echo "Speichenrechner installiert."
    echo "  Menü:    Zubehör → Speichenrechner"
    echo "  Direkt:  python3 $PROJEKT/speichenrechner.py"
}

case "${1:-}" in
    --entfernen|--uninstall|-e) entfernen ;;
    --ohne-pruefung) PRUEFEN=nein; installieren ;;
    "") installieren ;;
    *) echo "Unbekannte Option: $1" >&2; exit 2 ;;
esac
