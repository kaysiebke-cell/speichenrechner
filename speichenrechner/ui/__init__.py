"""GTK-Oberfläche des Speichenrechners.

Die Oberfläche ist in kleine, eigenständige Bausteine zerlegt:

* :mod:`~speichenrechner.ui.widgets`     – wiederverwendbare Bau-Helfer
* :mod:`~speichenrechner.ui.stil`        – Theme-Anbindung und wenig CSS
* :mod:`~speichenrechner.ui.zeichnung`   – Zeichen-Werkzeugkasten und Export
* :mod:`~speichenrechner.ui.eingabe`     – linke Spalte mit allen Eingaben
* :mod:`~speichenrechner.ui.ergebnis`    – rechte Spalte mit den Ergebnissen
* :mod:`~speichenrechner.ui.schema`      – Speichenbild (Aufsicht aufs Rad)
* :mod:`~speichenrechner.ui.querschnitt` – Querschnitt durch den Nabenbereich
* :mod:`~speichenrechner.ui.vergleich`   – Tabelle über die Kreuzungszahlen
* :mod:`~speichenrechner.ui.bauteile`    – Nabe und Felgenprofil als Zeichnung
* :mod:`~speichenrechner.ui.messen`      – bemaßte Skizzen mit den echten Werten
* :mod:`~speichenrechner.ui.bauart_dialog` – Speichenmaße und E-Modul
* :mod:`~speichenrechner.ui.tabellen_fenster` – Nabentabelle zum Nachtragen
* :mod:`~speichenrechner.ui.vorlagen_leiste` – Vorlagen wählen, speichern, löschen
* :mod:`~speichenrechner.ui.vorlagen_dialog` – Namensabfrage beim Speichern
* :mod:`~speichenrechner.ui.nabe_hilfe`  – Umrechnung ab Kontermutter
* :mod:`~speichenrechner.ui.hauptfenster`– setzt die Bausteine zusammen
* :mod:`~speichenrechner.ui.anwendung`   – Gtk.Application samt Menü
"""
