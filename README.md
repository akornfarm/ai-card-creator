# AI Card Creator - Anki Addon

An Anki addon that generates flashcards using AI (Gemini 2.5 Flash via OpenRouter API). Optimized for Japanese vocabulary learning with Korean UI.

## Features

- 🤖 AI-powered card generation using Gemini 2.5 Flash
- 🇯🇵 Optimized for Japanese vocabulary learning
- 📝 Process multiple words at once (supports various delimiters)
- ⚡ Background processing keeps UI responsive
- 🎯 Automatic field mapping for different note types
- 🔧 Configurable prompt templates

## Installation

1. Download the addon files
2. Place in Anki's addon folder: `Anki2/addons21/ai-card-creator/`
3. Restart Anki

## Setup

1. Get an API key from [OpenRouter](https://openrouter.ai)
2. In Anki: Tools → AI Card Creator Settings
3. Enter your API key
4. Configure default deck and note type

## Usage

1. Tools → AI Card Creator
2. Enter Japanese words (one or multiple)
3. Click "카드 생성" (Create Card)
4. Cards are automatically created with all fields filled

### Supported Delimiters
- Newline (Enter)
- Comma (,)
- Space
- Middle dot (・)

## Note Type Fields

For Japanese (일본어) note type:
- 단어 (Word)
- 요미가나 (Reading)
- 의미 (Meaning)
- 영어 (English)
- 예문 (Examples)
- 한자 (Kanji)
- 메모 (Notes)
- 품사 (Part of Speech)

## Requirements

- Anki 23.10 or higher
- Python `requests` library
- OpenRouter API key

## Configuration

Settings are stored in `config.json`:
- API credentials
- Default deck and note type
- Prompt template
- Field mappings

## License

MIT License