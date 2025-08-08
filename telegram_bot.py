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
                # +++ HIER IST DIE GEWÜNSCHTE ANTWORT-FORMATIERUNG +++
                berlin_tz = pytz.timezone("Europe/Berlin")
                now_berlin = datetime.now(berlin_tz)
                
                response_message = f"""✅ **Erinnerung von {author_name} erfolgreich gespeichert!**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

📅 **Gespeichert am:** {now_berlin.strftime("%d.%m.%Y um %H:%M Uhr")}"""
                
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
            else:
                # Die Fehlermeldung bleibt informativ
                response_message = f"""⚠️ **Transkription erfolgreich, aber Speichern fehlgeschlagen**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

❌ **Hinweis:** Die Erinnerung konnte nicht in der Google-Tabelle gespeichert werden. Prüfe die Logs in Render."""
                await processing_msg.edit_text(response_message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Fehler in handle_voice_message: {e}", exc_info=True)
            await update.message.reply_text("❌ Ein unerwarteter Fehler ist aufgetreten.")
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📝 Ich verstehe nur Sprachnachrichten! 🎤")

    async def _transcribe_audio(self, audio_data: BytesIO) -> Optional[str]:
        """
        Transkribiert eine Audiodatei mit Groq unter Verwendung des Whisper-Modells.
        """
        if not self.groq_client:
            logger.warning("Transkription übersprungen, da der Groq-Client nicht initialisiert wurde.")
            return None

        try:
            logger.info("Sende Audiodatei zur Transkription an Groq (Whisper)...")
            
            # Wichtig: Wir müssen sicherstellen, dass die BytesIO-Daten einen Dateinamen haben,
            # damit die Groq-API den Dateityp erkennen kann.
            audio_data.name = "voice_message.ogg"

            # Die Groq-API erwartet ein Tupel: (Dateiname, Audiodaten)
            transcription = self.groq_client.audio.transcriptions.create(
                file=(audio_data.name, audio_data.read()),
                model="whisper-large-v3",
                response_format="json", # Stellt sicher, dass wir eine saubere Antwort bekommen
                language="de" # Wichtig: Wir geben die Sprache an, um die Genauigkeit zu maximieren
            )

            logger.info("✅ Transkription von Groq erfolgreich erhalten.")
            return transcription.text.strip()

        except Exception as e:
            logger.error(f"Fehler bei der Transkription mjt Groq: {e}", exc_info=True)
            return None

    async def _enhance_text(self, text: str) -> str:
        if not self.groq_client:
            logger.warning("Text-Verbesserung übersprungen, da Groq-Client nicht initialisiert.")
            return text
        try:
            prompt = f"""**Anweisung:**
            Du bist ein Assistent, der einen deutschen Tagebucheintrag formuliert.
            Befolge diese Regeln strikt:
            1.  **SPRACHE:** Deine Antwort MUSS ausschließlich auf Deutsch sein. Antworte unter keinen Umständen auf Englisch.
            2.  **INHALT:** Du erhältst einen Rohtext, der wie ein spontanes Gespräch, Transkript oder Mitschnitt wirkt.
Schreibe daraus einen flüssigen, zusammenhängenden Fließtext in lebendigem Romanstil.

Anforderungen:
	1.	Behalte den Inhalt und die Kernaussagen vollständig bei.
	2.	Glätte Formulierungen, entferne unnötige Wiederholungen und fasse abgehackte Sätze sinnvoll zusammen.
	3.	Strukturiere Dialoge sauber mit korrekten deutschen Anführungszeichen („…“) und füge Sprecherhinweise ein, wo passend.
	4.	Verwende bildhafte, abwechslungsreiche Sprache und ergänze, wo stimmig, kurze emotionale oder situative Beschreibungen.
	5.	Halte Erzählperspektive, Rechtschreibung und Grammatik durchgehend korrekt.
            3.  **FORMAT:** Gib NUR den reinen, verbesserten Text des Tagebucheintrags zurück. KEINE Einleitungen, KEINE Kommentare, KEINE Anführungszeichen am Anfang oder Ende. Schweife nicht aus!

            **Original-Transkript:**"{text}" """
            chat_completion = self.groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.2
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
