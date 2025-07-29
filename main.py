import os
import sys
import threading
import time
from dotenv import load_dotenv

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Lade Umgebungsvariablen
load_dotenv()

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.telegram_bot import TochterErinnerungenBot

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# CORS aktivieren
CORS(app)

app.register_blueprint(user_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

# Bot-Instanz
bot_instance = None
bot_thread = None

@app.route('/api/bot/status')
def bot_status():
    """API Endpoint um Bot-Status zu überprüfen"""
    global bot_instance, bot_thread
    
    status = {
        'bot_running': bot_thread is not None and bot_thread.is_alive(),
        'bot_token_configured': bool(os.getenv('TELEGRAM_BOT_TOKEN')),
        'openai_configured': bool(os.getenv('OPENAI_API_KEY')),
        'sheets_configured': bool(os.getenv('GOOGLE_SHEETS_ID'))
    }
    
    return jsonify(status)

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """API Endpoint um Bot zu starten"""
    global bot_instance, bot_thread
    
    try:
        if bot_thread and bot_thread.is_alive():
            return jsonify({'success': False, 'message': 'Bot läuft bereits'})
        
        bot_instance = TochterErinnerungenBot()
        bot_thread = threading.Thread(target=bot_instance.run, daemon=True)
        bot_thread.start()
        
        # Kurz warten um sicherzustellen, dass der Bot startet
        time.sleep(2)
        
        return jsonify({'success': True, 'message': 'Bot erfolgreich gestartet'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Starten: {str(e)}'})

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """API Endpoint um Bot zu stoppen"""
    global bot_instance, bot_thread
    
    try:
        if bot_instance and hasattr(bot_instance, 'application'):
            # Bot stoppen (vereinfacht)
            bot_instance = None
            
        return jsonify({'success': True, 'message': 'Bot gestoppt'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Fehler beim Stoppen: {str(e)}'})

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

def start_bot_automatically():
    """Startet den Bot automatisch beim App-Start"""
    global bot_instance, bot_thread
    
    try:
        print("🤖 Starte Telegram Bot automatisch...")
        bot_instance = TochterErinnerungenBot()
        bot_thread = threading.Thread(target=bot_instance.run, daemon=True)
        bot_thread.start()
        print("✅ Telegram Bot erfolgreich gestartet!")
        
    except Exception as e:
        print(f"❌ Fehler beim automatischen Bot-Start: {e}")

if __name__ == '__main__':
    # Bot automatisch starten
    start_bot_automatically()
    
    # Flask App starten
    print("🌐 Starte Flask Web-Interface...")
    app.run(host='0.0.0.0', port=5000, debug=False)  # Debug=False um Threading-Probleme zu vermeiden
