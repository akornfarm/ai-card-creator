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
        print(f"AI Card Creator: Generating fields for word: {word}")
        
        api_key = self.config.get("api_key", "")
        if not api_key:
            print("AI Card Creator: No API key configured")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://ankiweb.net",
                "X-Title": "Anki AI Card Creator"
            }
            
            prompt = self.config.get("prompt_template", "").format(word=word)
            model = self.config.get("model", "google/gemini-2.5-flash")
            api_url = f"{self.config.get('api_base_url', 'https://openrouter.ai/api/v1')}/chat/completions"
            
            print(f"AI Card Creator: Using model: {model}")
            print(f"AI Card Creator: API URL: {api_url}")
            
            data = {
                "model": model,
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
            
            print(f"AI Card Creator: Making API request...")
            response = requests.post(api_url, headers=headers, json=data, timeout=30)
            
            print(f"AI Card Creator: API response status: {response.status_code}")
            
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"AI Card Creator: {error_msg}")
                return None
                
            result = response.json()
            print(f"AI Card Creator: API response received, parsing...")
            
            if "choices" not in result or len(result["choices"]) == 0:
                print(f"AI Card Creator: No choices in response: {result}")
                return None
                
            content = result["choices"][0]["message"]["content"]
            print(f"AI Card Creator: Content received (first 200 chars): {content[:200]}...")
            
            try:
                fields_data = json.loads(content)
                # Validate that it's a dictionary
                if not isinstance(fields_data, dict):
                    print(f"AI Card Creator: Invalid response format - expected dict, got {type(fields_data).__name__}")
                    print(f"AI Card Creator: Response content: {content[:200]}...")
                    return None
                return fields_data
            except json.JSONDecodeError as e:
                print(f"AI Card Creator: JSON decode error: {str(e)}")
                print(f"AI Card Creator: Content: {content[:200]}...")
                return None
                
        except requests.exceptions.Timeout:
            print("AI Card Creator: Request timeout")
            return None
        except requests.exceptions.ConnectionError:
            print("AI Card Creator: Connection error")
            return None
        except Exception as e:
            print(f"AI Card Creator: Unexpected error: {str(e)}")
            import traceback
            traceback.print_exc()
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