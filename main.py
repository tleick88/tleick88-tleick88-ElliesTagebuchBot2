# main.py - Finale, stabile und synchrone Version

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

if __name__ == '__main__':
    try:
        # Starte den Flask-Webserver in einem Hintergrund-Thread
        flask_thread = threading.Thread(target=run_flask, daemon=True)
        flask_thread.start()
        logger.info("Flask-Server für Render Health-Check gestartet.")

        # 1. Bot-Instanz erstellen (dies initialisiert auch Gemini synchron)
        bot = TochterErinnerungenBot()
        
        # 2. Den Bot starten. Die run()-Methode ist jetzt blockierend und
        #    kümmert sich intern um ALLE asynchronen Aufgaben, inkl. Initialisierung.
        logger.info("Übergebe die Kontrolle an den Bot...")
        bot.run()

    except Exception as e:
        logger.critical(f"Bot konnte nicht gestartet werden: {e}", exc_info=True)

