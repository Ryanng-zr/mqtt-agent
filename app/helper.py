from typing import Dict, Any
import json

def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from a Gemini text response.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nRaw text:\n{text}")
