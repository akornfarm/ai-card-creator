from aqt import mw
from aqt.utils import showInfo, showWarning, tooltip
from typing import Dict, Any, Optional, Tuple

class CardCreator:
    def __init__(self, config):
        self.config = config
        
    def create_card(self, fields_data: Dict[str, Any], word: str) -> Tuple[bool, str]:
        """
        Create an Anki card from the AI-generated fields data
        Returns tuple: (success: bool, message: str)
        """
        try:
            # Validate fields_data type
            if not isinstance(fields_data, dict):
                return False, f"Invalid AI response format: expected dict, got {type(fields_data).__name__}"
            
            # Get the configured deck and note type
            deck_name = self.config.get("default_deck", "단어")
            note_type_name = self.config.get("default_note_type", "일본어")
            
            # Get deck ID
            deck = mw.col.decks.by_name(deck_name)
            if not deck:
                return False, f"Deck '{deck_name}' not found"
            deck_id = deck["id"]
            
            # Get note type (model)
            model = mw.col.models.by_name(note_type_name)
            if not model:
                return False, f"Note type '{note_type_name}' not found"
                
            # Create new note
            note = mw.col.new_note(model)
            
            # Get field mappings for this note type
            field_mappings = self.config.get("field_mappings", {}).get(note_type_name, {})
            
            # Map AI fields to note fields
            fields_filled = False
            
            # Debug: Print available fields
            print(f"AI Card Creator: Note type '{note_type_name}' has fields: {list(note.keys())}")
            print(f"AI Card Creator: AI generated fields: {list(fields_data.keys())}")
            
            # For Japanese note type, use specific field mapping
            if note_type_name == "일본어":
                mapping = {
                    "단어": "단어",
                    "요미가나": "요미가나", 
                    "의미": "의미",
                    "영어": "영어",
                    "예문": "예문",
                    "한자": "한자",
                    "메모": "메모",
                    "품사": "품사"
                }
                
                for ai_field, note_field in mapping.items():
                    if ai_field in fields_data and note_field in note:
                        # Format the field value properly
                        field_value = fields_data[ai_field]
                        
                        # Handle list values (like 의미 field)
                        if isinstance(field_value, list):
                            # Join list items with line breaks or bullet points
                            if ai_field == "의미":
                                # Format meanings with bullet points
                                formatted_value = "\n".join([f"• {item}" for item in field_value])
                            else:
                                # For other lists, join with line breaks
                                formatted_value = "\n".join(field_value)
                        else:
                            formatted_value = str(field_value)
                        
                        note[note_field] = formatted_value
                        fields_filled = True
                        print(f"AI Card Creator: Mapped {ai_field} -> {note_field}")
                    elif ai_field in fields_data:
                        print(f"AI Card Creator: Field '{note_field}' not found in note type")
                    else:
                        print(f"AI Card Creator: Field '{ai_field}' not in AI response")
            else:
                # For other note types, try direct mapping first
                for field_name, field_value in fields_data.items():
                    if field_name in note:
                        # Handle list values
                        if isinstance(field_value, list):
                            formatted_value = "\n".join([str(item) for item in field_value])
                        else:
                            formatted_value = str(field_value)
                        note[field_name] = formatted_value
                        fields_filled = True
                    else:
                        # Try field mappings
                        for mapped_field in field_mappings.values():
                            if mapped_field == field_name and mapped_field in note:
                                note[mapped_field] = str(field_value)
                                fields_filled = True
                                break
            
            if not fields_filled:
                return False, "No matching fields found"
            
            # Set the deck for the note
            note.note_type()["did"] = deck_id
            
            # Try to add the note
            try:
                mw.col.add_note(note, deck_id)
                # Update the UI
                mw.reset()
                return True, "추가 완료"
            except Exception as e:
                # Check if it's a duplicate error by examining the exception message
                if "duplicate" in str(e).lower():
                    return False, "이미 존재"
                else:
                    raise
                
        except Exception as e:
            return False, str(e)
    
    def get_available_fields(self, note_type_name: str) -> list:
        """Get list of fields for a given note type"""
        model = mw.col.models.by_name(note_type_name)
        if not model:
            return []
        return [field["name"] for field in model["flds"]]
    
    def validate_note_type(self, note_type_name: str) -> bool:
        """Check if a note type exists"""
        return mw.col.models.by_name(note_type_name) is not None
    
    def get_all_note_types(self) -> list:
        """Get list of all available note types"""
        return [model["name"] for model in mw.col.models.all()]
    
    def get_all_decks(self) -> list:
        """Get list of all available decks"""
        return [deck["name"] for deck in mw.col.decks.all()]