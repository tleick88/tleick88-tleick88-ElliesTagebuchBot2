# 💝 Tochter-Erinnerungen Telegram Bot

Ein liebevoller Telegram-Bot, der deine Sprachnachrichten über deine Tochter in wunderschöne Erinnerungen verwandelt und für die Zukunft bewahrt.

## 🌟 Was macht dieser Bot?

Dieser Bot ist dein persönlicher Erinnerungs-Assistent, der:

- 🎤 **Sprachnachrichten empfängt** über lustige, süße oder besondere Momente mit deiner Tochter
- 🤖 **Automatisch transkribiert** mit modernster KI-Technologie (OpenAI Whisper)
- ✨ **Text aufbereitet** und in schöne, liebevolle Erinnerungen verwandelt
- 📊 **In Google Sheets speichert** für dauerhafte Aufbewahrung
- 📅 **Monats- und Jahres-Zusammenfassungen** erstellt mit emotionalen KI-generierten Rückblicken
- 💝 **Ein Geschenk für die Zukunft** - deine Tochter wird diese Erinnerungen lieben!

## 🚀 Schnellstart

### 1. Bot starten
```bash
cd tochter_erinnerungen_bot
python start_bot.py
```

### 2. In Telegram verwenden
1. Suche deinen Bot in Telegram
2. Sende `/start` um zu beginnen
3. Schicke eine Sprachnachricht über deine Tochter
4. Schaue zu, wie der Bot sie in eine schöne Erinnerung verwandelt!

### 3. Zusammenfassungen abrufen
- `/monats_zusammenfassung` - Alle Erinnerungen des aktuellen Monats
- `/jahres_zusammenfassung` - Rückblick auf das ganze Jahr

## 📋 Verfügbare Befehle

| Befehl | Beschreibung |
|--------|-------------|
| `/start` | Bot starten und Willkommensnachricht |
| `/help` | Hilfe und Anweisungen anzeigen |
| `/monats_zusammenfassung` | Intelligente Zusammenfassung des aktuellen Monats |
| `/jahres_zusammenfassung` | Umfassender Jahresrückblick |

## 🛠️ Installation und Setup

### Voraussetzungen
- Python 3.11+
- Telegram Bot Token (von @BotFather)
- OpenAI API Key
- Google Sheets Zugang

### Schritt-für-Schritt Installation

1. **Repository klonen/herunterladen**
   ```bash
   # Alle Dateien in einen Ordner kopieren
   cd tochter_erinnerungen_bot
   ```

2. **Virtual Environment erstellen**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # oder
   venv\Scripts\activate     # Windows
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren**
   
   Erstelle eine `.env` Datei mit:
   ```env
   TELEGRAM_BOT_TOKEN=dein_bot_token_hier
   GOOGLE_SHEETS_ID=deine_google_sheets_id
   OPENAI_API_KEY=dein_openai_key  # Falls nicht global verfügbar
   ```

5. **Google Sheets vorbereiten**
   - Öffne deine Google-Tabelle
   - Teile sie mit dem Bot (Service Account Email) oder mache sie öffentlich bearbeitbar
   - Die erste Zeile wird automatisch als Header erstellt

6. **Bot testen**
   ```bash
   python start_bot.py
   ```

### Automatisches Deployment
```bash
python deploy.py
```

Dieses Script:
- ✅ Überprüft alle Anforderungen
- 📦 Installiert Dependencies
- 🧪 Testet den Bot
- 🔧 Erstellt systemd Service für automatischen Start
- 💾 Erstellt Backup-Scripts

## 📊 Google Sheets Integration

### Datenstruktur
Der Bot speichert folgende Spalten in deiner Google-Tabelle:

| Spalte | Inhalt | Beispiel |
|--------|--------|----------|
| A | Datum und Zeit | 24.07.2025 14:30:15 |
| B | Original-Transkript | "Heute hat sie zum ersten mal mama gesagt" |
| C | Aufbereiteter Text | "Heute war ein ganz besonderer Tag - meine kleine Tochter hat zum ersten Mal 'Mama' gesagt..." |
| D | Monat | 2025-07 |
| E | Jahr | 2025 |

### Google Sheets Berechtigungen einrichten

**Option 1: Einfache Freigabe**
1. Öffne deine Google-Tabelle
2. Klicke "Freigeben"
3. Ändere auf "Jeder mit dem Link kann bearbeiten"

**Option 2: Service Account (Empfohlen für Produktion)**
1. Gehe zur [Google Cloud Console](https://console.cloud.google.com/)
2. Erstelle ein neues Projekt oder wähle ein bestehendes
3. Aktiviere die Google Sheets API
4. Erstelle Service Account Credentials
5. Lade die JSON-Datei herunter und speichere sie als `service_account.json`
6. Teile deine Google-Tabelle mit der Service Account Email

## 🤖 KI-Features

### Sprachtranskription
- **OpenAI Whisper**: Hochpräzise Transkription in deutscher Sprache
- **Automatische Bereinigung**: Entfernt Füllwörter und korrigiert Fehler
- **Robuste Fehlerbehandlung**: Fallback-Mechanismen bei API-Problemen

### Text-Aufbereitung
- **GPT-4 Integration**: Verwandelt Transkripte in liebevolle Erinnerungen
- **Emotionale Sprache**: Warm, herzlich und für die Zukunft geschrieben
- **Detail-Erhaltung**: Alle wichtigen Informationen bleiben erhalten
- **Konsistente Ich-Form**: Geschrieben aus Eltern-Perspektive

### Intelligente Zusammenfassungen
- **Monats-Rückblicke**: Emotionale Zusammenfassung aller Erinnerungen
- **Jahres-Übersichten**: Entwicklungsreflexion und Highlights
- **Automatische Kategorisierung**: Nach Datum und Themen sortiert
- **Poetische Sprache**: Schöne, literarische Formulierungen

## 🔧 Konfiguration

### Erweiterte Einstellungen

**Bot-Verhalten anpassen** (in `src/telegram_bot.py`):
```python
# Maximale Sprachnachricht-Länge (Sekunden)
MAX_VOICE_DURATION = 300  # 5 Minuten

# Whisper-Einstellungen
WHISPER_TEMPERATURE = 0.0  # Konsistenz vs. Kreativität
WHISPER_LANGUAGE = "de"    # Sprache
```

**Text-Aufbereitung anpassen** (in `src/summary_generator.py`):
```python
# GPT-4 Einstellungen
TEMPERATURE = 0.8          # Kreativität der Zusammenfassungen
MAX_TOKENS = 800          # Maximale Länge
```

### Logging
Logs werden in der Konsole ausgegeben. Für Datei-Logging:

```python
# In telegram_bot.py hinzufügen:
logging.basicConfig(
    filename='bot.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🚨 Troubleshooting

### Häufige Probleme

**Bot startet nicht**
- ✅ Überprüfe `.env` Datei und Bot-Token
- ✅ Stelle sicher, dass alle Dependencies installiert sind
- ✅ Prüfe Internet-Verbindung

**Sprachtranskription funktioniert nicht**
- ✅ OpenAI API Key korrekt konfiguriert?
- ✅ Ausreichend API-Credits vorhanden?
- ✅ Sprachnachricht nicht zu lang (max. 5 Min)?

**Google Sheets Speicherung fehlschlägt**
- ✅ Google Sheets ID korrekt in `.env`?
- ✅ Berechtigungen für die Tabelle gesetzt?
- ✅ Service Account JSON vorhanden?

**Zusammenfassungen sind leer**
- ✅ Sind bereits Erinnerungen gespeichert?
- ✅ Richtiger Monat/Jahr ausgewählt?
- ✅ Google Sheets Verbindung funktioniert?

### Debug-Modus
```bash
# Mit ausführlichen Logs starten
python start_bot.py --debug
```

### Logs überprüfen
```bash
# Systemd Service Logs (falls installiert)
sudo journalctl -u tochter-erinnerungen-bot -f

# Oder direkt in der Konsole beim manuellen Start
```

## 🔒 Sicherheit und Datenschutz

### Datenschutz
- **Lokale Verarbeitung**: Sprachdaten werden nur temporär verarbeitet
- **Sichere APIs**: Verschlüsselte Verbindungen zu OpenAI und Google
- **Keine Datenspeicherung**: Bot speichert keine Sprachdateien dauerhaft
- **Private Google Sheets**: Nur du hast Zugang zu deinen Erinnerungen

### API-Keys sicher aufbewahren
- ❌ Niemals API-Keys in Code committen
- ✅ Immer `.env` Datei verwenden
- ✅ `.env` zu `.gitignore` hinzufügen
- ✅ Regelmäßig API-Keys rotieren

### Backup-Strategie
```bash
# Automatisches Backup erstellen
./create_backup.sh

# Google Sheets als zusätzliches Backup
# (Daten sind bereits in der Cloud gesichert)
```

## 🎁 Das perfekte Geschenk

Dieser Bot erstellt nicht nur Erinnerungen - er erschafft ein **digitales Tagebuch voller Liebe**, das du deiner Tochter eines Tages schenken kannst.

### Ideen für die Zukunft
- 📖 **Erinnerungs-Buch**: Drucke die schönsten Momente als Buch
- 🎂 **Geburtstags-Geschenk**: Jahres-Zusammenfassung zum Geburtstag
- 🎓 **Meilenstein-Momente**: Besondere Entwicklungsschritte festhalten
- 💌 **Liebesbriefe**: Deine Gedanken und Gefühle für die Zukunft

### Tipps für bessere Erinnerungen
- 🎤 **Sprich deutlich** und in ruhiger Umgebung
- 📝 **Erzähle Details** - auch kleine Momente sind wertvoll
- 💭 **Teile deine Gefühle** - was denkst du in diesem Moment?
- 📅 **Regelmäßig nutzen** - täglich oder wöchentlich
- 🌟 **Besondere Momente** - erste Worte, Schritte, Lachen

## 📞 Support und Weiterentwicklung

### Bei Problemen
1. 📖 Diese Dokumentation durchlesen
2. 🔍 Logs überprüfen
3. 🧪 `python deploy.py` erneut ausführen
4. 💬 GitHub Issues erstellen (falls Repository verfügbar)

### Mögliche Erweiterungen
- 📱 **Mobile App**: Native iOS/Android App
- 🖼️ **Foto-Integration**: Bilder zu Erinnerungen hinzufügen
- 🎵 **Audio-Archiv**: Original-Sprachnachrichten aufbewahren
- 👨‍👩‍👧‍👦 **Multi-User**: Mehrere Familienmitglieder
- 🌍 **Mehrsprachig**: Unterstützung für andere Sprachen
- 📊 **Analytics**: Statistiken über Erinnerungen
- 🔔 **Erinnerungen**: Automatische Aufforderungen zum Aufnehmen

## 📄 Lizenz und Credits

### Verwendete Technologien
- **Python 3.11+**: Programmiersprache
- **python-telegram-bot**: Telegram Bot Framework
- **OpenAI API**: Whisper (Transkription) und GPT-4 (Text-Aufbereitung)
- **Google Sheets API**: Datenspeicherung
- **Flask**: Web-Framework für erweiterte Features

### Credits
Entwickelt mit ❤️ für alle Eltern, die die kostbaren Momente mit ihren Kindern festhalten möchten.

---

**💝 Viel Freude beim Sammeln wundervoller Erinnerungen! 💝**

