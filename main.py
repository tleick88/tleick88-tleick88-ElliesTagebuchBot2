# main.py

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

        # Erstelle eine Instanz des Bots
        bot = TochterErinnerungenBot()
        
        # Rufe die blockierende run-Methode des Bots auf.
        # Diese Methode wird nun den Haupt-Thread übernehmen und den Bot ausführen.
        # asyncio.run() wird nicht mehr benötigt.
        bot.run()

    except Exception as e:
        logger.critical(f"Bot konnte nicht gestartet werden: {e}", exc_info=True)
