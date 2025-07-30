# main.py - Finale, korrigierte Version

import asyncio
import os
import logging
import threading
from flask import Flask
from telegram_bot import TochterErinnerungenBot

# Logging konfigurieren
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Webserver für Render Health-Check ---
app = Flask(__name__)

@app.route('/')
def index():
    return "Bot is running healthily!"

def run_flask():
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
# --- Ende des Webserver-Teils ---

async def main():
    """Initialisiert alle Dienste und startet den Bot."""
    
    # 1. Bot-Instanz erstellen
    bot = TochterErinnerungenBot()
    
    # 2. Google Sheets Manager explizit initialisieren
    #    Wir greifen auf die Instanz zu, die im Bot erstellt wurde.
    logger.info("Initialisiere Google Sheets Manager...")
    is_sheets_ok = await bot.sheets_manager.initialize()
    
    if not is_sheets_ok:
        logger.critical("KRITISCHER FEHLER: Google Sheets konnte nicht initialisiert werden. Der Bot startet, aber das Speichern wird fehlschlagen.")
        # Man könnte hier auch mit `return` abbrechen, aber wir lassen den Bot trotzdem laufen.
    
    # 3. Den Bot starten (jetzt, da alles andere bereit ist)
    await bot.run()


if __name__ == '__main__':
    try:
        # Starte den Flask-Webserver in einem Hintergrund-Thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("Flask-Server für Render Health-Check gestartet.")

        # Starte die asynchrone Hauptfunktion, die alles initialisiert und den Bot startet
        asyncio.run(main())
        
    except Exception as e:
        logger.critical(f"Bot konnte nicht gestartet werden: {e}", exc_info=True)
