# telegram_bot.py - Finale Version mit deaktivierten Zusammenfassungs-Befehlen

"""
Telegram Bot für Tochter-Erinnerungen
Verarbeitet Sprachnachrichten und speichert sie in Google Sheets
"""

import os
import logging
import asyncio
from datetime import datetime
import pytz
from typing import Optional
from io import BytesIO

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
# import openai # Auskommentiert, da wir es vorerst nicht nutzen
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

from google_sheets_manager import GoogleSheetsManager
from summary_generator import SummaryGenerator # Importieren wir weiterhin, auch wenn die Klasse leer ist

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
        
        # OpenAI Client ist jetzt deaktiviert, um den API-Key-Fehler zu vermeiden
        self.openai_client = None
        
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        self.sheets_manager = GoogleSheetsManager()
        self.sheets_initialized = False
        
        self.summary_generator = SummaryGenerator()
        
        self.application = Application.builder().token(self.token).build()
        
        self._register_handlers()
    
    async def _initialize_sheets(self):
        """Initialisiert Google Sheets falls noch nicht geschehen"""
        if not self.sheets_initialized:
            logger.info("Initialisiere Google Sheets...")
            self.sheets_initialized = await self.sheets_manager.initialize()
            if self.sheets_initialized:
                logger.info("✅ Google Sheets erfolgreich initialisiert")
            else:
                logger.warning("⚠️ Google Sheets Initialisierung fehlgeschlagen - verwende Mock-Modus")
    
    # --- HIER IST DIE ERSTE WICHTIGE ÄNDERUNG ---
    def _register_handlers(self):
        """Registriert alle Bot-Handler"""
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        
        # Die folgenden Handler sind jetzt auskommentiert und somit deaktiviert
        # self.application.add_handler(CommandHandler("monats_zusammenfassung", self.monthly_summary_command))
        # self.application.add_handler(CommandHandler("jahres_zusammenfassung", self.yearly_summary_command))
        
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für /start Command"""
        # Die Willkommensnachricht wird angepasst, um die deaktivierten Befehle nicht mehr anzuzeigen
        welcome_message = """
🎉 Willkommen beim Tochter-Erinnerungen Bot! 🎉

Dieser Bot hilft dir dabei, die schönsten und lustigsten Momente mit deiner Tochter festzuhalten.

📝 **So funktioniert's:**
• Sende mir eine Sprachnachricht mit einer Erinnerung
• Ich transkribiere sie und mache sie schöner
• Alles wird automatisch mit Datum gespeichert

Sende einfach eine Sprachnachricht, um zu beginnen! 🎤

(Die Zusammenfassungs-Funktionen sind zurzeit deaktiviert.)
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für /help Command"""
        help_message = """
📖 **Hilfe - Tochter-Erinnerungen Bot**

🎤 **Sprachnachrichten senden:**
Sende einfach eine Sprachnachricht mit einer Erinnerung an deine Tochter. Der Bot wird:
1. Die Nachricht transkribieren
2. Den Text stilistisch verbessern (falls aktiviert)
3. Mit Datum in der Google-Tabelle speichern

📊 **Verfügbare Befehle:**
• `/start` - Bot starten und Willkommensnachricht
• `/help` - Diese Hilfe anzeigen

(Die Zusammenfassungs-Funktionen sind zurzeit deaktiviert.)
        """
        await update.message.reply_text(help_message)
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verarbeitet eingehende Sprachnachrichten"""
        try:
            processing_msg = await update.message.reply_text("🎤 Verarbeite deine Sprachnachricht...")
            voice = update.message.voice
            logger.info(f"Sprachnachricht erhalten: {voice.duration}s, {voice.file_size} bytes")
            
            if voice.duration > 300:
                await processing_msg.edit_text("❌ Sprachnachricht zu lang! Bitte sende maximal 5 Minuten.")
                return
            
            await processing_msg.edit_text("📥 Lade Sprachnachricht herunter...")
            voice_file = await voice.get_file()
            voice_data = BytesIO()
            await voice_file.download_to_memory(voice_data)
            voice_data.seek(0)
            
            voice_data.name = "voice_message.ogg"
            
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
            success = await self._save_to_sheets(transcript, enhanced_text)            
            
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

❌ **Hinweis:** Die Erinnerung konnte nicht in der Google-Tabelle gespeichert werden."""
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Fehler bei Sprachnachricht-Verarbeitung: {e}", exc_info=True)
            await update.message.reply_text("❌ Ein unerwarteter Fehler ist aufgetreten.")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für Textnachrichten"""
        await update.message.reply_text("📝 Ich verstehe nur Sprachnachrichten! 🎤")
    
    async def _transcribe_audio(self, audio_data: BytesIO) -> Optional[str]:
        """Transkribiert Audio mit Azure Speech-to-Text"""
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
    
    # --- HIER IST DIE ZWEITE WICHTIGE ÄNDERUNG ---
    async def _enhance_text(self, text: str) -> str:
        """Verbessert den transkribierten Text stilistisch. Ist aktuell deaktiviert."""
        # Wenn der OpenAI-Client nicht initialisiert ist, geben wir den Originaltext zurück.
        if not self.openai_client:
            logger.info("OpenAI-Client nicht konfiguriert. Text-Verbesserung wird übersprungen.")
            return text
        
        # Der restliche Code wird nur ausgeführt, wenn der Client existiert.
        try:
            prompt = f"""Du bist ein liebevoller Assistent... (restlicher Prompt)"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7
            )
            enhanced_text = response.choices[0].message.content.strip().strip('"').strip("'")
            
            return enhanced_text if enhanced_text else text
            
        except Exception as e:
            logger.error(f"Fehler bei Text-Verbesserung: {e}", exc_info=True)
            return text

    async def _save_to_sheets(self, original_text: str, enhanced_text: str) -> bool:
        """Speichert die Erinnerung in Google Sheets"""
        try:
            await self._initialize_sheets()
            return await self.sheets_manager.save_memory(original_text, enhanced_text)
        except Exception as e:
            logger.error(f"Fehler beim Aufruf von save_memory: {e}", exc_info=True)
            return False

    # Die folgenden zwei Funktionen werden nicht mehr aufgerufen, da die Handler deaktiviert sind.
    # Wir können sie vorerst im Code belassen.
    async def monthly_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Diese Funktion ist zurzeit deaktiviert.")
    
    async def yearly_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Diese Funktion ist zurzeit deaktiviert.")
    
    # NEUE, KORREKTE VERSION
    def run(self):
        """Startet den Bot und führt ihn im Polling-Modus aus."""
        logger.info("Bot wird im Polling-Modus gestartet...")
        # Diese Methode startet das Polling und blockiert, bis der Bot gestoppt wird.
        self.application.run_polling()
un(self):
        """Diese Methode wird von main.py aufgerufen, um die Handler zu registrieren."""
        logger.info("Bot-Handler werden registriert...")
        pass
