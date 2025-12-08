import json
from typing import Any, Dict
from langchain_core.tools import tool
from mqttPayloadSchema import BaseMessage


def _render_payload(base_msg: BaseMessage) -> str:
    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        "data": base_msg.data,
    }
    return json.dumps(payload_dict, indent=2)


def _wrap_tool(fn, *, name: str, description: str):
    @tool(name, description=description)
    def _inner(**kwargs):
        if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            nested = kwargs.pop("kwargs")
            kwargs.update(nested)

        return fn(**kwargs)

    return _inner


# Helper to extract text from AI Response
def _extract_text(content: Any) -> str:
    """
    Handle string and list of strings from agent response
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(part) for part in content)
    return str(content)


# Helper to extract JSON object from LLM response
def extract_json_object(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from LLM response.
    """
    original_text = text
    text = text.strip()

    # Method 1 to Parse out chosen_goals from JSON
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

    # Method 2 to Parse out chosen_goals from JSON
    fence_start = text.find("```")
    if fence_start != -1:
        fence_end = text.find("```", fence_start + 3)
        if fence_end != -1:
            json_block = text[fence_start + 3 : fence_end].strip()
            try:
                return json.loads(json_block)
            except json.JSONDecodeError as e:
                pass

    # If no fenced block, find curly braces
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # fall through to final error
            pass

    # If entire response is a JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Failed to parse JSON from LLM response: {e}\nRaw text:\n{original_text}"
        )
