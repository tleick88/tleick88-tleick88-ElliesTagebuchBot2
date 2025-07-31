# telegram_bot.py - Finale, stabile Version mit Groq und Autor-Fix

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
from groq import Groq

from google_sheets_manager import GoogleSheetsManager
from summary_generator import SummaryGenerator

load_dotenv()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

class TochterErinnerungenBot:
    def __init__(self):
        """Initialisiert den Bot und seine Komponenten synchron."""
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN nicht gefunden!")

        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        self.sheets_manager = GoogleSheetsManager()
        self.summary_generator = SummaryGenerator()
        self.application = Application.builder().token(self.token).build()
        self.application.post_init = self.post_init_async

        # GROQ INITIALISIERUNG
        self.groq_client = None
        try:
            groq_api_key = os.getenv('GROQ_API_KEY')
            if not groq_api_key:
                logger.warning("GROQ_API_KEY nicht gefunden. Text-Verfeinerung wird deaktiviert.")
            else:
                self.groq_client = Groq(api_key=groq_api_key)
                logger.info("✅ Groq Client erfolgreich initialisiert.")
        except Exception as e:
            logger.error(f"FEHLER bei der Initialisierung von Groq: {e}. Text-Verfeinerung ist deaktiviert.")
        
        self._register_handlers()

    async def post_init_async(self, application: Application):
        """Wird nach der Initialisierung der Application ausgeführt, um Sheets zu verbinden."""
        logger.info("Führe Post-Initialisierungs-Aufgaben aus (Google Sheets)...")
        is_sheets_ok = await self.sheets_manager.initialize()
        if not is_sheets_ok:
            logger.critical("KRITISCHER FEHLER: Google Sheets konnte nicht initialisiert werden.")
        else:
            logger.info("✅ Post-Initialisierung (Google Sheets) erfolgreich abgeschlossen.")

    def _register_handlers(self):
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🎉 Willkommen! Sende eine Sprachnachricht, um eine Erinnerung zu speichern. 🎤")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Sende eine Sprachnachricht. Ich transkribiere sie, verbessere den Text und speichere alles in Google Sheets.")

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # +++ DER FIX: 'user' hier definieren +++
        user = update.message.from_user
        
        try:
            author_name = user.first_name
            
            processing_msg = await update.message.reply_text("🎤 Verarbeite deine Sprachnachricht...")
            voice = update.message.voice
            
            await processing_msg.edit_text("📥 Lade herunter...")
            voice_file = await voice.get_file()
            voice_data = BytesIO()
            await voice_file.download_to_memory(voice_data)
            voice_data.seek(0)
            
            await processing_msg.edit_text("🎯 Transkribiere...")
            transcript = await self._transcribe_audio(voice_data)
            if not transcript:
                await processing_msg.edit_text("❌ Konnte nichts verstehen.")
                return
            
            await processing_msg.edit_text("✨ Bereite Text auf...")
            enhanced_text = await self._enhance_text(transcript)
            
            await processing_msg.edit_text("💾 Speichere...")
            success = await self.sheets_manager.save_memory(transcript, enhanced_text, author_name)
            
            if success:
                response_message = f"✅ **Erinnerung gespeichert!**\n\n✨ **Version:**\n{enhanced_text}"
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
            else:
                await processing_msg.edit_text("⚠️ Speichern fehlgeschlagen. Transkription war: " + transcript)
        except Exception as e:
            logger.error(f"Fehler in handle_voice_message: {e}", exc_info=True)
            await update.message.reply_text("❌ Ein unerwarteter Fehler ist aufgetreten.")

    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📝 Ich verstehe nur Sprachnachrichten! 🎤")

    async def _transcribe_audio(self, audio_data: BytesIO) -> Optional[str]:
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
            return result.text.strip() if result.reason == speechsdk.ResultReason.RecognizedSpeech else None
        except Exception as e:
            logger.error(f"Fehler bei Azure Transkription: {e}", exc_info=True)
            return None

    async def _enhance_text(self, text: str) -> str:
        if not self.groq_client:
            logger.warning("Text-Verbesserung übersprungen, da Groq-Client nicht initialisiert.")
            return text
        try:
            prompt = f"""Du bist ein liebevoller Assistent, der hilft, Erinnerungen eines Elternteils an seine Tochter festzuhalten. Wandle das folgende Diktat in einen flüssigen, herzerwärmenden Tagebucheintrag um. Korrigiere Fehler, aber bewahre den Sinn. Gib NUR den fertigen Text zurück. Original-Transkript: "{text}" """
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
            )
            enhanced_text = chat_completion.choices[0].message.content.strip()
            logger.info("✅ Text erfolgreich mit Groq/Llama3 verbessert.")
            return enhanced_text if enhanced_text else text
        except Exception as e:
            logger.error(f"FEHLER bei der Text-Verbesserung mit Groq: {e}", exc_info=True)
            return text

    def run(self):
        logger.info("Starte run_polling...")
        self.application.run_polling()
