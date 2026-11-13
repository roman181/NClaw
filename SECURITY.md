# Sicherheitsrichtlinie

## Sicherheitslücken melden

Bitte veröffentliche keine Details zu einer vermuteten Sicherheitslücke in einem öffentlichen Issue. Nutze die private Meldemöglichkeit unter **Security → Advisories** im GitHub-Repository.

## Sicherheitsgrundsätze

- Geheimnisse gehören ausschließlich in eine lokale `.env`-Datei und niemals in Git.
- Unbekannte Dateien und externe Inhalte werden als nicht vertrauenswürdig behandelt.
- Dateioperationen müssen auf freigegebene Arbeitsverzeichnisse begrenzt werden.
- Shell-Befehle, Netzwerkzugriffe, Veröffentlichungen und destruktive Aktionen benötigen eine explizite Freigabe.
- Skills und Agenten-Erweiterungen werden vor Aktivierung geprüft und getestet.

## Unterstützte Version

Sicherheitskorrekturen werden für den aktuellen Entwicklungsstand auf dem Branch `main` bereitgestellt.
