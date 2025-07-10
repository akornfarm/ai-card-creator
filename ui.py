from aqt import mw
from aqt.qt import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, 
                     QTextEdit, QLineEdit, QComboBox, QPushButton, QTimer,
                     Qt)
from aqt.utils import showInfo, tooltip
from .ai_client import AIClient
from .card_creator import CardCreator

class AICardCreatorWindow(QDialog):
    def __init__(self, parent, config):
        super().__init__(parent)
        self.config = config
        self.ai_client = AIClient(config)
        self.card_creator = CardCreator(config)
        
        self.setWindowTitle("AI Card Creator")
        self.setWindowFlags(Qt.WindowType.Window)
        
        self.setup_ui()
        self.load_position()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        title = QLabel("AI Card Creator - VocabMate")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Input section
        input_group = QGroupBox("입력")
        input_layout = QVBoxLayout()
        
        # Word input - now a text area for multiple words
        input_label = QLabel("일본어 단어 입력 (여러 개 가능):")
        input_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(input_label)
        
        self.word_input = QTextEdit()
        self.word_input.setPlaceholderText("단어를 입력하세요...\n\n구분자: 줄바꿈, 쉼표(,), 공백, 가운뎃점(・)\n예: 日本, 勉強する\n    透明・曖昧")
        self.word_input.setMaximumHeight(100)
        input_layout.addWidget(self.word_input)
        
        # Deck and Note Type selection
        selection_layout = QHBoxLayout()
        
        deck_layout = QVBoxLayout()
        deck_label = QLabel("덱:")
        deck_layout.addWidget(deck_label)
        self.deck_combo = QComboBox()
        self.refresh_decks()
        deck_layout.addWidget(self.deck_combo)
        selection_layout.addLayout(deck_layout)
        
        note_type_layout = QVBoxLayout()
        note_type_label = QLabel("노트 타입:")
        note_type_layout.addWidget(note_type_label)
        self.note_type_combo = QComboBox()
        self.refresh_note_types()
        note_type_layout.addWidget(self.note_type_combo)
        selection_layout.addLayout(note_type_layout)
        
        input_layout.addLayout(selection_layout)
        
        # Create button
        self.create_button = QPushButton("카드 생성")
        self.create_button.clicked.connect(self.create_cards)
        self.create_button.setStyleSheet("QPushButton { padding: 10px; font-weight: bold; font-size: 14px; background-color: #4CAF50; color: white; }")
        input_layout.addWidget(self.create_button)
        
        # Progress indicator
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("color: #666; font-style: italic;")
        input_layout.addWidget(self.progress_label)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Results section
        results_group = QGroupBox("처리 결과")
        results_layout = QVBoxLayout()
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        results_group.setLayout(results_layout)
        layout.addWidget(results_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        refresh_button = QPushButton("새로고침")
        refresh_button.clicked.connect(self.refresh_lists)
        refresh_button.setToolTip("덱과 노트 타입 목록을 새로고침합니다")
        button_layout.addWidget(refresh_button)
        
        clear_button = QPushButton("결과 지우기")
        clear_button.clicked.connect(self.clear_results)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.resize(600, 700)
        
    def create_cards(self):
        input_text = self.word_input.toPlainText().strip()
        if not input_text:
            tooltip("단어를 입력해주세요")
            return
            
        # Parse words
        words = self.ai_client.parse_words(input_text)
        if not words:
            tooltip("처리할 단어가 없습니다")
            return
            
        # Update config with current selections
        self.config.set("default_deck", self.deck_combo.currentText())
        self.config.set("default_note_type", self.note_type_combo.currentText())
        
        # Disable UI during processing
        self.set_ui_enabled(False)
        self.progress_label.setText(f"{len(words)}개 단어 처리 중...")
        self.results_text.clear()
        
        # Store words for background processing
        self.words_to_process = words
        
        # Use Anki's task manager for background processing
        def task():
            return self._process_cards_background(words)
        
        def on_done(future):
            try:
                result = future.result()
                self._on_cards_processing_complete(result)
            except Exception as e:
                self._on_creation_failed(str(e))
        
        mw.taskman.run_in_background(task, on_done)
        
    def _process_cards_background(self, words):
        """Process cards in background - only API calls, no UI operations"""
        try:
            print(f"AI Card Creator: Starting background processing for {len(words)} words")
            
            # Generate fields for all words
            results = self.ai_client.generate_cards_for_words(words)
            
            print(f"AI Card Creator: Generated fields for {len(results)} words")
            
            # Collect results without creating cards (card creation must happen in main thread)
            detailed_results = []
            
            for word, fields_data, error in results:
                if error:
                    detailed_results.append((word, None, error))
                else:
                    detailed_results.append((word, fields_data, None))
            
            return detailed_results
                
        except Exception as e:
            print(f"AI Card Creator: Background processing error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
    
    def _on_cards_processing_complete(self, results):
        """Called when background processing is complete - create cards in main thread"""
        try:
            print(f"AI Card Creator: Processing complete, creating cards for {len(results)} words")
            
            # Process each result and create cards
            success_count = 0
            duplicate_count = 0
            fail_count = 0
            detailed_results = []
            
            for word, fields_data, error in results:
                if error:
                    fail_count += 1
                    detailed_results.append((word, False, error, None))
                elif fields_data:
                    # Try to create the card in main thread
                    success, message = self.card_creator.create_card(fields_data, word)
                    if success:
                        success_count += 1
                        detailed_results.append((word, True, message, fields_data))
                    elif "이미 존재" in message:
                        duplicate_count += 1
                        detailed_results.append((word, False, message, None))
                    else:
                        fail_count += 1
                        detailed_results.append((word, False, message, None))
                else:
                    fail_count += 1
                    detailed_results.append((word, False, "No data generated", None))
            
            # Update UI
            self._on_cards_created(len(results), success_count, duplicate_count, fail_count, detailed_results)
            
        except Exception as e:
            print(f"AI Card Creator: Error in main thread processing: {str(e)}")
            import traceback
            traceback.print_exc()
            self._on_creation_failed(str(e))
            
    def _on_cards_created(self, total, success, duplicate, fail, results):
        self.set_ui_enabled(True)
        self.progress_label.setText("")
        
        # Build results text
        result_text = f"📊 처리 결과: {total}개 중 {success}개 추가 완료\n\n"
        
        # Summary by status
        for word, is_success, message, fields_data in results:
            if is_success:
                result_text += f"✅ {word}"
                if fields_data and "요미가나" in fields_data:
                    result_text += f" ({fields_data['요미가나']})"
                result_text += f" - {message}\n"
                if fields_data and "의미" in fields_data:
                    result_text += f"   → {fields_data['의미']}\n"
            elif "이미 존재" in message:
                result_text += f"⚠️ {word} - {message}\n"
            else:
                result_text += f"❌ {word} - {message}\n"
        
        # Add detailed content for successfully added cards
        if success > 0:
            result_text += "\n\n[추가된 카드 상세 내용]\n"
            result_text += "="*50 + "\n\n"
            
            for word, is_success, message, fields_data in results:
                if is_success and fields_data:
                    result_text += f"【{word}】\n"
                    if "요미가나" in fields_data:
                        result_text += f"읽기: {fields_data['요미가나']}\n"
                    if "의미" in fields_data:
                        result_text += f"의미: {fields_data['의미']}\n"
                    if "영어" in fields_data:
                        result_text += f"영어: {fields_data['영어']}\n"
                    if "품사" in fields_data:
                        result_text += f"품사: {fields_data['품사']}\n"
                    if "한자" in fields_data and fields_data["한자"]:
                        result_text += f"한자: {fields_data['한자']}\n"
                    result_text += "\n"
        
        self.results_text.setPlainText(result_text)
        
        # Clear input if all successful
        if success > 0:
            self.word_input.clear()
            self.word_input.setFocus()
            
    def _on_creation_failed(self, error):
        self.set_ui_enabled(True)
        self.progress_label.setText("")
        self.results_text.setPlainText(f"❌ 오류 발생: {error}")
        
    def set_ui_enabled(self, enabled):
        self.word_input.setEnabled(enabled)
        self.create_button.setEnabled(enabled)
        self.deck_combo.setEnabled(enabled)
        self.note_type_combo.setEnabled(enabled)
        
    def refresh_decks(self):
        self.deck_combo.clear()
        decks = self.card_creator.get_all_decks()
        self.deck_combo.addItems(decks)
        
        current_deck = self.config.get("default_deck", "단어")
        if current_deck in decks:
            self.deck_combo.setCurrentText(current_deck)
            
    def refresh_note_types(self):
        self.note_type_combo.clear()
        note_types = self.card_creator.get_all_note_types()
        self.note_type_combo.addItems(note_types)
        
        current_note_type = self.config.get("default_note_type", "일본어")
        if current_note_type in note_types:
            self.note_type_combo.setCurrentText(current_note_type)
            
    def refresh_lists(self):
        """Refresh deck and note type lists"""
        self.refresh_decks()
        self.refresh_note_types()
        # Show tooltip only if called manually (not during showEvent)
        if self.sender() and hasattr(self.sender(), 'text'):
            tooltip("목록이 새로고침되었습니다")
        
    def clear_results(self):
        self.results_text.clear()
        
    def load_position(self):
        pos = self.config.get("window_position", {"x": 100, "y": 100})
        self.move(pos["x"], pos["y"])
        
    def showEvent(self, event):
        """Refresh lists when window is shown"""
        super().showEvent(event)
        # Refresh deck and note type lists in case they changed
        self.refresh_lists()
        
    def closeEvent(self, event):
        # Save window position
        pos = self.pos()
        self.config.set("window_position", {"x": pos.x(), "y": pos.y()})
        event.accept()