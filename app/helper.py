from typing import Dict, Any
import json

# def extract_json_object(text: str) -> Dict[str, Any]:
#     """
#     Extract a JSON object from a Gemini text response.
#     """
#     text = text.strip()
#     if text.startswith("```"):
#         text = text.strip("`")
#         if text.lower().startswith("json"):
#             text = text[4:].strip()

#     try:
#         return json.loads(text)
#     except json.JSONDecodeError as e:
#         raise ValueError(f"Failed to parse JSON from Gemini response: {e}\nRaw text:\n{text}")

import json
from typing import Any, Dict


def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Extract a JSON object from an LLM response.
    Handles:
    - pure JSON
    - ```json ... ``` fenced blocks
    - ``` ... ``` generic fenced blocks
    - extra prose before/after JSON
    """
    original_text = text
    text = text.strip()

    # 1) Try to find a ```json fenced block first
    fence_start = text.lower().find("```json")
    if fence_start != -1:
        fence_end = text.find("```", fence_start + 7)
        if fence_end != -1:
            json_block = text[fence_start + len("```json") : fence_end].strip()
            try:
                return json.loads(json_block)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Failed to parse JSON from fenced ```json block: {e}\nRaw block:\n{json_block}"
                )

    # 2) Fallback: any ``` fenced block (no language tag)
    fence_start = text.find("```")
    if fence_start != -1:
        fence_end = text.find("```", fence_start + 3)
        if fence_end != -1:
            json_block = text[fence_start + 3 : fence_end].strip()
            try:
                return json.loads(json_block)
            except json.JSONDecodeError as e:
                # continue to next strategy instead of failing immediately
                pass

    # 3) Fallback: find first '{' and last '}' and try that substring
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # fall through to final error
            pass

    # 4) Last resort: try to parse the whole thing (maybe it was already JSON)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from LLM response: {e}\nRaw text:\n{original_text}"
        )
