# In telegram_bot.py

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Verarbeitet eingehende Sprachnachrichten."""
        
        user = update.message.from_user
        # Sicherheitscheck für erlaubte IDs (falls konfiguriert)
        if self.allowed_ids and user.id not in self.allowed_ids:
            logger.warning(f"Unbefugter Zugriff von User-ID: {user.id} ({user.username})")
            await update.message.reply_text("Entschuldigung, dieser Bot ist privat.")
            return

        try:
            # +++ WICHTIG: Autor-Name hier definieren +++
            author_name = user.first_name 

            processing_msg = await update.message.reply_text("🎤 Verarbeite deine Sprachnachricht...")
            voice = update.message.voice
            logger.info(f"Sprachnachricht erhalten: {voice.duration}s, {voice.file_size} bytes")
            
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
            
            # +++ WICHTIG: Der korrigierte Aufruf +++
            success = await self.sheets_manager.save_memory(transcript, enhanced_text, author_name)            
            
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

