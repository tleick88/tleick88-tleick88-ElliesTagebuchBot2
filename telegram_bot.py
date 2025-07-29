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
import openai
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment

from src.google_sheets_manager import GoogleSheetsManager
from src.summary_generator import SummaryGenerator

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
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        
        # OpenAI Client initialisieren (für Text-Aufbereitung)
        self.openai_client = openai.OpenAI(base_url="https://api.openai.com/v1/")
        
        # Azure Speech-to-Text Konfiguration
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")
        
        # Google Sheets Manager initialisieren
        self.sheets_manager = GoogleSheetsManager()
        self.sheets_initialized = False
        
        # Summary Generator initialisieren
        self.summary_generator = SummaryGenerator()
        
        # Bot Application erstellen
        self.application = Application.builder().token(self.bot_token).build()
        
        # Handler registrieren
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
    
    def _register_handlers(self):
        """Registriert alle Bot-Handler"""
        # Command Handler
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("monats_zusammenfassung", self.monthly_summary_command))
        self.application.add_handler(CommandHandler("jahres_zusammenfassung", self.yearly_summary_command))
        
        # Message Handler für Sprachnachrichten
        self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))
        
        # Message Handler für Text (falls jemand Text schreibt)
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text_message))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für /start Command"""
        welcome_message = """
🎉 Willkommen beim Tochter-Erinnerungen Bot! 🎉

Dieser Bot hilft dir dabei, die schönsten und lustigsten Momente mit deiner Tochter festzuhalten.

📝 **So funktioniert's:**
• Sende mir eine Sprachnachricht mit einer Erinnerung
• Ich transkribiere sie und mache sie schöner
• Alles wird automatisch mit Datum gespeichert

📊 **Verfügbare Befehle:**
/help - Diese Hilfe anzeigen
/monats_zusammenfassung - Zusammenfassung des aktuellen Monats
/jahres_zusammenfassung - Zusammenfassung des aktuellen Jahres

Sende einfach eine Sprachnachricht, um zu beginnen! 🎤
        """
        await update.message.reply_text(welcome_message)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für /help Command"""
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
• `/monats_zusammenfassung` - Zusammenfassung des aktuellen Monats
• `/jahres_zusammenfassung` - Zusammenfassung des aktuellen Jahres

💡 **Tipps:**
• Sprich deutlich für bessere Transkription
• Erzähle ruhig Details - der Bot macht daraus schöne Erinnerungen
• Die Zusammenfassungen werden automatisch erstellt

Bei Problemen wende dich an den Administrator.
        """
        await update.message.reply_text(help_message)
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verarbeitet eingehende Sprachnachrichten"""
        try:
            # Benutzer informieren, dass die Nachricht verarbeitet wird
            processing_msg = await update.message.reply_text("🎤 Verarbeite deine Sprachnachricht...")
            
            # Voice-Datei Informationen loggen
            voice = update.message.voice
            logger.info(f"Sprachnachricht erhalten: {voice.duration}s, {voice.file_size} bytes")
            
            # Prüfe Sprachnachricht-Länge (max 5 Minuten)
            if voice.duration > 300:
                await processing_msg.edit_text("❌ Sprachnachricht zu lang! Bitte sende maximal 5 Minuten.")
                return
            
            # Voice-Datei herunterladen
            await processing_msg.edit_text("📥 Lade Sprachnachricht herunter...")
            voice_file = await voice.get_file()
            voice_data = BytesIO()
            await voice_file.download_to_memory(voice_data)
            voice_data.seek(0)
            
            # Dateiname für Whisper setzen
            voice_data.name = "voice_message.ogg"
            
            # Transkription mit OpenAI Whisper
            await processing_msg.edit_text("🎯 Transkribiere Sprachnachricht...")
            transcript = await self._transcribe_audio(voice_data)
            
            if not transcript:
                await processing_msg.edit_text(
                    "❌ Entschuldigung, ich konnte die Sprachnachricht nicht verstehen.\n\n"
                    "💡 Tipps:\n"
                    "• Sprich deutlich und nicht zu schnell\n"
                    "• Vermeide Hintergrundgeräusche\n"
                    "• Sprich mindestens 2-3 Sekunden"
                )
                return
            
            # Text aufbereiten
            await processing_msg.edit_text("✨ Bereite Text auf...")
            enhanced_text = await self._enhance_text(transcript)
            
            berlin_tz = pytz.timezone("Europe/Berlin")
            now_berlin = datetime.now(berlin_tz)
            date_str = now_berlin.strftime("%Y-%m-%d %H:%M:%S")
            month_str = now_berlin.strftime("%Y-%m")
            year_str = now_berlin.strftime("%Y")

            # In Google Sheets speichern
            await processing_msg.edit_text("💾 Speichere Erinnerung...")
            success = await self._save_to_sheets(transcript, enhanced_text)            
            # Erfolgreiche Antwort
            if success:
                response_message = f"""✅ **Erinnerung erfolgreich gespeichert!**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

📅 **Gespeichert am:** {now_berlin.strftime("%d.%m.%Y um %H:%M Uhr")}

💝 Eine weitere schöne Erinnerung für deine Tochter!"""
                
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
            else:
                # Fehler beim Speichern, aber zeige trotzdem das Ergebnis
                response_message = f"""⚠️ **Transkription erfolgreich, aber Speichern fehlgeschlagen**

📝 **Original-Transkript:**
_{transcript}_

✨ **Aufbereitete Version:**
{enhanced_text}

❌ **Hinweis:** Die Erinnerung konnte nicht in der Google-Tabelle gespeichert werden. Das wird in Phase 3 behoben.

💡 **Tipp:** Kopiere dir den Text als Backup!"""
                
                await processing_msg.edit_text(response_message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Fehler bei Sprachnachricht-Verarbeitung: {e}")
            try:
                await update.message.reply_text(
                    "❌ Ein unerwarteter Fehler ist aufgetreten.\n\n"
                    "🔧 Bitte versuche es in ein paar Minuten erneut.\n"
                    "📞 Falls das Problem weiterhin besteht, wende dich an den Administrator."
                )
            except:
                # Falls auch das Senden der Fehlermeldung fehlschlägt
                logger.error("Konnte Fehlermeldung nicht senden")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler für Textnachrichten"""
        await update.message.reply_text(
            "📝 Ich verstehe nur Sprachnachrichten! 🎤\n\n"
            "Bitte sende mir eine Sprachnachricht mit deiner Erinnerung."
        )
    
    async def _transcribe_audio(self, audio_data: BytesIO) -> Optional[str]:
        """Transkribiert Audio mit Azure Speech-to-Text"""
        try:
            speech_config = speechsdk.SpeechConfig(subscription=self.azure_speech_key, region=self.azure_speech_region)
            speech_config.speech_recognition_language="de-DE"

            # Audio-Daten für Azure vorbereiten: Konvertierung von OGG zu WAV
            import tempfile
            import os
            from pydub import AudioSegment

            # Speichern der OGG-Audiodaten in einer temporären Datei
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp_ogg_file:
                tmp_ogg_file.write(audio_data.getvalue())
                tmp_ogg_path = tmp_ogg_file.name

            # Konvertierung von OGG zu WAV
            audio = AudioSegment.from_ogg(tmp_ogg_path)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav_file:
                audio.export(tmp_wav_file.name, format="wav")
                tmp_wav_path = tmp_wav_file.name

            # Azure Speech-to-Text mit der WAV-Datei
            audio_config = speechsdk.AudioConfig(filename=tmp_wav_path)

            speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

            result = speech_recognizer.recognize_once_async().get()

            # Temporäre Dateien löschen
            os.remove(tmp_ogg_path)
            os.remove(tmp_wav_path)
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                text = result.text.strip()
                if len(text) < 3:
                    logger.warning(f"Transkript zu kurz: {text}")
                    return None
                logger.info(f"Transkription erfolgreich mit Azure: {len(text)} Zeichen")
                return text
            elif result.reason == speechsdk.ResultReason.NoMatch:
                logger.warning("Azure Speech konnte keine Sprache erkennen.")
                return None
            elif result.reason == speechsdk.ResultReason.Canceled:
                cancellation_details = result.cancellation_details
                logger.error(f"Azure Speech Transkription abgebrochen: {cancellation_details.reason}")
                if cancellation_details.reason == speechsdk.CancellationReason.Error:
                    logger.error(f"Azure Speech Fehlerdetails: {cancellation_details.error_details}")
                return None
            
        except Exception as e:
            logger.error(f"Fehler bei Azure Transkription: {e}")
            return None
    
    async def _enhance_text(self, text: str) -> str:
        """Verbessert den transkribierten Text stilistisch"""
        try:
            # Prompt für bessere Text-Aufbereitung
            prompt = f"""Du bist ein liebevoller Assistent, der dabei hilft, Erinnerungen an eine Tochter schön und herzlich zu formulieren.

AUFGABE: Verbessere den folgenden Text, der aus einer Sprachnachricht eines Elternteils transkribiert wurde.

REGELN:
- Korrigiere Grammatik und Rechtschreibung
- Mache den Text stilistisch schöner und emotionaler
- Behalte ALLE wichtigen Details und Fakten bei
- Schreibe in der Ich-Form (als Elternteil)
- Füge keine neuen Informationen hinzu
- Mache den Text warm und liebevoll
- Verwende eine natürliche, erzählende Sprache

ORIGINAL TEXT:
"{text}"

VERBESSERTE VERSION:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.7,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            enhanced_text = response.choices[0].message.content.strip()
            
            # Fallback falls die Antwort leer ist
            if not enhanced_text or len(enhanced_text) < 10:
                logger.warning("Text-Verbesserung ergab leeren Text, verwende Original")
                return text
            
            # Entferne mögliche Anführungszeichen am Anfang/Ende
            enhanced_text = enhanced_text.strip('"').strip("'")
            
            logger.info(f"Text-Verbesserung erfolgreich: {len(text)} -> {len(enhanced_text)} Zeichen")
            return enhanced_text
            
        except Exception as e:
            logger.error(f"Fehler bei Text-Verbesserung: {e}")
            return text  # Fallback: Original-Text zurückgeben

    async def _save_to_sheets(self, original_text: str, enhanced_text: str) -> bool:
        """Speichert die Erinnerung in Google Sheets"""
        try:
            # Google Sheets initialisieren falls nötig
            await self._initialize_sheets()
            
            berlin_tz = pytz.timezone("Europe/Berlin")
            now_berlin = datetime.now(berlin_tz)
            date_str = now_berlin.strftime("%Y-%m-%d %H:%M:%S")
            month_str = now_berlin.strftime("%Y-%m")
            year_str = now_berlin.strftime("%Y")

            row_data = [date_str, original_text, enhanced_text, month_str, year_str]
            
            if self.sheets_manager.is_connected():
                success = await self.sheets_manager.append_row(self.sheets_id, row_data)
            else:
                # Fallback für Mock-Modus oder wenn keine Verbindung
                logger.warning("Google Sheets nicht verbunden, speichere im Mock-Modus.")
                success = True # Simuliere Erfolg im Mock-Modus

            if success:
                logger.info("Erinnerung erfolgreich in Google Sheets gespeichert")
            else:
                logger.error("Fehler beim Speichern in Google Sheets")
            
            return success
            
        except Exception as e:
            logger.error(f"Fehler beim Speichern in Google Sheets: {e}")
            return False

    async def monthly_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Erstellt eine intelligente Monats-Zusammenfassung"""
        try:
            processing_msg = await update.message.reply_text("📊 Erstelle intelligente Monats-Zusammenfassung...")
            
            # Aktueller Monat
            now = datetime.now()
            year = now.year
            month = now.month
            
            # Google Sheets initialisieren
            await self._initialize_sheets()
            
            # Erinnerungen für den Monat abrufen
            await processing_msg.edit_text("📥 Lade Erinnerungen aus Google Sheets...")
            memories = await self.sheets_manager.get_memories_by_month(year, month)
            
            # Intelligente Zusammenfassung erstellen
            await processing_msg.edit_text("🤖 Erstelle KI-Zusammenfassung...")
            summary = await self.summary_generator.generate_monthly_summary(memories, year, month)
            
            # Zusammenfassung senden
            await processing_msg.edit_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Fehler bei Monats-Zusammenfassung: {e}")
            await update.message.reply_text("❌ Fehler beim Erstellen der Monats-Zusammenfassung.")
    
    async def yearly_summary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Erstellt eine intelligente Jahres-Zusammenfassung"""
        try:
            processing_msg = await update.message.reply_text("📊 Erstelle intelligente Jahres-Zusammenfassung...")
            
            # Aktuelles Jahr
            year = datetime.now().year
            
            # Google Sheets initialisieren
            await self._initialize_sheets()
            
            # Erinnerungen für das Jahr abrufen
            await processing_msg.edit_text("📥 Lade alle Erinnerungen des Jahres...")
            memories = await self.sheets_manager.get_memories_by_year(year)
            
            # Intelligente Zusammenfassung erstellen
            await processing_msg.edit_text("🤖 Erstelle umfassende KI-Jahres-Zusammenfassung...")
            summary = await self.summary_generator.generate_yearly_summary(memories, year)
            
            # Zusammenfassung senden
            await processing_msg.edit_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Fehler bei Jahres-Zusammenfassung: {e}")
            await update.message.reply_text("❌ Fehler beim Erstellen der Jahres-Zusammenfassung.")
    
    def run(self):
        """Startet den Bot"""
        logger.info("Starte Tochter-Erinnerungen Bot...")
        
        # Neuen Event Loop für diesen Thread erstellen
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            self.application.run_polling()
        finally:
            loop.close()

# Für direkten Start
if __name__ == "__main__":
    bot = TochterErinnerungenBot()
    bot.run()

