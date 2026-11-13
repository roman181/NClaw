🧠 NClaw – Autonomous AI Agent Framework

"CI" (https://github.com/roman181/NClaw/actions/workflows/ci.yml/badge.svg)
"Security" (https://github.com/roman181/NClaw/actions/workflows/security.yml/badge.svg)
"Termux" (https://github.com/roman181/NClaw/actions/workflows/termux.yml/badge.svg)

"Status" (https://img.shields.io/badge/status-Konzeptphase-orange)
"Architecture" (https://img.shields.io/badge/architecture-modular-blue)
"Local First" (https://img.shields.io/badge/local--first-yes-green)
"Platform" (https://img.shields.io/badge/platform-Android%20%7C%20Linux-lightgrey)
"License" (https://img.shields.io/badge/license-Apache--2.0-blue)

NClaw ist ein autonomes, local-first KI-Agenten-Framework, das aus einem einfachen Chat einen proaktiven digitalen Mitarbeiter macht.

NClaw verbindet lokale KI-Modelle, autonome Agenten, Skills, eine lokale Wissensbibliothek und kontrollierte Systemwerkzeuge zu einem modularen AI Office.

Die Steuerung erfolgt über eine zentrale Benutzeroberfläche und optional über Telegram.

«Projektstatus: Frühes Entwicklungsstadium. Der Nexus-Core, ein einfacher Orchestrator, ein Freigabeschutz und erste Tests sind implementiert. Weitere Funktionen befinden sich in Planung.»

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

- Beliebige Dateien importieren.
- ZIP-Archive analysieren.
- PDFs auslesen.
- Quellcode untersuchen.
- GitHub-Links importieren.
- Duplikate erkennen.
- Inhalte kategorisieren.
- Neue Skills identifizieren.

Verzeichnis:

Sandbox-Ai/
├── incoming/
├── processing/
├── approved/
├── rejected/
└── quarantine/

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

TokenGuard überwacht die verfügbare Kontextkapazität des Llama-Modells.

Geplanter Ablauf:

- Kontextverbrauch überwachen.
- Bei 90 % einen Handoff auslösen.
- Projektstatus als JSON sichern.
- Offene Aufgaben dokumentieren.
- Einen JSON-Zwischenstand sichern.
- Kontext für eine spätere Fortsetzung bereitstellen.
- Arbeit nach Freigabe fortsetzen.

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
NCLAW_LOG_LEVEL=INFO\nNCLAW_WORKSPACE=workspace

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
│   └── telegram/
│       ├── __init__.py
│       └── bot.py
│
├── core/
│   ├── __init__.py
│   ├── nexus.py
│   ├── orchestrator.py
│   └── approvals.py
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
│   └── test_telegram.py
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

Neue Versionen werden über Git-Tags veröffentlicht.

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
- [ ] Sandmann-Agent
- [ ] Agentenverwaltung
- [x] Telegram-Freigabe-Basis (Ablaufzeit, Einmalfreigabe, Aktionsbindung)\n- [x] Erste kontrollierte Aktion: neue Textdatei im Workspace nach separater Freigabe und Ausführungsbefehl
- [ ] Aufgabenverwaltung

Phase 3 – Bibliothek

- [ ] Sandbox-Ai
- [ ] ZIP-Analyse
- [ ] PDF-Analyse
- [ ] GitHub-Import
- [ ] Dateiverwaltung
- [ ] Duplikaterkennung

Phase 4 – Intelligenz

- [x] Llama-Einzelmodell (Basis)
- [ ] TokenGuard
- [ ] JSON-Handoff
- [ ] Skill-Registry
- [ ] Skill-Versionierung

Phase 5 – Evolution

- [ ] Lernschleife
- [ ] Skill-Verbesserung
- [ ] Skill-Baum
- [ ] Three.js Visualisierung
- [ ] Agenten-Evolution

Phase 6 – Dashboard

- [ ] Nexus Chat
- [ ] Agentenstatus
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
