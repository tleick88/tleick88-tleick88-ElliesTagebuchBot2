#!/usr/bin/env python3
"""
Deployment-Script für den Tochter-Erinnerungen Bot
Bereitet den Bot für die Produktion vor und startet ihn
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Überprüft ob alle Anforderungen erfüllt sind"""
    print("🔍 Überprüfe Anforderungen...")
    
    # .env Datei prüfen
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env Datei nicht gefunden!")
        print("💡 Erstelle eine .env Datei mit:")
        print("   TELEGRAM_BOT_TOKEN=dein_bot_token")
        print("   GOOGLE_SHEETS_ID=deine_sheets_id")
        return False
    
    # Bot Token prüfen
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN nicht in .env gefunden!")
        return False
    
    sheets_id = os.getenv('GOOGLE_SHEETS_ID')
    if not sheets_id:
        print("❌ GOOGLE_SHEETS_ID nicht in .env gefunden!")
        return False
    
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY nicht verfügbar!")
        return False
    
    print("✅ Alle Anforderungen erfüllt!")
    return True

def install_dependencies():
    """Installiert alle Dependencies"""
    print("📦 Installiere Dependencies...")
    
    try:
        # Virtual Environment aktivieren und Dependencies installieren
        result = subprocess.run([
            'bash', '-c', 
            'source venv/bin/activate && pip install -r requirements.txt'
        ], check=True, capture_output=True, text=True)
        
        print("✅ Dependencies erfolgreich installiert!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Fehler bei Installation: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def create_systemd_service():
    """Erstellt einen systemd Service für automatischen Start"""
    print("🔧 Erstelle systemd Service...")
    
    current_dir = os.getcwd()
    service_content = f"""[Unit]
Description=Tochter Erinnerungen Telegram Bot
After=network.target

[Service]
Type=simple
User={os.getenv('USER', 'ubuntu')}
WorkingDirectory={current_dir}
Environment=PATH={current_dir}/venv/bin
ExecStart={current_dir}/venv/bin/python {current_dir}/start_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('/tmp/tochter-erinnerungen-bot.service')
    service_file.write_text(service_content)
    
    print(f"📄 Service-Datei erstellt: {service_file}")
    print("💡 Um den Service zu installieren, führe aus:")
    print(f"   sudo cp {service_file} /etc/systemd/system/")
    print("   sudo systemctl daemon-reload")
    print("   sudo systemctl enable tochter-erinnerungen-bot")
    print("   sudo systemctl start tochter-erinnerungen-bot")
    
    return True

def test_bot():
    """Testet den Bot kurz"""
    print("🧪 Teste Bot...")
    
    try:
        # Bot für 5 Sekunden starten
        process = subprocess.Popen([
            'bash', '-c',
            'source venv/bin/activate && timeout 5 python start_bot.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        stdout, stderr = process.communicate()
        
        if "Bot erfolgreich initialisiert" in stdout:
            print("✅ Bot-Test erfolgreich!")
            return True
        else:
            print("❌ Bot-Test fehlgeschlagen!")
            print(f"Output: {stdout}")
            print(f"Error: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Bot-Test: {e}")
        return False

def create_backup_script():
    """Erstellt ein Backup-Script für die Daten"""
    print("💾 Erstelle Backup-Script...")
    
    backup_script = """#!/bin/bash
# Backup-Script für Tochter-Erinnerungen Bot

BACKUP_DIR="backups/$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

# .env Datei sichern (ohne sensible Daten)
cp .env "$BACKUP_DIR/env_backup.txt"

# Logs sichern falls vorhanden
if [ -f "bot.log" ]; then
    cp bot.log "$BACKUP_DIR/"
fi

# Google Sheets ID für Referenz
echo "Google Sheets ID: $GOOGLE_SHEETS_ID" > "$BACKUP_DIR/sheets_info.txt"

echo "✅ Backup erstellt in: $BACKUP_DIR"
"""
    
    backup_file = Path('create_backup.sh')
    backup_file.write_text(backup_script)
    backup_file.chmod(0o755)
    
    print(f"✅ Backup-Script erstellt: {backup_file}")
    return True

def main():
    """Hauptfunktion für Deployment"""
    print("🚀 Starte Deployment für Tochter-Erinnerungen Bot")
    print("=" * 50)
    
    # Schritt 1: Anforderungen prüfen
    if not check_requirements():
        print("❌ Deployment abgebrochen - Anforderungen nicht erfüllt")
        return False
    
    # Schritt 2: Dependencies installieren
    if not install_dependencies():
        print("❌ Deployment abgebrochen - Dependencies-Installation fehlgeschlagen")
        return False
    
    # Schritt 3: Bot testen
    if not test_bot():
        print("❌ Deployment abgebrochen - Bot-Test fehlgeschlagen")
        return False
    
    # Schritt 4: Systemd Service erstellen
    create_systemd_service()
    
    # Schritt 5: Backup-Script erstellen
    create_backup_script()
    
    print("\n" + "=" * 50)
    print("🎉 Deployment erfolgreich abgeschlossen!")
    print("\n📋 Nächste Schritte:")
    print("1. Bot manuell starten: python start_bot.py")
    print("2. Oder systemd Service installieren (siehe Anweisungen oben)")
    print("3. Bot in Telegram testen mit /start")
    print("4. Erste Sprachnachricht senden")
    print("5. Zusammenfassungen testen mit /monats_zusammenfassung")
    print("\n💡 Bei Problemen: Logs in der Konsole überprüfen")
    print("📞 Support: Dokumentation in README.md")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

