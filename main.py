# main.py - Aktualisierte Version für den Webhook-Modus auf Render

import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

# Lade Umgebungsvariablen (nützlich für lokale Tests)
load_dotenv()

# --- Importe aus unseren eigenen Dateien ---
from models import db
from routes import user_bp
from telegram_bot import TochterErinnerungenBot
# Wichtig: Wir benötigen die Update-Klasse von der Telegram-Bibliothek
from telegram import Update

# --- App Initialisierung ---
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, static_folder=STATIC_FOLDER)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ein-zufaelliger-geheimer-schluessel')
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.register_blueprint(user_bp, url_prefix='/api')

# --- Datenbank Konfiguration ---
DB_STORAGE_DIR = '/var/data/database'
DB_FILE_PATH = os.path.join(DB_STORAGE_DIR, 'app.db')

if not os.path.exists(DB_STORAGE_DIR):
    print(f"WARNUNG: Persistenter Speicherpfad '{DB_STORAGE_DIR}' nicht gefunden.")
    print("Erstelle lokalen Fallback-Ordner 'database'.")
    local_fallback_dir = os.path.join(os.path.dirname(__file__), 'database')
    if not os.path.exists(local_fallback_dir):
        os.makedirs(local_fallback_dir)
    DB_FILE_PATH = os.path.join(local_fallback_dir, 'app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print(f"Initialisiere Datenbank unter: {DB_FILE_PATH}")
    db.create_all()
    print("Datenbank-Tabellen erfolgreich initialisiert.")

# --- BOT-INITIALISIERUNG UND WEBHOOK-SETUP ---

# 1. Erstelle eine Instanz des Bots
#    Die __init__-Methode des Bots sollte das Token und das Application-Objekt initialisieren
bot_instance = TochterErinnerungenBot()

# 2. Rufe die run()-Methode auf, um alle Handler (Befehle etc.) zu registrieren
#    Die run()-Methode darf NICHT mehr updater.start_polling() enthalten!
bot_instance.run() 

# 3. Hole das Application-Objekt aus der Bot-Instanz
#    (Stellen Sie sicher, dass Ihre Bot-Klasse eine 'self.application'-Variable hat)
application = bot_instance.application

# 4. Definiere die Webhook-Route
#    Dies ist der Endpunkt, den Telegram aufrufen wird.
#    Das Token in der URL dient als einfaches Geheimnis.
@app.route(f'/{bot_instance.token}', methods=['POST'])
async def telegram_webhook():
    """Diese Funktion verarbeitet eingehende Updates von Telegram."""
    try:
        # Nimm die JSON-Daten von der Anfrage
        update_data = await request.get_json(force=True)
        # Erstelle ein Update-Objekt daraus
        update = Update.de_json(update_data, application.bot)
        # Verarbeite das Update (dies führt die passenden Handler aus)
        await application.process_update(update)
        return 'ok', 200
    except Exception as e:
        print(f"Fehler im Webhook: {e}")
        return 'error', 500

# --- Routen für die Web-Oberfläche ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static_app(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# --- Hauptausführung des Programms ---
if __name__ == '__main__':
    # Der Code zum Setzen des Webhooks bleibt unverändert
    render_url = os.getenv('RENDER_EXTERNAL_URL')
    if render_url:
        webhook_url = f"{render_url}/{bot_instance.token}"
        print(f"Versuche, Webhook zu setzen auf: {webhook_url}")
        
        async def set_telegram_webhook():
            await application.bot.set_webhook(url=webhook_url, allowed_updates=Update.ALL_TYPES)
        
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(set_telegram_webhook())
        else:
            loop.run_until_complete(set_telegram_webhook())
            
        print("✅ Webhook-Setz-Befehl an Telegram gesendet.")
    else:
        print("🔴 WARNUNG: RENDER_EXTERNAL_URL nicht gefunden.")

    # --- HIER IST DIE ENTSCHEIDENDE ÄNDERUNG ---
    # Wir importieren den "Übersetzer"
    from wsgitoasgi import WsgiToAsgi

    # Wir "verpacken" unsere Flask-App in den Übersetzer
    asgi_app = WsgiToAsgi(app)

    # Wir importieren uvicorn
    import uvicorn
    server_port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starte den Webserver mit uvicorn und WSGI-zu-ASGI-Adapter auf http://0.0.0.0:{server_port}" )
    
    # Wir übergeben uvicorn die "übersetzte" App anstelle der rohen Flask-App
    uvicorn.run(asgi_app, host='0.0.0.0', port=server_port)
