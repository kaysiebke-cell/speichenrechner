"""Speichenrechner – Berechnung von Fahrrad-Speichenlängen.

Das Paket ist bewusst in kleine Module aufgeteilt:

* :mod:`speichenrechner.modelle`      – Datenklassen (Nabe, Felge, Einspeichung, …)
* :mod:`speichenrechner.berechnung`   – Geometrie, ohne GUI-Abhängigkeit
* :mod:`speichenrechner.speiche`      – Bauart, Dehnung, Gewicht und Speichenton
* :mod:`speichenrechner.vorlagen`     – mitgelieferte und eigene Vorlagen
* :mod:`speichenrechner.katalog`      – Nabenmodelle vieler Hersteller
* :mod:`speichenrechner.tabelle`      – Schreibweisen der Herstellertabelle
* :mod:`speichenrechner.einstellungen`– Speichern der zuletzt benutzten Werte
* :mod:`speichenrechner.bericht`      – Ergebnis als Text
* :mod:`speichenrechner.formatierung` – Zahlen in deutscher Schreibweise
* :mod:`speichenrechner.ui`           – GTK-Oberfläche
"""

APP_ID = "de.speichenrechner.Speichenrechner"
APP_NAME = "Speichenrechner"
VERSION = "1.5.0"

__all__ = ["APP_ID", "APP_NAME", "VERSION"]
