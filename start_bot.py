#!/usr/bin/env python3
"""
Separater Starter für den Telegram Bot
Läuft unabhängig von Flask
"""

import os
import sys
from dotenv import load_dotenv

# Pfad für Imports setzen
sys.path.insert(0, os.path.dirname(__file__))

# Umgebungsvariablen laden
load_dotenv()

from src.telegram_bot import TochterErinnerungenBot

if __name__ == "__main__":
    print("🚀 Starte Tochter-Erinnerungen Telegram Bot...")
    
    # Bot-Token überprüfen
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN nicht gefunden in .env Datei!")
        sys.exit(1)
    
    # OpenAI API Key überprüfen
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY nicht gefunden!")
        sys.exit(1)
    
    print(f"✅ Bot-Token konfiguriert: {bot_token[:10]}...")
    print(f"✅ OpenAI API konfiguriert")
    
    try:
        # Bot erstellen und starten
        bot = TochterErinnerungenBot()
        print("🤖 Bot erfolgreich initialisiert!")
        print("📱 Bot ist jetzt online und wartet auf Nachrichten...")
        print("💡 Sende /start an deinen Bot in Telegram um zu beginnen!")
        print("🛑 Drücke Ctrl+C um den Bot zu stoppen")
        
        # Bot starten (blockiert hier)
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot wird gestoppt...")
    except Exception as e:
        print(f"❌ Fehler beim Starten des Bots: {e}")
        sys.exit(1)

