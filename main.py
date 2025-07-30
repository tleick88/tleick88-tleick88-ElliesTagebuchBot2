# main.py

import asyncio
import os
import logging
import threading
from flask import Flask
from telegram_bot import TochterErinnerungenBot

# Logging konfigurieren (optional, aber empfohlen)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- NEUER TEIL: Webserver für Render ---
# Erstelle eine einfache Flask-App
app = Flask(__name__)

@app.route('/')
def index():
    # Diese Seite wird von Render's Health Check aufgerufen
    return "Bot is running healthily!"

def run_flask():
    # Render stellt den Port über die PORT-Umgebungsvariable bereit.
    # Der Default 5000 ist für lokales Testen.
    port = int(os.environ.get('PORT', 5000))
    # Wichtig: host='0.0.0.0' damit es von außerhalb des Containers erreichbar ist.
    app.run(host='0.0.0.0', port=port)
# --- ENDE DES NEUEN TEILS ---

async def main():
    """Initialisiert und startet den Bot."""
    bot = TochterErinnerungenBot()
    
    # Diese Methode registriert nur die Handler, sie startet den Bot nicht.
    # Das ist gut so, wie es in deinem Code bereits ist.
    bot.run() 
    
    logger.info("Starte Polling für den Bot...")
    # `run_polling` startet den Bot und blockiert, bis das Programm beendet wird.
    await bot.application.run_polling()

if __name__ == '__main__':
    try:
        # Starte den Flask-Webserver in einem Hintergrund-Thread.
        # Der 'daemon=True' sorgt dafür, dass der Thread beendet wird, wenn das Hauptprogramm endet.
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("Flask-Server für Render Health-Check gestartet.")

        # Starte die asynchrone Hauptfunktion des Bots.
        asyncio.run(main())
        
    except Exception as e:
        logger.critical(f"Bot konnte nicht gestartet werden: {e}", exc_info=True)

