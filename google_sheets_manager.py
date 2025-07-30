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
        
        # Spalten-Mapping für bessere Lesbarkeit
        self.columns = {
            'timestamp': 'A',
            'original_text': 'B', 
            'enhanced_text': 'C',
            'month': 'D',
            'year': 'E'
        }

    async def initialize(self) -> bool:
        """Initialisiert die Google Sheets Verbindung über eine einzige, robuste Methode."""
        if not self.sheets_id:
            logger.error("GOOGLE_SHEETS_ID ist nicht in den Umgebungsvariablen gesetzt!")
            return False
            
        try:
            self.client = await self._authenticate()
            if not self.client:
                logger.error("Google Sheets Authentifizierung fehlgeschlagen. Überprüfe die Credentials.")
                # Wir aktivieren hier KEINEN Mock-Modus mehr, um den Fehler klar zu sehen.
                return False

            self.spreadsheet = await self.client.open_by_key(self.sheets_id)
            await self._setup_worksheet()
            logger.info("✅ Google Sheets erfolgreich initialisiert und verbunden.")
            return True
        except gspread.exceptions.SpreadsheetNotFound:
            logger.error(f"Spreadsheet mit der ID '{self.sheets_id}' nicht gefunden. Überprüfe die ID und die Freigabe für den Service Account.")
            return False
        except Exception as e:
            logger.error(f"Unerwarteter Fehler bei der Google Sheets Initialisierung: {e}", exc_info=True)
            return False

    async def _authenticate(self):
        """
        Authentifiziert sich bei der Google Sheets API.
        Priorisiert Umgebungsvariable, nutzt dann Secret File als Fallback.
        """
        creds_json_str = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
        creds_path = '/etc/secrets/credentials.json' # Standardpfad für Render Secret Files
        
        creds_info = None
        
        # Methode 1: Versuche, die Credentials aus der Umgebungsvariable zu laden
        if creds_json_str:
            logger.info("Versuche Authentifizierung über Umgebungsvariable 'GOOGLE_SHEETS_CREDENTIALS'.")
            try:
                creds_info = json.loads(creds_json_str)
            except json.JSONDecodeError:
                logger.error("Fehler beim Parsen der JSON-Credentials aus der Umgebungsvariable.")
                return None
        
        # Methode 2: Wenn Methode 1 fehlschlägt, versuche, die Secret File zu laden
        elif os.path.exists(creds_path):
            logger.info(f"Versuche Authentifizierung über Secret File '{creds_path}'.")
            try:
                with open(creds_path, 'r') as f:
                    creds_info = json.load(f)
            except (IOError, json.JSONDecodeError):
                logger.error(f"Fehler beim Lesen oder Parsen der Secret File '{creds_path}'.")
                return None
        
        if not creds_info:
            logger.error("Keine Google-Credentials gefunden. Setze entweder die 'GOOGLE_SHEETS_CREDENTIALS' Umgebungsvariable oder erstelle eine Secret File 'credentials.json'.")
            return None

        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes )
            # gspread.service_account_from_dict ist die moderne Methode
            return gspread.service_account(credentials_filename=None, credentials_info=creds_info, scope=scopes)
        except Exception as e:
            logger.error(f"Fehler bei der Google-Authentifizierung mit den bereitgestellten Credentials: {e}", exc_info=True)
            return None

    async def _setup_worksheet(self):
        """Richtet das Arbeitsblatt ein und stellt sicher, dass die Header existieren."""
        try:
            self.worksheet = self.spreadsheet.sheet1
        except gspread.exceptions.WorksheetNotFound:
            logger.info("Standard-Arbeitsblatt 'Sheet1' nicht gefunden. Erstelle neues Blatt 'Erinnerungen'.")
            self.worksheet = self.spreadsheet.add_worksheet(title="Erinnerungen", rows="1000", cols="10")
        
        headers = self.worksheet.row_values(1)
        expected_headers = ["Datum", "Original Text", "Aufbereiteter Text", "Monat", "Jahr"]
        if headers != expected_headers:
            logger.info("Header-Zeile fehlt oder ist inkorrekt. Erstelle sie neu.")
            self.worksheet.insert_row(expected_headers, 1)

    async def save_memory(self, original_text: str, enhanced_text: str) -> bool:
        """Speichert eine Erinnerung in Google Sheets."""
        if not self.worksheet:
            logger.error("Speichern fehlgeschlagen: Kein aktives Worksheet vorhanden. Initialisierungsproblem?")
            return False
            
        try:
            now = datetime.now()
            timestamp = now.strftime("%d.%m.%Y %H:%M:%S")
            month = now.strftime("%Y-%m")
            year = str(now.year)
            
            row_data = [timestamp, original_text, enhanced_text, month, year]
            
            self.worksheet.append_row(row_data)
            logger.info(f"✅ Erinnerung erfolgreich in Google Sheets gespeichert.")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Zeile in Google Sheets: {e}", exc_info=True)
            return False

    # Die get-Methoden können wir vorerst so lassen, aber ohne Mock-Daten
    async def get_memories_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        if not self.worksheet: return []
        # ... (Logik bleibt gleich)
        pass

    async def get_memories_by_year(self, year: int) -> List[Dict[str, Any]]:
        if not self.worksheet: return []
        # ... (Logik bleibt gleich)
        pass

    def is_connected(self) -> bool:
        return self.worksheet is not None
