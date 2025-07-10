import json
import requests
import re
from typing import Dict, Any, Optional, List, Tuple

class AIClient:
    def __init__(self, config):
        self.config = config
        
    def parse_words(self, input_text: str) -> List[str]:
        """
        Parse input text to extract individual words based on delimiters:
        - Newline (\n)
        - Comma (,)
        - Space ( ) - but not spaces within words
        - Middle dot (・)
        """
        # First split by newlines
        lines = input_text.strip().split('\n')
        
        words = []
        for line in lines:
            # Split by comma and middle dot
            parts = re.split(r'[,、・]', line)
            for part in parts:
                # For space splitting, we need to be careful about compound words
                # Simple approach: if a part contains only Japanese characters and spaces,
                # treat spaces as delimiters. Otherwise, keep as is.
                part = part.strip()
                if part:
                    # Check if it's likely multiple words separated by spaces
                    if ' ' in part and all(ord(c) > 127 or c == ' ' for c in part):
                        # Split by spaces for Japanese-only text
                        subparts = part.split()
                        words.extend(subparts)
                    else:
                        words.append(part)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_words = []
        for word in words:
            if word and word not in seen:
                seen.add(word)
                unique_words.append(word)
                
        return unique_words
        
    def generate_card_fields(self, word: str) -> Optional[Dict[str, Any]]:
        """
        Generate card fields for a given word using OpenRouter API
        Returns a dictionary with field names as keys and content as values
        """
        api_key = self.config.get("api_key", "")
        if not api_key:
            # Don't show warning from background thread
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ankiweb.net",
                "X-Title": "Anki AI Card Creator"
            }
            
            prompt = self.config.get("prompt_template", "").format(word=word)
            
            data = {
                "model": self.config.get("model", "google/gemini-2.5-flash"),
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that generates Anki card content. Always respond with valid JSON only, no additional text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.config.get('api_base_url', 'https://openrouter.ai/api/v1')}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text}"
                return None
                
            result = response.json()
            
            if "choices" not in result or len(result["choices"]) == 0:
                return None
                
            content = result["choices"][0]["message"]["content"]
            
            try:
                fields_data = json.loads(content)
                return fields_data
            except json.JSONDecodeError:
                return None
                
        except requests.exceptions.Timeout:
            return None
        except requests.exceptions.ConnectionError:
            return None
        except Exception:
            return None
    
    def generate_cards_for_words(self, words: List[str]) -> List[Tuple[str, Optional[Dict[str, Any]], Optional[str]]]:
        """
        Generate card fields for multiple words
        Returns a list of tuples: (word, fields_data or None, error_message or None)
        """
        results = []
        
        api_key = self.config.get("api_key", "")
        if not api_key:
            # Return error for all words if no API key
            return [(word, None, "API key not configured") for word in words]
        
        for word in words:
            fields_data = self.generate_card_fields(word)
            if fields_data:
                results.append((word, fields_data, None))
            else:
                results.append((word, None, "Failed to generate content"))
                
        return results
    
    def validate_api_key(self) -> bool:
        """Test if the API key is valid by making a minimal request"""
        api_key = self.config.get("api_key", "")
        if not api_key:
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Make a minimal request to check if the key works
            data = {
                "model": self.config.get("model", "google/gemini-2.5-flash"),
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                f"{self.config.get('api_base_url', 'https://openrouter.ai/api/v1')}/chat/completions",
                headers=headers,
                json=data,
                timeout=10
            )
            
            return response.status_code == 200
            
        except:
            return False