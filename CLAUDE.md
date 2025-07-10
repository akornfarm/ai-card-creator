# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

AI Card Creator is an Anki addon that generates flashcards using AI (via OpenRouter API). It's specifically optimized for Japanese vocabulary learning but supports any note type.

## Architecture

The addon follows a clean separation of concerns with four main components:

1. **`__init__.py`** - Entry point that hooks into Anki's profile_did_open event
2. **`config.py`** - Configuration management and settings UI
3. **`ai_client.py`** - OpenRouter API integration for AI content generation  
4. **`card_creator.py`** - Anki card creation logic with field mapping
5. **`ui.py`** - Qt-based UI window for user interaction

## Critical Implementation Details

### Threading Model
- **Background tasks**: Use `mw.taskman.run_in_background(task, on_done)` for API calls
- **Main thread only**: All Anki collection operations (`mw.col.*`) must happen in main thread
- **UI updates**: Use callbacks after background processing completes

### Anki API Usage
```python
# Correct background task pattern:
def task():
    return api_call()  # API calls only
    
def on_done(future):
    result = future.result()
    # Card creation and UI updates here in main thread
    
mw.taskman.run_in_background(task, on_done)
```

### Field Mapping
The addon handles multiple note types but is optimized for Japanese (일본어) note type with these fields:
- 단어, 요미가나, 의미, 영어, 예문, 한자, 메모, 품사

Lists from AI are formatted with bullet points to avoid bracket display issues.

### Configuration
- User settings in `config.json` (includes API key)
- Default model: `google/gemini-2.5-flash` via OpenRouter
- Prompt template uses Korean instructions for VocabMate persona

## Common Development Tasks

### Testing Changes
1. Edit files in place
2. Restart Anki (no separate build process)
3. Tools → AI Card Creator to test
4. Check console for debug output

### Debugging Crashes
- Check for Qt import issues (use specific imports, not wildcards)
- Ensure no `mw.col` access in background threads
- Look for `showWarning()` calls outside main thread

### Adding New Fields
1. Update field mapping in `card_creator.py` 
2. Modify prompt template in `config.json`
3. Handle list formatting if field can have multiple values

## Key Constraints

- Minimum Anki version: 23.10
- Requires `requests` library (install via Anki addon)
- OpenRouter API key required for operation
- Japanese note type expected by default configuration