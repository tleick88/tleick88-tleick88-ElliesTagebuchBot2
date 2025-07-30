# telegram_bot.py - Angepasst für Google Gemini

"""
Telegram Bot für Tochter-Erinnerungen
Verarbeitet Sprachnachrichten, verfeinert sie mit Google Gemini und speichert sie in Google Sheets
"""

import os
import logging
from datetime import datetime
import pytz
from typing import Optional
from io import BytesIO

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

# +++ NEUE IMPORTS FÜR GEMINI +++
import vertexai
from vertexai.generative_models import GenerativeModel

from google_sheets_manager import GoogleSheetsManager
from summary_generator import SummaryGenerator

# Lade Umgebungsvariablen
load_dotenv()

# Logging konfigurieren
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class TochterErinnerungenBot:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN nicht gefunden! Bitte als Umgebungsvariable setzen.")
            
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        self.sheets_manager = GoogleSheetsManager()
        
        self.summary_generator = SummaryGenerator()
        
        self.application = Application.builder().token(self.token).build()
        
        # +++ NEUER TEIL: GEMINI INITIALISIERUNG +++
        self.gemini_model = None # Standardmäßig deaktiviert
        try:
            project_id = os.getenv('GOOGLE_PROJECT_ID')
            if not project_id:
                logger.warning("GOOGLE_PROJECT_ID nicht gefunden. Text-Verfeinerung wird deaktiviert.")
            else:
                # Initialisiert die Verbindung zu Vertex AI. Nutzt die vorhandenen Service-Account-Credentials.
                vertexai.init(project=project_id, location="europe-west1") 
                self.gemini_model = GenerativeModel("gemini-1.0-pro") # Lädt das Gemini-Modell
                logger.info("✅ Vertex AI (Gemini) erfolgreich initialisiert.")
        except Exception as e:
            logger.error(f"FEHLER bei der Initialisierung von Vertex AI: {e}. Text-Verfeinerung ist deaktiviert.")
            self.gemini_model = None
        # +++ ENDE DES NEUEN TEILS +++
        
        self._register_handlers()
    
    def _register_handlers(self):
        """Registriert alle Bot-Handler"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ... (Diese Methode bleibt unverändert)
        welcome_message = """
🎉 Willkommen beim Tochter-Erinnerungen Bot! 🎉

Dieser Bot hilft dir dabei, die schönsten und lustigsten Momente mit deiner Tochter festzuhalten.

📝 **So funktioniert's:**
• Sende mir eine Sprachnachricht mit einer Erinnerung
• Ich transkribiere sie und mache sie schöner
• Alles wird automatisch mit Datum gespeichert

Sende einfach eine Sprachnachricht, um zu beginnen! 🎤
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ... (Diese Methode bleibt unverändert)
        help_message = """
📖 **Hilfe - Tochter-Erinnerungen Bot**

🎤 **Sprachnachrichten senden:**
Sende einfach eine Sprachnachricht mit einer Erinnerung an deine Tochter. Der Bot wird:
1. Die Nachricht transkribieren
2. Den Text stilistisch verbessern
3. Mit Datum in der Google-Tabelle speichern

📊 **Verfügbare Befehle:**
• `/start` - Bot starten und Willkommensnachricht
• `/help` - Diese Hilfe anzeigen
        """
        await update.message.reply_text(help_message)
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verarbeitet eingehende Sprachnachrichten"""
        # Wir rufen hier nicht mehr _initialize_sheets auf, das passiert jetzt im sheets_manager
        try:
            processing_msg = await update.message.reply_text("🎤 Verarbeite deine Sprachnachricht...")
            voice = update.message.voice
            logger.info(f"Sprachnachricht erhalten: {voice.duration}s, {voice.file_size} bytes")
            
            # ... (Der Rest der Methode bis zum Aufruf von _save_to_sheets bleibt unverändert)
            
            await processing_msg.edit_text("📥 Lade Sprachnachricht herunter...")
            voice_file = await voice.get_file()
            voice_data = BytesIO()
            await voice_file.download_to_memory(voice_data)
            voice_data.seek(0)
            
            await processing_msg.edit_text("🎯 Transkribiere Sprachnachricht...")
            transcript = await self._transcribe_audio(voice_data)
            
            if not transcript:
                await processing_msg.edit_text("❌ Entschuldigung, ich konnte die Sprachnachricht nicht verstehen.")
                return
            
            await processing_msg.edit_text("✨ Bereite Text auf...")
            enhanced_text = await self._enhance_text(transcript)
            
            berlin_tz = pytz.timezone("Europe/Berlin")
            now_berlin = datetime.now(berlin_tz)

            await processing_msg.edit_text("💾 Speichere Erinnerung...")
            # Der sheets_manager wird jetzt beim Start initialisiert
            success = await self.sheets_manager.save_memory(transcript, enhanced_text)            
            
            if success:
                response_message = f"""✅ **Erinnerung erfolgreich gespeichert!**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

📅 **Gespeichert am:** {now_berlin.strftime("%d.%m.%Y um %H:%M Uhr")}"""
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
            else:
                response_message = f"""⚠️ **Transkription erfolgreich, aber Speichern fehlgeschlagen**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

❌ **Hinweis:** Die Erinnerung konnte nicht in der Google-Tabelle gespeichert werden. Prüfe die Logs in Render."""
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Fehler bei Sprachnachricht-Verarbeitung: {e}", exc_info=True)
            await update.message.reply_text("❌ Ein unerwarteter Fehler ist aufgetreten.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # ... (Diese Methode bleibt unverändert)
        await update.message.reply_text("📝 Ich verstehe nur Sprachnachrichten! 🎤")
    
    async def _transcribe_audio(self, audio_data: BytesIO) -> Optional[str]:
        # ... (Diese Methode bleibt unverändert)
        try:
            speech_config = speechsdk.SpeechConfig(subscription=self.azure_speech_key, region=self.azure_speech_region)
            speech_config.speech_recognition_language="de-DE"

            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg_file:
                tmp_ogg_file.write(audio_data.getvalue())
                tmp_ogg_path = tmp_ogg_file.name

            audio = AudioSegment.from_ogg(tmp_ogg_path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav_file:
                audio.export(tmp_wav_file.name, format="wav")
                tmp_wav_path = tmp_wav_file.name

            audio_config = speechsdk.AudioConfig(filename=tmp_wav_path)
            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            result = speech_recognizer.recognize_once_async().get()

            os.remove(tmp_ogg_path)
            os.remove(tmp_wav_path)

            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                return result.text.strip()
            return None
        except Exception as e:
            logger.error(f"Fehler bei Azure Transkription: {e}", exc_info=True)
            return None
    
    # +++ ERSETZTE METHODE FÜR GEMINI +++
    async def _enhance_text(self, text: str) -> str:
        """Verbessert den transkribierten Text stilistisch mit Google Gemini."""
        if not self.gemini_model:
            logger.warning("Text-Verbesserung übersprungen, da das Gemini-Modell nicht initialisiert wurde.")
            return text

        try:
            prompt = f"""
            Du bist ein liebevoller und kreativer Assistent, der dabei hilft, die Erinnerungen eines Vaters an seine Tochter festzuhalten.
            Deine Aufgabe ist es, das folgende, direkt transkribierte Diktat in einen flüssigen, herzerwärmenden und gut lesbaren Text umzuwandeln.
            Korrigiere Grammatik- und Flüchtigkeitsfehler, aber bewahre den ursprünglichen Sinn und die Emotionen.
            Formuliere es so, als würde der Vater die Erinnerung in ein Tagebuch schreiben.
            Gib NUR den überarbeiteten Text zurück, ohne zusätzliche Einleitungen oder Kommentare wie "Hier ist der überarbeitete Text:".

            Original-Transkript:
            "{text}"
            """
            
            # Die `generate_content` Methode ist asynchron in neueren Versionen, aber wir rufen sie hier synchron auf.
            # Für eine vollständig asynchrone Anwendung könnte man `generate_content_async` verwenden.
            response = self.gemini_model.generate_content(prompt)
            enhanced_text = response.text.strip()
            
            logger.info("✅ Text erfolgreich mit Gemini verbessert.")
            return enhanced_text if enhanced_text else text

        except Exception as e:
            logger.error(f"FEHLER bei der Text-Verbesserung mit Gemini: {e}", exc_info=True)
            return text # Im Fehlerfall geben wir den Originaltext zurück

    async def _save_to_sheets(self, original_text: str, enhanced_text: str) -> bool:
        """Speichert die Erinnerung in Google Sheets. Die Initialisierung erfolgt jetzt im Manager selbst."""
        try:
            # Die Initialisierung wird jetzt intern im Manager gehandhabt, falls nötig.
            return await self.sheets_manager.save_memory(original_text, enhanced_text)
        except Exception as e:
            logger.error(f"Fehler beim Aufruf von save_memory: {e}", exc_info=True)
            return False

    async def run(self):
        """Startet den Bot im Polling-Modus. Diese Methode ist jetzt asynchron."""
        logger.info("Bot wird im Polling-Modus gestartet...")
        # run_polling ist eine asynchrone, blockierende Operation
        await self.application.run_polling()
