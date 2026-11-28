# Nexus-Handoffs: Validierung

Lokale TokenGuard-Handoffs verwenden Schema-Version 1. `HandoffStore.load(handoff_id)` liest einen Datensatz ausschließlich anhand seiner UUID-Hex-ID und validiert ihn, ohne eine Aufgabe fortzusetzen oder einen Agenten zu starten.

- Unbekannte Schema-Versionen und zusätzliche oder fehlende Felder werden abgewiesen.
- Doppelte JSON-Schlüssel, ungültige UTF-8-Daten und beschädigtes JSON werden abgewiesen.
- Dateien müssen reguläre Dateien sein und dürfen 64 KiB nicht überschreiten.
- Symlink-Dateien werden mit `O_NOFOLLOW` (sofern verfügbar) abgewiesen.
- Pflichtfelder, Typen, Tokenmetriken, Status und Notizen werden geprüft.
- `created_at` muss eine ISO-8601-Zeitzonenangabe enthalten; naive lokale Zeitstempel werden abgewiesen, damit Zeitpunkte auf Android/Termux und Linux eindeutig bleiben.
- Handoffs bleiben lokal; es gibt keine Modellumschaltung oder automatische Wiederaufnahme.

Das Schema ist bewusst strikt: Eine zukünftige inkompatible Änderung benötigt eine neue Schema-Version und eine explizite Migration. Laden ist nur eine lesende Validierung und ersetzt keine Nutzerfreigabe zur Fortsetzung.
