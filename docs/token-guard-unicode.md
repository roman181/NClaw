# TokenGuard: Unicode-Schätzung

TokenGuard schätzt den Kontextbedarf lokal, bevor ein Prompt an das einzige konfigurierte Llama-Modell über Ollama übergeben wird. Die Schätzung ist **kein exakter Ollama-Tokenizer** und darf nicht als exakte Tokenabrechnung interpretiert werden.

## Mehrsprachige Texte

Texte ohne Leerzeichen, insbesondere Chinesisch, Japanisch und Koreanisch, können durch reine Wortsegmentierung deutlich unterschätzt werden. TokenGuard zählt deshalb CJK-Codepoints separat und budgetiert dafür mindestens 1,5 geschätzte Tokens je Codepoint. Für den übrigen Text bleibt die bisherige konservative Maximal-Schätzung aus UTF-8-Bytes und lexikalischen Einheiten bestehen; beide Budgets werden addiert.

Die Erkennung umfasst CJK-Zeichen, Kana, Hangul sowie gebräuchliche CJK-Kompatibilitäts- und Erweiterungsbereiche. Gemischte Texte werden ebenfalls berücksichtigt.

## Fehlerhafte Unicode-Eingaben

Eingehender Text kann einzelne UTF-16-Surrogate enthalten, etwa durch escaped JSON-Daten. Solche Codepoints sind keine gültigen UTF-8-Skalarwerte. TokenGuard ersetzt sie ausschließlich für die Byte-Schätzung durch das standardisierte UTF-8-Ersatzzeichen, statt die Schätzung mit `UnicodeEncodeError` abzubrechen. Der ursprüngliche Prompt wird dadurch nicht verändert.

## Grenzen und Sicherheitsverhalten

- Die Schätzung ist absichtlich konservativ und kann den Bedarf überschätzen.
- Emoji, Spezial-Token und modellinterne Tokenisierung werden nicht exakt nachgebildet.
- Bei Erreichen des konfigurierten Schwellenwerts bleibt das bestehende lokale JSON-Handoff-Verhalten erhalten.
- Es gibt keinen Modellwechsel, keinen externen Tokenizer und keine automatische Fortsetzung.
- Für exakte Werte wäre ein zur konkret installierten Ollama-Modellversion passender Tokenizer nötig; diese Funktion behauptet das nicht.
