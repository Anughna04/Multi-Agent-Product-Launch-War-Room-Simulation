import json
from utils.logger import logger

def extract_and_parse_json(text: str) -> dict:
    """Finds the first '{' and last '}', extracts and parses the JSON."""
    try:
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        
        if start_idx == -1 or end_idx == -1 or start_idx > end_idx:
            raise ValueError("No JSON object found in text.")
            
        json_str = text[start_idx:end_idx+1]
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"[JSON Extraction] Failed to parse JSON: {e}")
        raise ValueError(f"Invalid JSON: {e}")
