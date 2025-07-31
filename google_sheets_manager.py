# google_sheets_manager.py - Für Render optimierte Version

import os
import logging
import json
from datetime import datetime
from typing import List, Dict, Any
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)

class GoogleSheetsManager:
    def __init__(self):
        self.client = None
        self.spreadsheet = None
        self.worksheet = None
        self.sheets_id = os.getenv('GOOGLE_SHEETS_ID')

    async def initialize(self) -> bool:
        """Initialisiert die Google Sheets Verbindung über eine einzige, robuste Methode."""
        if not self.sheets_id:
            logger.error("FEHLER: GOOGLE_SHEETS_ID ist nicht in den Umgebungsvariablen gesetzt!")
            return False
            
        try:
            self.client = await self._authenticate()
            if not self.client:
                logger.error("FEHLER: Google Sheets Authentifizierung fehlgeschlagen. Überprüfe die Credentials in Render.")
                return False

            self.spreadsheet = self.client.open_by_key(self.sheets_id)
            await self._setup_worksheet()
            logger.info("✅ Google Sheets erfolgreich initialisiert und verbunden.")
            return True
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"FEHLER: Spreadsheet mit der ID '{self.sheets_id}' nicht gefunden. Überprüfe die ID und die Freigabe für den Service Account.")
            return False
        except Exception as e:
            logger.error(f"FEHLER: Unerwarteter Fehler bei der Google Sheets Initialisierung: {e}", exc_info=True)
            return False

    async def _authenticate(self):
        """Authentifiziert sich bei der Google Sheets API über eine Secret File."""
        # Render stellt Secret Files unter /etc/secrets/<filename> bereit
        creds_path = '/etc/secrets/credentials.json'
        
        if not os.path.exists(creds_path):
            logger.error(f"FEHLER: Secret File nicht gefunden unter '{creds_path}'. Stelle sicher, dass sie in Render korrekt angelegt ist.")
            return None

        logger.info(f"Versuche Authentifizierung über Secret File '{creds_path}'.")
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            # gspread kann direkt mit dem Dateipfad arbeiten
            return gspread.service_account(filename=creds_path, scopes=scopes )
        except Exception as e:
            logger.error(f"FEHLER bei der Google-Authentifizierung mit der Secret File: {e}", exc_info=True)
            return None

    async def _setup_worksheet(self):
        """Richtet das Arbeitsblatt ein und stellt sicher, dass die Header existieren."""
        try:
            self.worksheet = self.spreadsheet.sheet1
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Standard-Arbeitsblatt 'Sheet1' nicht gefunden. Erstelle neues Blatt 'Erinnerungen'.")
            self.worksheet = self.spreadsheet.add_worksheet(title="Erinnerungen", rows="1000", cols="5")
        
        headers = self.worksheet.row_values(1)
        expected_headers = ["Datum", "Autor", "Original Text", "Aufbereiteter Text", "Monat", "Jahr"]
        if headers != expected_headers:
            logger.info("Header-Zeile fehlt oder ist inkorrekt. Erstelle sie neu.")
            # Leere die erste Zeile, bevor neue Header eingefügt werden, um Duplikate zu vermeiden
            self.worksheet.delete_rows(1)
            self.worksheet.insert_row(expected_headers, 1)

    async def save_memory(self, original_text: str, enhanced_text: str, author: str) -> bool:
        """Speichert eine Erinnerung inklusive des Autors in Google Sheets."""
        if not self.worksheet:
            logger.error("FEHLER: Speichern fehlgeschlagen, da kein aktives Worksheet vorhanden ist.")
            return False
            
        try:
            now = datetime.now()
            timestamp = now.strftime("%d.%m.%Y %H:%M:%S")
            month = now.strftime("%Y-%m")
            year = str(now.year)
            
            # Die neue Zeile enthält jetzt auch den Autorennamen
            row_data = [timestamp, author, original_text, enhanced_text, month, year]
            
            self.worksheet.append_row(row_data)
            logger.info(f"✅ Erinnerung von '{author}' erfolgreich in Google Sheets gespeichert.")
            return True
        except Exception as e:
            logger.error(f"FEHLER beim Speichern der Zeile in Google Sheets: {e}", exc_info=True)
            return False
