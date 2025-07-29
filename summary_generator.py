"""
Intelligenter Zusammenfassungs-Generator für Tochter-Erinnerungen
Erstellt schöne, emotionale Zusammenfassungen aus den gesammelten Erinnerungen
"""

import logging
from datetime import datetime
from typing import List, Dict, Any
import openai
import os

logger = logging.getLogger(__name__)

class SummaryGenerator:
    def __init__(self):
        self.openai_client = openai.OpenAI()
    
    async def generate_monthly_summary(self, memories: List[Dict[str, Any]], year: int, month: int) -> str:
        """Generiert eine intelligente Monats-Zusammenfassung"""
        try:
            if not memories:
                return self._create_empty_monthly_summary(year, month)
            
            # Alle aufbereiteten Texte sammeln
            memory_texts = []
            for memory in memories:
                enhanced_text = memory.get('Aufbereiteter Text', '')
                date = memory.get('Datum', '')
                if enhanced_text:
                    memory_texts.append(f"[{date}] {enhanced_text}")
            
            if not memory_texts:
                return self._create_empty_monthly_summary(year, month)
            
            # KI-Zusammenfassung erstellen
            month_names = [
                "", "Januar", "Februar", "März", "April", "Mai", "Juni",
                "Juli", "August", "September", "Oktober", "November", "Dezember"
            ]
            month_name = month_names[month] if 1 <= month <= 12 else str(month)
            
            prompt = f"""Du bist ein liebevoller Assistent, der dabei hilft, Erinnerungen an eine Tochter zusammenzufassen.

AUFGABE: Erstelle eine wunderschöne, emotionale Monats-Zusammenfassung für {month_name} {year}.

ERINNERUNGEN:
{chr(10).join(memory_texts)}

REGELN:
- Schreibe in der Du-Form (als würdest du zu den Eltern sprechen)
- Sei warm, liebevoll und emotional
- Hebe besondere Momente hervor
- Verwende schöne, poetische Sprache
- Strukturiere die Zusammenfassung in Absätze
- Beginne mit einer schönen Einleitung
- Ende mit einem herzlichen Abschluss
- Erwähne konkrete Details aus den Erinnerungen
- Maximal 500 Wörter

ZUSAMMENFASSUNG:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.8,
                presence_penalty=0.2
            )
            
            ai_summary = response.choices[0].message.content.strip()
            
            # Formatierte Zusammenfassung erstellen
            formatted_summary = f"""📊 **Monats-Zusammenfassung {month_name} {year}**

📝 **{len(memories)} wundervolle Erinnerungen gesammelt**

✨ **Dein Monat im Rückblick:**

{ai_summary}

📅 **Alle Erinnerungen:**
"""
            
            # Kurze Liste der Erinnerungen hinzufügen
            for i, memory in enumerate(memories[:10], 1):
                date = memory.get('Datum', '').split(' ')[0]  # Nur Datum, ohne Zeit
                enhanced = memory.get('Aufbereiteter Text', '')[:80]
                if len(enhanced) > 77:
                    enhanced = enhanced[:77] + "..."
                formatted_summary += f"{i}. [{date}] {enhanced}\n"
            
            if len(memories) > 10:
                formatted_summary += f"\n... und {len(memories) - 10} weitere kostbare Momente\n"
            
            formatted_summary += "\n💝 Was für ein besonderer Monat mit deiner Tochter!"
            
            return formatted_summary
            
        except Exception as e:
            logger.error(f"Fehler bei KI-Monats-Zusammenfassung: {e}")
            return self._create_simple_monthly_summary(memories, year, month)
    
    async def generate_yearly_summary(self, memories: List[Dict[str, Any]], year: int) -> str:
        """Generiert eine intelligente Jahres-Zusammenfassung"""
        try:
            if not memories:
                return self._create_empty_yearly_summary(year)
            
            # Erinnerungen nach Monaten gruppieren
            monthly_groups = {}
            for memory in memories:
                month_key = memory.get('Monat', '')
                if month_key:
                    if month_key not in monthly_groups:
                        monthly_groups[month_key] = []
                    monthly_groups[month_key].append(memory)
            
            # Highlights aus jedem Monat sammeln
            monthly_highlights = []
            for month_key in sorted(monthly_groups.keys()):
                month_memories = monthly_groups[month_key]
                month_num = int(month_key.split('-')[1]) if '-' in month_key else 1
                
                # Beste Erinnerung des Monats (längste aufbereitete Version)
                best_memory = max(month_memories, key=lambda m: len(m.get('Aufbereiteter Text', '')))
                highlight = best_memory.get('Aufbereiteter Text', '')[:150]
                if len(highlight) > 147:
                    highlight = highlight[:147] + "..."
                
                month_names = [
                    "", "Januar", "Februar", "März", "April", "Mai", "Juni",
                    "Juli", "August", "September", "Oktober", "November", "Dezember"
                ]
                month_name = month_names[month_num] if 1 <= month_num <= 12 else str(month_num)
                
                monthly_highlights.append(f"{month_name}: {highlight}")
            
            # KI-Jahres-Zusammenfassung erstellen
            prompt = f"""Du bist ein liebevoller Assistent, der dabei hilft, ein ganzes Jahr voller Erinnerungen an eine Tochter zusammenzufassen.

AUFGABE: Erstelle eine wunderschöne, emotionale Jahres-Zusammenfassung für {year}.

HIGHLIGHTS AUS JEDEM MONAT:
{chr(10).join(monthly_highlights)}

STATISTIKEN:
- Insgesamt {len(memories)} Erinnerungen gesammelt
- Aktive Monate: {len(monthly_groups)}

REGELN:
- Schreibe in der Du-Form (als würdest du zu den Eltern sprechen)
- Sei warm, liebevoll und emotional
- Reflektiere über das Wachstum und die Entwicklung
- Verwende poetische, herzliche Sprache
- Strukturiere in Absätze
- Beginne mit einer schönen Einleitung über das Jahr
- Ende mit einem hoffnungsvollen Ausblick
- Erwähne die Reise durch die Monate
- Maximal 600 Wörter

JAHRES-ZUSAMMENFASSUNG:"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.8,
                presence_penalty=0.2
            )
            
            ai_summary = response.choices[0].message.content.strip()
            
            # Formatierte Jahres-Zusammenfassung
            formatted_summary = f"""📊 **Jahres-Zusammenfassung {year}**

📝 **{len(memories)} kostbare Erinnerungen gesammelt**
📅 **{len(monthly_groups)} aktive Monate**

✨ **Dein Jahr im Rückblick:**

{ai_summary}

📈 **Erinnerungen pro Monat:**
"""
            
            # Monatsstatistiken
            for month_key in sorted(monthly_groups.keys()):
                month_num = int(month_key.split('-')[1]) if '-' in month_key else 1
                count = len(monthly_groups[month_key])
                month_names = [
                    "", "Jan", "Feb", "Mär", "Apr", "Mai", "Jun",
                    "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"
                ]
                month_name = month_names[month_num] if 1 <= month_num <= 12 else str(month_num)
                formatted_summary += f"• {month_name}: {count} Erinnerungen\n"
            
            formatted_summary += f"\n🌟 Ein ganzes Jahr voller Liebe, Lachen und unvergesslicher Momente mit deiner Tochter!"
            
            return formatted_summary
            
        except Exception as e:
            logger.error(f"Fehler bei KI-Jahres-Zusammenfassung: {e}")
            return self._create_simple_yearly_summary(memories, year)
    
    def _create_empty_monthly_summary(self, year: int, month: int) -> str:
        """Erstellt eine Zusammenfassung für einen leeren Monat"""
        month_names = [
            "", "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ]
        month_name = month_names[month] if 1 <= month <= 12 else str(month)
        
        return f"""📅 **Monats-Zusammenfassung {month_name} {year}**

📝 **Noch keine Erinnerungen gesammelt**

💡 **Tipp:** Sende Sprachnachrichten über die schönen Momente mit deiner Tochter, um diesen Monat mit Leben zu füllen!

🎤 Erzähle von:
• Lustigen Sprüchen oder Reaktionen
• Besonderen Momenten im Alltag
• Neuen Fähigkeiten oder Entwicklungen
• Gemeinsamen Erlebnissen und Abenteuern

💝 Jede kleine Erinnerung ist wertvoll!"""
    
    def _create_empty_yearly_summary(self, year: int) -> str:
        """Erstellt eine Zusammenfassung für ein leeres Jahr"""
        return f"""📅 **Jahres-Zusammenfassung {year}**

📝 **Noch keine Erinnerungen gesammelt**

🌟 **Ein neues Jahr voller Möglichkeiten!**

Dieses Jahr ist wie ein leeres Buch, das darauf wartet, mit wundervollen Erinnerungen an deine Tochter gefüllt zu werden.

💡 **Starte jetzt:**
• Sende täglich kleine Sprachnachrichten
• Halte besondere Momente fest
• Sammle lustige Sprüche und süße Reaktionen
• Dokumentiere Entwicklungsschritte

💝 Am Ende des Jahres wirst du ein wunderschönes Erinnerungsbuch haben!"""
    
    def _create_simple_monthly_summary(self, memories: List[Dict[str, Any]], year: int, month: int) -> str:
        """Fallback: Einfache Monats-Zusammenfassung ohne KI"""
        month_names = [
            "", "Januar", "Februar", "März", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember"
        ]
        month_name = month_names[month] if 1 <= month <= 12 else str(month)
        
        summary = f"""📊 **Monats-Zusammenfassung {month_name} {year}**

📝 **{len(memories)} Erinnerungen gesammelt**

📅 **Deine Erinnerungen:**
"""
        
        for i, memory in enumerate(memories[:10], 1):
            date = memory.get('Datum', '').split(' ')[0]
            enhanced = memory.get('Aufbereiteter Text', '')[:100]
            if len(enhanced) > 97:
                enhanced = enhanced[:97] + "..."
            summary += f"{i}. [{date}] {enhanced}\n"
        
        if len(memories) > 10:
            summary += f"\n... und {len(memories) - 10} weitere Erinnerungen\n"
        
        summary += "\n💝 Was für ein wundervoller Monat mit deiner Tochter!"
        return summary
    
    def _create_simple_yearly_summary(self, memories: List[Dict[str, Any]], year: int) -> str:
        """Fallback: Einfache Jahres-Zusammenfassung ohne KI"""
        # Gruppiere nach Monaten
        monthly_counts = {}
        for memory in memories:
            month_key = memory.get('Monat', '')
            if month_key:
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        
        summary = f"""📊 **Jahres-Zusammenfassung {year}**

📝 **{len(memories)} Erinnerungen gesammelt**
📅 **{len(monthly_counts)} aktive Monate**

📈 **Erinnerungen pro Monat:**
"""
        
        for month_key in sorted(monthly_counts.keys()):
            month_num = month_key.split('-')[1] if '-' in month_key else month_key
            count = monthly_counts[month_key]
            summary += f"• {month_num}: {count} Erinnerungen\n"
        
        summary += f"\n💝 Ein ganzes Jahr voller wundervoller Momente mit deiner Tochter!"
        return summary

