# main.py - Finale, korrigierte Version für Docker & Render

import os
import threading
from dotenv import load_dotenv
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# Lade Umgebungsvariablen (nützlich für lokale Tests, wird auf Render ignoriert)
load_dotenv()

# --- Importe aus unseren eigenen Dateien ---
# (Geht davon aus, dass alle .py-Dateien im selben Ordner liegen)
from models import db
from routes import user_bp
from telegram_bot import TochterErinnerungenBot

# --- App Initialisierung ---
# Der 'static' Ordner enthält Ihre Web-Oberfläche
STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
app = Flask(__name__, static_folder=STATIC_FOLDER)

# Es ist eine gute Praxis, den Secret Key aus den Umgebungsvariablen zu laden
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'ein-zufaelliger-geheimer-schluessel')

# CORS für die API aktivieren
CORS(app, resources={r"/api/*": {"origins": "*"}})

# API-Routen aus routes.py registrieren
app.register_blueprint(user_bp, url_prefix='/api')


# --- KORRIGIERTE DATENBANK KONFIGURATION ---
# Dieser Pfad '/var/data/database' wird von Render bereitgestellt und ist persistent.
DB_STORAGE_DIR = '/var/data/database'
DB_FILE_PATH = os.path.join(DB_STORAGE_DIR, 'app.db')

# Wir prüfen, ob der Speicherpfad existiert. In der Render-Umgebung sollte er das.
# Wenn nicht (z.B. bei lokaler Ausführung), erstellen wir einen lokalen 'database'-Ordner.
if not os.path.exists(DB_STORAGE_DIR):
    print(f"WARNUNG: Persistenter Speicherpfad '{DB_STORAGE_DIR}' nicht gefunden.")
    print("Erstelle lokalen Fallback-Ordner 'database'. Dies ist für lokale Tests normal.")
    local_fallback_dir = os.path.join(os.path.dirname(__file__), 'database')
    if not os.path.exists(local_fallback_dir):
        os.makedirs(local_fallback_dir)
    DB_FILE_PATH = os.path.join(local_fallback_dir, 'app.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_FILE_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Erstellt die Datenbanktabellen, falls sie nicht existieren
with app.app_context():
    print(f"Initialisiere Datenbank unter: {DB_FILE_PATH}")
    db.create_all()
    print("Datenbank-Tabellen erfolgreich initialisiert.")


# --- Routen für die Web-Oberfläche ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static_app(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Leitet alle unbekannten Anfragen an die index.html weiter
        return send_from_directory(app.static_folder, 'index.html')


# --- Telegram Bot Start-Funktion ---
def run_telegram_bot():
    """Diese Funktion startet den Bot in einem separaten Thread."""
    print("🤖 Versuch, den Telegram Bot zu starten...")
    try:
        bot_instance = TochterErinnerungenBot()
        bot_instance.run()
        print("✅ Telegram Bot wurde gestartet und läuft.")
    except Exception as e:
        print(f"❌ Ein kritischer Fehler ist beim Starten des Bots aufgetreten: {e}")


# --- Hauptausführung des Programms ---
if __name__ == '__main__':
    # 1. Starte den Telegram-Bot in einem Hintergrund-Thread
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

    # 2. Starte den Flask Webserver
    # Render stellt die 'PORT'-Umgebungsvariable automatisch zur Verfügung.
    server_port = int(os.getenv('PORT', 5000))
    print(f"🌐 Starte den Webserver auf http://0.0.0.0:{server_port}" )
    app.run(host='0.0.0.0', port=server_port)

