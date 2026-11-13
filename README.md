# 🧠 NClaw – Autonomous AI Agent Framework

[![CI](https://github.com/roman181/NClaw/actions/workflows/ci.yml/badge.svg)](https://github.com/roman181/NClaw/actions/workflows/ci.yml)
[![Security](https://github.com/roman181/NClaw/actions/workflows/security.yml/badge.svg)](https://github.com/roman181/NClaw/actions/workflows/security.yml)
[![Termux](https://github.com/roman181/NClaw/actions/workflows/termux.yml/badge.svg)](https://github.com/roman181/NClaw/actions/workflows/termux.yml)
[![Links](https://github.com/roman181/NClaw/actions/workflows/links.yml/badge.svg)](https://github.com/roman181/NClaw/actions/workflows/links.yml)
![Status](https://img.shields.io/badge/status-active%20development-orange)
![Architecture](https://img.shields.io/badge/architecture-modular-blue)
![Local First](https://img.shields.io/badge/local--first-yes-green)
![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Linux-lightgrey)
![License](https://img.shields.io/badge/license-Apache--2.0-blue)

NClaw ist ein autonomes, local-first KI-Agenten-Framework, das aus einem einfachen Chat einen proaktiven digitalen Mitarbeiter macht.

NClaw verbindet lokale KI-Modelle, autonome Agenten, Skills, eine lokale Wissensbibliothek und kontrollierte Systemwerkzeuge zu einem modularen AI Office.

Die Steuerung erfolgt über eine zentrale Benutzeroberfläche und optional über Telegram.

«Projektstatus: Frühes Entwicklungsstadium. Nexus-Core, Telegram-Freigaben, eine lokale Sandmann-Sandbox und ein optionaler Google-Drive-Adapter sind implementiert. Die Drive-Anmeldung und Synchronisierung benötigen noch die Einrichtung eigener Google-OAuth-Zugangsdaten.»

---

📑 Inhaltsverzeichnis

- "1. Vision" (#-1-vision)
- "2. Kernprinzipien" (#-2-kernprinzipien)
- "3. Systemarchitektur" (#-3-systemarchitektur)
- "4. Agententeam" (#-4-agententeam)
- "5. Hauptfunktionen" (#-5-hauptfunktionen)
- "6. Skill-Evolution" (#-6-skill-evolution)
- "7. Llama-Einzelmodell" (#-7-llama-einzelmodell)
- "8. TokenGuard" (#-8-tokenguard)
- "9. Sicherheit" (#-9-sicherheit)
- "10. Voraussetzungen" (#-10-voraussetzungen)
- "11. Installation" (#-11-installation)
- "12. Konfiguration" (#-12-konfiguration)
- "13. Projektstruktur" (#-13-projektstruktur)
- "14. GitHub Actions" (#-14-github-actions)
- "15. Roadmap" (#-15-roadmap)
- "16. Lernquellen" (#-16-lernquellen)
- "17. Mitmachen" (#-17-mitmachen)
- "18. Lizenz" (#-18-lizenz)

---

🧠 1. Vision

NClaw soll ein digitales KI-Büro werden, das eigenständig Aufgaben übernimmt, Projekte organisiert, Informationen analysiert und seine Fähigkeiten kontinuierlich erweitert.

Anstatt nur auf Fragen zu antworten, soll NClaw:

- Aufgaben selbstständig planen.
- Dateien analysieren und organisieren.
- GitHub-Repositories untersuchen.
- Neue Skills erstellen und verbessern.
- Lokale KI-Modelle koordinieren.
- Fehler erkennen und melden.
- Langfristig aus freigegebenen Erfahrungen lernen.
- Aufgaben im Hintergrund überwachen.
- Über Telegram mit dem Nutzer kommunizieren.

Das Ziel: Ein persönlicher digitaler Mitarbeiter, der lokal auf eigener Hardware arbeitet und unter deiner Kontrolle bleibt.

---

⚙️ 2. Kernprinzipien

Prinzip| Beschreibung
Local-first| Lokale KI-Modelle als Standard
Autonom| Selbstständige Planung und Ausführung
Kontrolliert| Kritische Aktionen benötigen Freigabe
Modular| Agenten und Skills sind austauschbar
Transparent| Entscheidungen und Aktionen werden protokolliert
Lernfähig| Skills können verbessert und erweitert werden
Privat| Persönliche Daten bleiben lokal

Cloud-Modelle sind optional und werden nur nach ausdrücklicher Freigabe verwendet.

---

🏗️ 3. Systemarchitektur

flowchart TD
    U["👤 Nutzer"] <--> T["Telegram-Agent"]
    U <--> UI["NClaw Dashboard"]

    T <--> N["🧠 NEXUS<br/>Zentraler Koordinator"]
    UI <--> N

    N <--> S["📂 Sandmann"]
    N <--> A["Llama via Ollama"]

    A --> X["Antwortprüfung durch Llama"]

    S --> SB["Sandbox-Ai"]
    SB --> L["Lokale Bibliothek"]

    L --> ST["Skill-Baum<br/>Three.js"]

    N <--> TG["TokenGuard"]
    N <--> LP["Lernschleife"]

    LP --> ST
    ST --> N

Komponenten

- Nexus: Zentrale Steuerung und Aufgabenverteilung.
- Telegram-Agent: Kommunikation und Freigaben.
- Sandmann: Dateiverarbeitung und Bibliotheksverwaltung.
- Llama: Einziges lokales KI-Modell für Analyse und Antworten.
- TokenGuard: Kontextüberwachung und JSON-Übergabe.
- Skill-Baum: Visualisierung der Fähigkeiten.
- Sandbox-Ai: Isolierte Prüfung unbekannter Daten und Skills.

---

🤖 4. Agententeam

🧠 Nexus – Der Chef

Nexus ist das zentrale Gehirn des gesamten Systems.

Aufgaben:

- Aufgaben analysieren.
- Arbeit an Agenten verteilen.
- Modelle auswählen.
- Ergebnisse vergleichen.
- Entscheidungen koordinieren.
- Projektstatus verwalten.
- Nutzerfreigaben einholen.

📱 Telegram-Agent – Die Kommunikation

Aufgaben:

- Nachrichten empfangen und beantworten.
- Aufgaben an Nexus weitergeben.
- Freigaben einholen.
- Fehler melden.
- Fortschritte zusammenfassen.
- Zwei-Satz-Berichte liefern.

📂 Sandmann – Die Bibliothek

Aufgaben:

- Ordner "Sandbox-Ai" verwalten.
- ZIP-Dateien untersuchen.
- PDFs und Dokumente analysieren.
- GitHub-Repositories prüfen.
- Dateien sortieren.
- Duplikate erkennen.
- Skills extrahieren.
- Neue Inhalte in der Bibliothek organisieren.

🚀 Zukünftige Agenten

Das System soll mit der Zeit weitere Spezialisten erhalten.

Jeder Agent bekommt:

- Eigenes Profil.
- Eigenen Charakter-Prompt.
- Eigene Aufgaben.
- Zugewiesenes Modell.
- Definierte Berechtigungen.
- Eigenes Langzeitgedächtnis.

---

🔥 5. Hauptfunktionen

📂 Sandbox und Bibliothek

Die Sandbox ist der Eingang für neue Informationen.

Geplant:

- Dateien lokal auf dem Android-Gerät oder Linux-System aufnehmen.
- ZIP-Archive sicher auflisten (kein automatisches Entpacken).
- PDFs auslesen (pypdf).
- Text- und Quellcodedateien als Daten untersuchen, niemals ausführen.
- Unbekannte Dateitypen in quarantine ablegen.
- Importgrößen, ZIP-Einträge und entpackte Größen begrenzen.
- Dateien nach manueller Prüfung in approved verschieben.
- Google Drive als optionales Backup-Ziel für freigegebene Dateien verwenden.

Verzeichnis:

~/.nclaw/ (lokaler Gerätespeicher; per NCLAW_DATA_DIR änderbar)
├── incoming/
├── processing/
├── approved/
├── rejected/
├── quarantine/
├── library/
└── metadata/

Unbekannter Code wird niemals ungeprüft ausgeführt.

🌳 Skill-Baum

Der Skill-Baum ist das langfristige Wissens- und Fähigkeiten-System.

Geplant:

- 3D-Darstellung mit Three.js.
- Jeder Skill ist ein eigener Knoten.
- Verbindungen zeigen Abhängigkeiten.
- Ähnliche Skills können verglichen werden.
- Verbesserungen erzeugen neue Skill-Versionen.
- Alte Versionen bleiben nachvollziehbar.
- Nutzer können Skills freigeben oder ablehnen.

🔄 Lernschleife

Die Lernschleife kann über das Dashboard gestartet und gestoppt werden.

Funktionen:

- Öffentliche Open-Source-Projekte untersuchen.
- Dokumentationen analysieren.
- Neue Fähigkeiten identifizieren.
- Skills erstellen.
- Skills testen.
- Bestehende Fähigkeiten verbessern.
- Ergebnisse zur Freigabe vorlegen.

Wichtig: Lernen bedeutet nicht unkontrollierte Selbstveränderung. Neue Fähigkeiten werden zunächst isoliert getestet und erst nach Freigabe aktiviert.

---

⚔️ 6. Skill-Evolution

Skills sollen sich langfristig weiterentwickeln können.

Geplanter Ablauf:

flowchart TD
    A["Neue Information"] --> B["Sandmann analysiert"]
    B --> C["Sandbox-Prüfung"]
    C --> D["Skill extrahieren"]
    D --> E["Skill testen"]
    E --> F{"Test erfolgreich?"}
    F -->|Nein| G["Verwerfen oder überarbeiten"]
    F -->|Ja| H["Neue Skill-Version"]
    H --> I["Nutzerfreigabe"]
    I --> J["Bibliothek aktualisieren"]
    J --> K["Skill-Baum erweitern"]

Jeder Skill erhält eine eindeutige ID und eine Versionshistorie.

**Implementierte Basis:** `skills/registry.py` speichert Skill-Beschreibungen und Anweisungen als lokale JSON-Metadaten unter `~/.nclaw/library/skills/`. Neue Versionen beginnen immer mit `pending_approval`. Sie werden erst nach einem dokumentierten erfolgreichen Test und einer ausdrücklichen Freigabe als aktiv gelistet. Bereits vorhandene Versionen können nicht überschrieben werden. Skill-Anweisungen bleiben Text und werden nicht als Python- oder Shell-Code ausgeführt.

Beispiel:

{
  "skill_id": "github-analyzer",
  "name": "GitHub Repository Analyzer",
  "version": "1.0.0",
  "status": "pending_approval",
  "source": "public_repository",
  "tests_passed": true
}

---

🧩 7. Llama-Einzelmodell

NClaw nutzt ausschließlich ein lokales Llama-Modell über Ollama.

Komponente | Aufgabe
Llama | Analyse, Planung, Antwort und Selbstprüfung
Nexus | Koordination und Entscheidung

Ablauf

1. Nexus erstellt eine Aufgabe.
2. Llama bearbeitet die Aufgabe.
3. Llama prüft die Antwort anhand der Aufgabenanforderungen.
4. Nexus kontrolliert den Ablauf und gibt das Ergebnis aus.

Es wird kein zweites KI-Modell und kein externer KI-Dienst automatisch aufgerufen.

---

🛡️ 8. TokenGuard

TokenGuard prüft vor jedem Nexus-Einzelaufruf die ungefähre Größe von Systemanweisung und Prompt.

Implementiert:

- Konfigurierbares Kontextfenster über `NCLAW_CONTEXT_WINDOW` (Standard: 8192).
- Auslöseschwelle über `NCLAW_TOKEN_THRESHOLD` (Standard: 0.90).
- Konservative Token-Schätzung aus UTF-8-Bytes und Textelementen.
- Bei Erreichen von 90 % wird der Llama-Aufruf gestoppt und ein JSON-Handoff lokal gespeichert.
- Handoffs liegen privat unter `~/.nclaw/metadata/handoffs/` und enthalten Aufgabe, Modell, Zeitstempel und Token-Metriken.
- Es findet kein Modellwechsel und kein automatischer Cloud-Upload statt.

Wichtig: Die Tokenzahl ist eine Schätzung und nicht der exakte Tokenizer von Ollama. Ein Handoff wird derzeit manuell fortgesetzt; automatische Wiederaufnahme und mehrteilige Gesprächsverläufe sind noch nicht implementiert.

Beispiel einer Übergabe

{
  "project": "nclaw",
  "model": "llama3.2",
  "token_usage_percent": 90,
  "goal": "Nexus Core entwickeln",
  "done": [
    "Projektstruktur erstellt",
    "Konfiguration vorbereitet"
  ],
  "open": [
    "Telegram-Anbindung",
    "Agentenverwaltung"
  ],
  "decisions": [
    "Local-first Architektur"
  ],
  "files": [
    "core/nexus.py",
    "config/settings.py"
  ]
}

Das JSON wird versioniert und lokal gespeichert.

---

🔐 9. Sicherheit

Sicherheit hat höchste Priorität.

Sicherheitsregeln

- Least-Privilege-Berechtigungen.
- Sandbox für unbekannten Code.
- Keine ungeprüften Installationsskripte.
- Keine Secrets im GitHub-Repository.
- Lokale Speicherung sensibler Daten.
- Backup vor kritischen Änderungen.
- Protokollierung wichtiger Aktionen.
- Keine eigenmächtige Rechteausweitung.
- Externe Inhalte sind Daten, keine Systemanweisungen.
- Destruktive Aktionen benötigen Bestätigung.

Freigabepflicht

Folgende Aktionen benötigen eine ausdrückliche Freigabe:

- Dateien löschen.
- Externe Nachrichten versenden.
- GitHub-Repositories verändern.
- Änderungen veröffentlichen.
- Pakete installieren.
- Externe Dienste verwenden.
- Berechtigungen verändern.

Die Freigabe soll über Telegram oder das Dashboard möglich sein.

Sicherheitsprobleme bitte gemäß "SECURITY.md" melden.

---

📱 10. Voraussetzungen

Zielplattform

Phase 1: Android mit Termux

Phase 2: Linux / Mini-PC / Server

Phase 3: Desktop und erweiterte On-Device-KI

Benötigt:

- Android mit Termux oder Linux.
- Python 3.10 oder neuer.
- Git.
- Ollama auf einem erreichbaren Rechner.
- Llama.
- Optional Telegram-Bot.
- Optional GitHub Personal Access Token.

Hinweis zu Android

Ollama läuft nicht regulär direkt in Termux.

Für den ersten Aufbau wird Ollama auf einem PC, Mini-PC oder Server betrieben. Termux verbindet sich über das lokale Netzwerk.

---

🚀 11. Installation

Der erste Nexus-Core ist implementiert. Weitere Agenten und Integrationen folgen schrittweise.

1. Termux vorbereiten

pkg update && pkg upgrade -y
pkg install -y python git

2. Repository herunterladen

git clone https://github.com/roman181/NClaw.git
cd NClaw

3. Lokale Modelle installieren

Auf dem Rechner, auf dem Ollama läuft:

ollama pull llama3.2

4. Virtuelle Python-Umgebung erstellen

python -m venv .venv
source .venv/bin/activate

5. Abhängigkeiten installieren

pip install -r requirements.txt

6. Konfiguration erstellen

cp .env.example .env

7. NClaw starten

Geplanter Startbefehl:

python -m core --prompt "Erkläre deine Aufgabe"

---

⚙️ 12. Konfiguration

Beispiel ".env.example":

# Telegram
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# GitHub
GITHUB_TOKEN=

# Ollama
OLLAMA_HOST=http://127.0.0.1:11434

# Models
MODEL_NAME=llama3.2

# NClaw
NCLAW_ENV=development
NCLAW_LOG_LEVEL=INFO
NCLAW_WORKSPACE=workspace
NCLAW_DATA_DIR=~/.nclaw
GOOGLE_DRIVE_CREDENTIALS=~/.nclaw/google-oauth-client.json
GOOGLE_DRIVE_TOKEN=~/.nclaw/google-drive-token.json

Wenn Ollama auf einem anderen Rechner läuft:

OLLAMA_HOST=http://192.168.1.50:11434

Die IP-Adresse muss durch die tatsächliche LAN-Adresse ersetzt werden.

Niemals die echte ".env"-Datei auf GitHub hochladen.


### Telegram-Agent starten

1. Erstelle über den offiziellen BotFather einen Telegram-Bot und kopiere dessen Bot-Token.
2. Ermittle deine numerische Telegram-Chat-ID über einen vertrauenswürdigen Weg.
3. Trage beide Werte ausschließlich in die lokale `.env`-Datei ein:

```env
TELEGRAM_BOT_TOKEN=dein_bot_token
TELEGRAM_CHAT_ID=deine_numerische_chat_id
```

4. Starte den Agenten:

```bash
python -m agents.telegram.bot
```

Verfügbare Telegram-Befehle: `/help`, `/status` und `/ask Deine Frage`.
Der Bot akzeptiert ausschließlich Nachrichten von der konfigurierten Chat-ID und führt keine Shell-Befehle aus.

**Freigegebene Dateierstellung:** Mit `/propose_file PFAD | INHALT` kann eine neue Textdatei vorgeschlagen werden. Der Bot zeigt Pfad und vollständigen Inhalt zur Prüfung an. Erst `/approve ID` genehmigt den exakt gebundenen Vorschlag; erst ein separater `/execute ID`-Befehl legt die Datei an. `/deny ID` lehnt ab und `/pending` zeigt offene Freigaben. Die Datei wird ausschließlich im konfigurierten `NCLAW_WORKSPACE` (Standard: `workspace/`) angelegt. Vorhandene Dateien, `.env`-Dateien, `.git` und Pfad-Ausbrüche sind gesperrt; Elternordner müssen bereits existieren. Dateien werden mit restriktiven Rechten angelegt. Freigaben und Dateivorschläge verfallen nach 10 Minuten, gelten einmal und gehen beim Neustart verloren. Allgemeine `/request`-Anfragen bleiben reine Freigabe-Einträge und führen keine Aktion aus.

Für den Betrieb muss der Rechner mit Ollama erreichbar sein. Beende den Polling-Prozess mit Ctrl+C.

### Lokale Gerätesandbox und Sandmann

Der Standardspeicher liegt unter `~/.nclaw/` im privaten Termux-App-Speicher. Er ist nicht öffentlich über andere Android-Apps sichtbar. Die Sandbox wird automatisch mit den Ordnern `incoming`, `processing`, `approved`, `rejected`, `quarantine`, `library` und `metadata` angelegt.

Für Zugriff auf Downloads und andere Android-Dateien:

```bash
termux-setup-storage
```

Danach kann in der lokalen `.env` z. B. folgender Speicherort gesetzt werden:

```env
NCLAW_DATA_DIR=~/storage/shared/Documents/NClaw
```

Sandmann-Befehle:

```bash
# Datei sicher in incoming oder quarantine kopieren
python -m agents.sandmann import ~/storage/shared/Download/datei.zip

# Importierte Datei analysieren (Pfad aus der Import-Ausgabe verwenden)
python -m agents.sandmann inspect ~/.nclaw/incoming/DATEI

# Nach eigener Prüfung bewusst in approved verschieben
python -m agents.sandmann approve ~/.nclaw/incoming/DATEI
```

ZIP-Dateien werden nur auf Einträge und Sicherheitsmerkmale geprüft, nicht entpackt. Unbekannte Formate werden quarantänisiert. Quellcode wird als Text betrachtet und nicht ausgeführt.

### Google Drive als optionaler Cloud-Speicher

Die Google-Drive-Anbindung verwendet NClaws eigene OAuth-Anmeldung. Sie ist unabhängig von einer ChatGPT-Drive-Verbindung. Nur Dateien aus `approved/` können hochgeladen werden; es gibt keine automatische Synchronisierung und keinen Upload von `incoming/` oder `quarantine/`.

1. In der [Google Cloud Console](https://console.cloud.google.com/) ein Projekt auswählen oder erstellen.
2. Die **Google Drive API** aktivieren.
3. Einen OAuth-Client vom Typ **Desktop-App** erstellen und die heruntergeladene JSON-Datei lokal ablegen:
   `~/.nclaw/google-oauth-client.json`
4. Bei einer OAuth-Test-App das eigene Google-Konto als Testnutzer eintragen.
5. Diese lokalen Einstellungen in `.env` setzen:

```env
GOOGLE_DRIVE_CREDENTIALS=~/.nclaw/google-oauth-client.json
GOOGLE_DRIVE_TOKEN=~/.nclaw/google-drive-token.json
```

6. Eine zuvor geprüfte Datei nach `approved/` verschieben und den Upload ausdrücklich starten:

```bash
# Eine einzelne Datei sichern (nur aus ~/.nclaw/approved/)
python -m cloud.google_drive upload --file ~/.nclaw/approved/DATEI

# Bereits von NClaw erstellte Backups anzeigen
python -m cloud.google_drive list

# Ein Backup anhand seiner Drive-ID wiederherstellen
python -m cloud.google_drive restore --id DRIVE_DATEI_ID
```

Beim ersten Start zeigt NClaw eine Google-Anmeldeseite an. Den Link im Android-Browser öffnen und den Zugriff bestätigen. Der OAuth-Token bleibt lokal und wird mit restriktiven Dateirechten gespeichert. Der angeforderte Scope ist `drive.file`; NClaw erhält damit keinen pauschalen Zugriff auf dein gesamtes Drive.

**Wiederherstellung:** NClaw akzeptiert nur Dateien im eigenen Backup-Ordner mit passenden NClaw-Metadaten. Vor dem Speichern werden Dateigröße und SHA-256 geprüft. Die Datei landet ausschließlich in `quarantine/` und wird dort nicht entpackt oder ausgeführt. Nach der manuellen Prüfung kannst du sie mit Sandmann untersuchen und bei Bedarf bewusst freigeben. Ein Restore überschreibt keine vorhandenen Dateien.

**Wichtig:** OAuth-Clientdatei und Token niemals in GitHub hochladen oder in Chats teilen. Upload und Restore werden nur durch einen ausdrücklich gestarteten CLI-Befehl ausgeführt; es gibt keinen Hintergrund-Sync.

---

📁 13. Projektstruktur

Geplante Repository-Struktur:

nclaw/
│
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   ├── security.yml
│   │   ├── links.yml
│   │   ├── termux.yml
│   │   └── release.yml
│   │
│   ├── ISSUE_TEMPLATE/
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
│
├── agents/
│   ├── telegram/
│   │   ├── __init__.py
│   │   └── bot.py
│   └── sandmann/
│       ├── __init__.py
│       ├── __main__.py
│       └── agent.py
│
├── sandbox/
│   ├── __init__.py
│   └── storage.py
│
├── cloud/
│   ├── __init__.py
│   └── google_drive.py
│
├── core/
│   ├── __init__.py
│   ├── nexus.py
│   ├── orchestrator.py
│   ├── approval_manager.py
│   └── approved_actions.py
│
├── agents/
│   ├── nexus/
│   ├── telegram/
│   └── sandmann/
│
├── models/
│   ├── __init__.py
│   ├── ollama.py
│   ├── llama.py
│   └── cloud_adapter.py
│
├── skills/
│   ├── registry.py
│   ├── manager.py
│   └── definitions/
│
├── tools/
│   ├── filesystem.py
│   ├── github.py
│   └── system.py
│
├── memory/
│   ├── storage.py
│   └── history/
│
├── sandbox/
│   ├── validator.py
│   ├── executor.py
│   └── quarantine/
│
├── tokenguard/
│   ├── monitor.py
│   └── handoff.py
│
├── library/
│
├── ui/
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── skill-tree/
│
├── config/
│   └── settings.py
│
├── tests/
│   ├── test_core.py
│   ├── test_telegram.py
│   ├── test_sandmann.py
│   └── test_google_drive.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── SECURITY.md
├── LICENSE
└── README.md

---

🔄 14. GitHub Actions

Geplante automatische Workflows:

Workflow| Funktion
"ci.yml"| Python-Linting und Tests
"security.yml"| Sicherheitsprüfungen und Secret-Scanning
"links.yml"| Markdown-Linkprüfung
"termux.yml"| Android-/Termux-Kompatibilitätschecks
"release.yml"| Automatische GitHub-Releases

CI

- Python 3.10 und 3.12 testen.
- Ruff für Codequalität.
- Pytest für automatisierte Tests.

Security

- Gitleaks für Secrets.
- CodeQL, soweit unterstützt.
- Dependency Review.
- Abhängigkeitsprüfungen.

Releases

Neue Versionen werden ausschließlich über Git-Tags im Format `v*` veröffentlicht. Der Release-Workflow startet nicht manuell, damit kein Release ohne gültigen Tag angelegt wird.

Beispiel:

git tag v0.1.0
git push origin v0.1.0

---

🗺️ 15. Roadmap

Phase 1 – Grundsystem

- [ ] Nexus Core
- [ ] Python-Projektstruktur
- [ ] Konfigurationssystem
- [ ] Lokale Speicherung
- [x] Ollama-Anbindung (Basis)
- [x] Llama-Integration (einziges Modell)

Phase 2 – Agenten

- [x] Telegram-Agent (sichere Basis: Allowlist, /ask, /status, /help)
- [x] Sandmann-Agent (sichere Dateiannahme und Analyse)
- [ ] Agentenverwaltung
- [x] Telegram-Freigabe-Basis (Ablaufzeit, Einmalfreigabe, Aktionsbindung)
- [x] Erste kontrollierte Aktion: neue Textdatei im Workspace nach separater Freigabe und Ausführungsbefehl
- [ ] Aufgabenverwaltung

Phase 3 – Bibliothek

- [x] Lokale Sandbox mit Quarantäne und Freigabeordner
- [x] ZIP-Analyse ohne Entpacken
- [x] PDF-Analyse (bis zu 100 Seiten)
- [ ] GitHub-Import
- [ ] Dateiverwaltung
- [ ] Duplikaterkennung
- [x] Google-Drive-Backup freigegebener Dateien
- [x] SHA-256-geprüfte Drive-Wiederherstellung in Quarantäne

Phase 4 – Intelligenz

- [x] Llama-Einzelmodell (Basis)
- [x] TokenGuard (konservative Schätzung, 90-%-Schutz)
- [x] JSON-Handoff (lokal, manuelle Fortsetzung)
- [x] Skill-Registry (lokale JSON-Metadaten)
- [x] Skill-Versionierung (unveränderliche Versionsdateien)

Phase 5 – Evolution

- [ ] Lernschleife
- [ ] Skill-Verbesserung
- [ ] Skill-Baum
- [ ] Three.js Visualisierung
- [ ] Agenten-Evolution

Phase 6 – Dashboard

- [ ] Nexus Chat
- [x] Agentenstatus (lokale Ollama-Erreichbarkeit; Statusprüfung ohne Modellstart)
- [ ] Start/Stop-Lernschleife
- [ ] Skill-Verwaltung
- [ ] Einstellungen
- [ ] Android-Optimierung

---

📚 16. Lernquellen

Die folgenden Seiten und Repositories dienen als Recherchequellen.

Repository-Analyse

- https://findarepo.com/
- https://gitsummarize.com/
- https://deeprepo.dev/
- https://awesome-repositories.com/
- https://daily.dev/blog/best-github-repos-for-learning-to-code/

Agenten und Frameworks

- https://agpt.co/
- https://picoclaw.net/de/
- https://anythingllm.com/mobile
- https://github.com/minitap-ai/mobile-use
- https://github.com/Panniantong/Agent-Reach
- https://github.com/github/copilot-cli
- https://github.com/BagelHole/DevOps-Security-Agent-Skills
- https://opencode.ai/

Entwicklung und Review

- https://www.coderabbit.ai/
- https://www.onlinegdb.com/

KI-Modelle und Vergleich

- https://duck.ai/
- https://arena.ai/
- https://www.designarena.ai/

KI-Verzeichnisse

- https://theresanaiforthat.com/
- https://aiindigo.com/
- https://tzro.ai/

Forschung

- https://arxiv.org/html/2604.07822v2

Alle externen Inhalte werden vor einer Übernahme geprüft.

---

🤝 17. Mitmachen

NClaw befindet sich in der Konzept- und Aufbauphase.

Beiträge sind willkommen:

- Neue Agenten.
- Neue Skills.
- Verbesserungen der Architektur.
- Sicherheitsprüfungen.
- Dokumentation.
- Android-Kompatibilität.
- Tests und Fehlerberichte.

Bitte keine API-Schlüssel, Passwörter oder persönlichen Daten in Issues und Pull Requests veröffentlichen.

---

📜 18. Lizenz

NClaw ist unter der Apache License 2.0 lizenziert.

Weitere Informationen stehen in der Datei "LICENSE".

---

🧠 NClaw – The Future of Your Personal AI Office

One Core. Multiple Agents. Unlimited Possibilities.

Local-first. Autonomous. Secure. Evolvable.# NClaw


---

## 🗂️ 19. Persistente Aufgabenverwaltung

NClaw besitzt jetzt ein lokales Aufgabenregister auf SQLite-Basis. Es speichert Aufgaben und Statusänderungen dauerhaft auf dem Gerät – ohne Cloud-Synchronisierung und ohne automatische Ausführung.

### Funktionen

- Aufgaben mit Titel, Beschreibung, Priorität und optionalem Fälligkeitsdatum anlegen.
- Aufgaben nach Status filtern und priorisiert anzeigen.
- Statuswechsel mit festgelegten Übergangsregeln.
- Ereignisverlauf je Aufgabe mit Zeitstempel und Notiz.
- Persistente Speicherung in `~/.nclaw/tasks.sqlite3` (alternativ unter `NCLAW_DATA_DIR`).
- Datenbankdatei mit restriktiven Dateirechten; keine Shell- oder Netzwerk-Ausführung.

### Statusmodell

| Status | Bedeutung |
|---|---|
| `queued` | Neu angelegt und wartet |
| `in_progress` | In Bearbeitung |
| `blocked` | Wartet auf eine Voraussetzung |
| `completed` | Erfolgreich abgeschlossen |
| `failed` | Fehlgeschlagen; kann erneut eingeplant werden |
| `cancelled` | Abgebrochen |

Abgeschlossene und abgebrochene Aufgaben sind Endzustände. Ungültige Statuswechsel werden abgewiesen.

### Verwendung in Termux oder Linux

```bash
# Aufgabe anlegen (Priorität 1 = höchste, 5 = niedrigste)
python -m tasks add "Nexus Dashboard bauen" --priority 1 \
  --description "Read-only Statusübersicht vorbereiten"

# Aufgaben anzeigen
python -m tasks list
python -m tasks list --status queued

# Aufgabe anzeigen und Verlauf prüfen
python -m tasks show TASK_ID

# Status kontrolliert ändern
python -m tasks move TASK_ID in_progress --note "Arbeit begonnen"
python -m tasks move TASK_ID completed --note "Tests erfolgreich"
```

Die Aufgabenverwaltung ist zunächst ein Planungs- und Nachverfolgungssystem. Sie startet keine Agenten, führt keine Befehle aus und veröffentlicht keine Änderungen. Solche Aktionen bleiben separat freigabepflichtig.

### Neue Dateien

```text
tasks/
├── __init__.py
├── __main__.py
└── store.py

tests/
└── test_tasks.py
```

### Roadmap-Erweiterung

- [x] Persistentes lokales Aufgabenregister
- [x] Prioritäten und Statusfilter
- [x] Ereignisverlauf und kontrollierte Statuswechsel
- [x] Android-/Termux-freundliche CLI
- [ ] Nexus-Aufgabenplanung mit expliziter Nutzerfreigabe
- [ ] Dashboard für Aufgaben und Agentenstatus
- [ ] Zeitgesteuerte Ausführung ausschließlich nach konfigurierter Freigabe


---

## 🖥️ 20. NClaw HTML Dashboard & Kommandozentrale

Ein responsives HTML5-Dashboard für Android/Termux und Linux. Die Oberfläche spricht ausschließlich mit einem kleinen lokalen Python-Server und der vorhandenen SQLite-Aufgabenverwaltung.

### Start

```bash
python -m dashboard.server
```

Anschließend im Browser öffnen:

```text
http://127.0.0.1:8765
```

Optionaler Port:

```bash
NCLAW_DASHBOARD_PORT=9000 python -m dashboard.server
```

### Dashboard-Menü

- Übersicht mit Statuskarten und letzten Aufgaben
- Aufgabenverwaltung mit Anlegen, Filtern und Statuswechseln
- Agentenübersicht für Nexus, Sandmann, TokenGuard und Task Engine
- Kommandozentrale mit begrenzten, erlaubten Aufgabenaktionen
- Aktivitätsübersicht
- Sicherheitsbereich und Einstellungen

### Sicherheit

- Bindet standardmäßig ausschließlich an `127.0.0.1`.
- Keine beliebige Shell-, Python- oder Terminal-Ausführung.
- Keine Agentenstarts oder externen API-Aufrufe aus dem Dashboard.
- Nur fest definierte HTTP-Routen.
- Eingaben werden serverseitig validiert.
- Statuswechsel verwenden die Regeln der Task Engine.
- Das Dashboard ist ein lokales Kontrollpanel, kein öffentlich abgesicherter Webdienst. Nicht ungeschützt ins Internet oder LAN exponieren.

### Dateien

```text
dashboard/
├── __init__.py
├── server.py
└── static/
    ├── index.html
    ├── style.css
    └── app.js
```


### Live-Systemmonitor

Die Startseite zeigt zusätzlich schreibgeschützte Host-Metriken: RAM-Auslastung (wenn `/proc/meminfo` verfügbar ist), freien Speicherplatz des Home-Dateisystems, Load Average und Systemlaufzeit (wenn `/proc/uptime` verfügbar ist). Die Anzeige aktualisiert sich alle 10 Sekunden über `GET /api/system`. Es werden keine Prozesse beendet, keine Einstellungen verändert und keine externen Dienste kontaktiert.


---

## 📱 21. Android-PWA und Offline-Oberfläche

Das lokale Dashboard kann auf Android in Chromium-basierten Browsern als App-Verknüpfung installiert werden.

1. NClaw in Termux starten: `python -m dashboard.server`.
2. Auf demselben Android-Gerät `http://127.0.0.1:8765` im Browser öffnen.
3. Im Browser-Menü **App installieren** oder **Zum Startbildschirm hinzufügen** wählen (die Bezeichnung hängt vom Browser ab).

Die PWA-Konfiguration liegt in `dashboard/static/manifest.webmanifest`. Der Service Worker speichert nur die statische Oberfläche (HTML, CSS, JavaScript, Manifest und Icon) zwischen. API-Antworten unter `/api/` werden ausdrücklich nicht gecacht; Aufgaben- und Systemdaten bleiben live und lokal. Wenn NClaw gestoppt ist, bleibt die Oberfläche möglicherweise sichtbar, aber dynamische Funktionen benötigen den laufenden lokalen Server.

Die Installation benötigt keine Cloud, keinen externen Dienst und keine zusätzlichen Python-Abhängigkeiten. Das Dashboard bleibt an `127.0.0.1` gebunden.

### Lokaler Ollama-Status

Im Bereich **Agenten** zeigt NClaw, ob Ollama erreichbar ist. Standardmäßig wird `http://127.0.0.1:11434` geprüft. Für einen Ollama-Rechner im privaten LAN kannst du vor dem Start des Dashboards `export OLLAMA_HOST=http://192.168.1.50:11434` setzen (IP und Port anpassen). Erlaubt sind Loopback-Adressen, private IP-Adressen und `.local`-Hostnamen; öffentliche Hosts, URL-Zugangsdaten und Weiterleitungen werden abgewiesen. Die Verbindungsprüfung fragt ausschließlich `GET /api/version` mit kurzem Timeout ab. Die Modellübersicht liest zusätzlich über `GET /api/tags` maximal 50 Modell-Metadatensätze (Name, Größe und Änderungsdatum). Sie lädt keine Modelle, startet keine Inferenz, scannt keine Netzwerkgeräte und führt keine Befehle aus. Beide Abfragen verwenden kurze Timeouts und folgen keinen HTTP-Weiterleitungen. Das Dashboard selbst bleibt ausschließlich an `127.0.0.1` gebunden.

Die **Kommandozentrale** bietet außerdem eine schreibgeschützte Systemdiagnose (Plattform, Python-Version, Arbeitsspeicher, Speicherplatz und Ollama-Status), das Erstellen geprüfter SQLite-Backups und einen Verlauf der letzten 20 Sicherungen. Backups werden neu angelegt und nicht überschrieben. Die Aufgaben-Aktivitäten sind über die lokale API nachvollziehbar. Es gibt absichtlich keine freie Shell, keine Modell-Inferenz und keine Fernsteuerung zum Starten/Stoppen von Prozessen.


---

## 🧩 22. Getrennte Agentenausführung, Freigaben und Modell-Inferenz

Diese drei Funktionen sind bewusst getrennt. Eine Freigabe ist keine Ausführung, ein Agentenstatus ist keine laufende Aktion und eine Modell-Inferenz darf keine Werkzeuge oder Systembefehle implizit starten.

### Agentenausführung (kontrollierter erster Baustein)

Der neue Modulpfad core/agent_runtime.py enthält einen expliziten Runtime-Dispatcher:

- Nur vertrauenswürdige Python-Handler, die der Anwendungscode ausdrücklich registriert hat, sind ausführbar.
- Keine Shell-Befehle, dynamischen Module, freien Funktionsnamen oder Code aus Nutzereingaben.
- Vor jedem Lauf ist eine Freigabe über den separaten ApprovalManager erforderlich.
- Die Freigabe bindet Agentenaktion und SHA-256 des kanonisierten JSON-Payloads; Änderungen am Payload machen sie ungültig.
- Freigaben werden vor dem Dispatch einmalig verbraucht. Auch fehlgeschlagene Läufe verbrauchen die Freigabe.
- Payloads und Ergebnisse sind auf jeweils 16 KiB begrenzt. Ausführungen erhalten einen Status und einen Fehlerklassennamen, aber keine sensiblen Exception-Details.

Der Runtime-Baustein ist eine Bibliotheksfunktion. Er wird nicht automatisch durch das Dashboard oder einen Agentenstatus gestartet. Konkrete Agenten-Handler müssen separat implementiert, geprüft und registriert werden.

### Freigabeverwaltung

core/approval_manager.py verwaltet auslaufende, einmalige Freigaben. Ablehnen, Ablauf, falsche Aktion, falsche Payload-Bindung und erneute Verwendung werden getrennt behandelt. Die Freigabe führt selbst keine Aktion aus. Der aufrufende Ausführungsdienst muss sie ausdrücklich konsumieren.

### Modell-Inferenz

models/ollama.py ist der getrennte Ollama-Transport. Er akzeptiert nur Loopback-, private IP-, localhost- oder .local-Ziele, lehnt Zugangsdaten und URL-Pfade ab, folgt keinen HTTP-Weiterleitungen und begrenzt Timeout (maximal 120 Sekunden), Prompt (16.000 Zeichen), Systemanweisung (4.000 Zeichen), Modellnamen (120 Zeichen) und Antwort (64 KiB). models/llama.py wählt das konfigurierte Modell und ruft diesen Adapter auf. Ein Modell-Output ist weiterhin nur Text/JSON-Daten und erhält keine Ausführungsrechte.

### Tests und Grenzen

Die Tests liegen in tests/test_agent_runtime.py, tests/test_approval_manager.py und tests/test_llama.py. Sie prüfen Freigabezwang, einmalige Nutzung, Payload-Bindung, unbekannte Agenten, Eingabegrenzen, Fehlerzustände, private Ollama-Ziele und Redirect-Schutz. Ein erfolgreicher Test mit Mock-Transport beweist nicht, dass ein echtes Ollama-Modell installiert oder verfügbar ist. Die Inferenz benötigt einen separat gestarteten und erreichbaren Ollama-Dienst.
