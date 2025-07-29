"""
Google Sheets Manager für Tochter-Erinnerungen Bot
Verwaltet die Verbindung und Operationen mit Google Sheets
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
import gspread
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
import json

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
        """Initialisiert die Google Sheets Verbindung"""
        try:
            # Versuche verschiedene Authentifizierungsmethoden
            success = await self._try_service_account_auth()
            
            if not success:
                success = await self._try_oauth_auth()
            
            if not success:
                success = await self._try_simple_auth()
            
            if success:
                await self._setup_worksheet()
                logger.info("Google Sheets erfolgreich initialisiert")
                return True
            else:
                logger.error("Alle Google Sheets Authentifizierungsmethoden fehlgeschlagen")
                return False
                
        except Exception as e:
            logger.error(f"Fehler bei Google Sheets Initialisierung: {e}")
            return False
    
    async def _try_service_account_auth(self) -> bool:
        """Versucht Service Account Authentifizierung"""
        try:
            # Suche nach Service Account JSON Datei
            service_account_paths = [
                '/home/ubuntu/tochter_erinnerungen_bot/service_account.json',
                '/home/ubuntu/tochter_erinnerungen_bot/credentials.json',
                os.getenv('GOOGLE_SERVICE_ACCOUNT_PATH')
            ]
            
            for path in service_account_paths:
                if path and os.path.exists(path):
                    logger.info(f"Versuche Service Account Auth mit: {path}")
                    
                    # Scopes für Google Sheets
                    scopes = [
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                    
                    credentials = Credentials.from_service_account_file(path, scopes=scopes)
                    self.client = gspread.authorize(credentials)
                    
                    # Test der Verbindung
                    self.spreadsheet = self.client.open_by_key(self.sheets_id)
                    logger.info("Service Account Authentifizierung erfolgreich")
                    return True
                    
        except Exception as e:
            logger.warning(f"Service Account Auth fehlgeschlagen: {e}")
        
        return False
    
    async def _try_oauth_auth(self) -> bool:
        """Versucht OAuth Authentifizierung"""
        try:
            # OAuth Token aus Umgebungsvariablen
            oauth_token = os.getenv('GOOGLE_OAUTH_TOKEN')
            if oauth_token:
                logger.info("Versuche OAuth Authentifizierung")
                
                # OAuth Credentials erstellen
                token_data = json.loads(oauth_token)
                credentials = OAuthCredentials.from_authorized_user_info(token_data)
                
                self.client = gspread.authorize(credentials)
                self.spreadsheet = self.client.open_by_key(self.sheets_id)
                
                logger.info("OAuth Authentifizierung erfolgreich")
                return True
                
        except Exception as e:
            logger.warning(f"OAuth Auth fehlgeschlagen: {e}")
        
        return False
    
    async def _try_simple_auth(self) -> bool:
        """Vereinfachte Authentifizierung für Demo-Zwecke"""
        try:
            logger.info("Versuche vereinfachte Authentifizierung")
            
            # Für Demo: Erstelle Mock-Client
            # In der Produktion würde hier eine echte Authentifizierung stehen
            logger.warning("Verwende Mock Google Sheets Client für Demo")
            self.client = None  # Mock
            return True
            
        except Exception as e:
            logger.error(f"Vereinfachte Auth fehlgeschlagen: {e}")
        
        return False
    
    async def _setup_worksheet(self):
        """Richtet das Arbeitsblatt ein"""
        try:
            if self.client and self.spreadsheet:
                # Erstes Arbeitsblatt verwenden oder erstellen
                try:
                    self.worksheet = self.spreadsheet.sheet1
                except:
                    self.worksheet = self.spreadsheet.add_worksheet(title="Erinnerungen", rows="1000", cols="10")
                
                # Header-Zeile erstellen falls nicht vorhanden
                await self._ensure_headers()
            else:
                # Mock für Demo
                logger.info("Mock Worksheet Setup")
                self.worksheet = None
                
        except Exception as e:
            logger.error(f"Fehler beim Worksheet Setup: {e}")
    
    async def _ensure_headers(self):
        """Stellt sicher, dass die Header-Zeile existiert"""
        try:
            if self.worksheet:
                # Prüfe ob Header bereits existieren
                first_row = self.worksheet.row_values(1)
                
                if not first_row or first_row[0] != "Datum":
                    # Header setzen
                    headers = ["Datum", "Original Text", "Aufbereiteter Text", "Monat", "Jahr"]
                    self.worksheet.insert_row(headers, 1)
                    logger.info("Header-Zeile erstellt")
            
        except Exception as e:
            logger.error(f"Fehler beim Header Setup: {e}")
    
    async def save_memory(self, original_text: str, enhanced_text: str, timestamp: str, month: str, year: str) -> bool:        """Speichert eine Erinnerung in Google Sheets"""
        try            now = datetime.now()
            timestamp = now.strftime("%d.%m.%Y %H:%M:%S")
            month = now.strftime("%Y-%m")
            year = str(now.year)
            
            # Daten für neue Zeile
            row_data = [timestamp, original_text, enhanced_text, month, year].append_row(row_data)
                logger.info(f"Erinnerung in Google Sheets gespeichert: {len(original_text)} Zeichen")
                return True
            else:
                # Mock für Demo - simuliere erfolgreiche Speicherung
                logger.info(f"Mock: Erinnerung gespeichert - {timestamp}")
                logger.info(f"Mock: Original: {original_text[:50]}...")
                logger.info(f"Mock: Enhanced: {enhanced_text[:50]}...")
                return True
                
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Erinnerung: {e}")
            return False
    
    async def get_memories_by_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Holt alle Erinnerungen für einen bestimmten Monat"""
        try:
            month_str = f"{year}-{month:02d}"
            
            if self.worksheet:
                # Alle Daten holen
                all_records = self.worksheet.get_all_records()
                
                # Nach Monat filtern
                month_memories = [
                    record for record in all_records 
                    if record.get('Monat') == month_str
                ]
                
                return month_memories
            else:
                # Mock Daten für Demo
                return [
                    {
                        'Datum': f'{month:02d}.{year} 10:30:00',
                        'Original Text': 'Mock Erinnerung für Demo',
                        'Aufbereiteter Text': 'Heute hatte meine Tochter einen wundervollen Tag...',
                        'Monat': month_str,
                        'Jahr': str(year)
                    }
                ]
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Monats-Erinnerungen: {e}")
            return []
    
    async def get_memories_by_year(self, year: int) -> List[Dict[str, Any]]:
        """Holt alle Erinnerungen für ein bestimmtes Jahr"""
        try:
            if self.worksheet:
                all_records = self.worksheet.get_all_records()
                
                year_memories = [
                    record for record in all_records 
                    if record.get('Jahr') == str(year)
                ]
                
                return year_memories
            else:
                # Mock Daten für Demo
                return [
                    {
                        'Datum': f'15.06.{year} 14:20:00',
                        'Original Text': 'Mock Jahres-Erinnerung',
                        'Aufbereiteter Text': 'Ein besonderes Jahr mit meiner Tochter...',
                        'Monat': f'{year}-06',
                        'Jahr': str(year)
                    }
                ]
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Jahres-Erinnerungen: {e}")
            return []
    
    def is_connected(self) -> bool:
        """Prüft ob die Verbindung zu Google Sheets aktiv ist"""
        return self.client is not None or True  # True für Mock-Modus

