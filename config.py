import json
import os
from aqt import mw
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
                     QLabel, QLineEdit, QComboBox, QTextEdit, QPushButton,
                     QCheckBox, QFrame)
from aqt.utils import showInfo

class AICardCreatorConfig:
    def __init__(self):
        self.addon_path = os.path.dirname(__file__)
        self.config_path = os.path.join(self.addon_path, "config.json")
        self.config = self.load_config()
        
    def load_config(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            # Don't show dialog during initialization, just use defaults
            print(f"AI Card Creator: Failed to load config: {str(e)}")
            return self.get_default_config()
    
    def save_config(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            showInfo(f"Failed to save config: {str(e)}")
    
    def get_default_config(self):
        return {
            "api_key": "",
            "api_base_url": "https://openrouter.ai/api/v1",
            "model": "google/gemini-2.5-flash",
            "default_deck": "Default",
            "default_note_type": "Basic",
            "prompt_template": "Generate Anki card for: {word}",
            "field_mappings": {},
            "window_position": {"x": 100, "y": 100}
        }
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def show_settings_dialog(self):
        dialog = SettingsDialog(mw, self)
        dialog.exec()

class SettingsDialog(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("AI Card Creator Settings")
        self.setMinimumWidth(600)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # API Settings
        api_group = QGroupBox("API Settings")
        api_layout = QFormLayout()
        
        self.api_key_edit = QLineEdit(self.config.get("api_key", ""))
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        api_layout.addRow("OpenRouter API Key:", self.api_key_edit)
        
        self.api_base_url_edit = QLineEdit(self.config.get("api_base_url", ""))
        api_layout.addRow("API Base URL:", self.api_base_url_edit)
        
        self.model_edit = QLineEdit(self.config.get("model", ""))
        api_layout.addRow("Model:", self.model_edit)
        
        api_group.setLayout(api_layout)
        layout.addWidget(api_group)
        
        # Card Settings
        card_group = QGroupBox("Card Settings")
        card_layout = QFormLayout()
        
        self.deck_combo = QComboBox()
        decks = [d["name"] for d in mw.col.decks.all()]
        self.deck_combo.addItems(decks)
        current_deck = self.config.get("default_deck", "Default")
        if current_deck in decks:
            self.deck_combo.setCurrentText(current_deck)
        card_layout.addRow("Default Deck:", self.deck_combo)
        
        self.note_type_combo = QComboBox()
        note_types = [m["name"] for m in mw.col.models.all()]
        self.note_type_combo.addItems(note_types)
        current_note_type = self.config.get("default_note_type", "Basic")
        if current_note_type in note_types:
            self.note_type_combo.setCurrentText(current_note_type)
        card_layout.addRow("Default Note Type:", self.note_type_combo)
        
        card_group.setLayout(card_layout)
        layout.addWidget(card_group)
        
        # Prompt Template
        prompt_group = QGroupBox("Prompt Template")
        prompt_layout = QVBoxLayout()
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlainText(self.config.get("prompt_template", ""))
        self.prompt_edit.setMinimumHeight(150)
        prompt_layout.addWidget(self.prompt_edit)
        
        prompt_help = QLabel("Use {word} as placeholder for the input word")
        prompt_help.setWordWrap(True)
        prompt_layout.addWidget(prompt_help)
        
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def save_settings(self):
        self.config.set("api_key", self.api_key_edit.text())
        self.config.set("api_base_url", self.api_base_url_edit.text())
        self.config.set("model", self.model_edit.text())
        self.config.set("default_deck", self.deck_combo.currentText())
        self.config.set("default_note_type", self.note_type_combo.currentText())
        self.config.set("prompt_template", self.prompt_edit.toPlainText())
        
        showInfo("Settings saved successfully!")
        self.accept()