import json
from typing import Any, Dict, List

from helper import extract_json_object
from llm import llm
from mqttPayloadSchema import BaseMessage
from tools import TOOLS


def plan_tool_calls_with_gemini(
    base_msg: BaseMessage, goal_modes: Dict[str, str], chosen_goals: List[str]
) -> List[Dict[str, Any]]:
    """
    Ask Gemini to plan tool calls based on:
    - JSON payload
    - goal_modes mapping (goal text -> MONITOR / EXECUTE / MONITOR_EXECUTE / MONITOR_INFORM)
    - chosen_goals list (zero or more textual descriptions)
    - tool descriptions
    """
    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        "data": base_msg.data,
    }

    tools_desc = [
        {"name": t.name, "description": t.description} for t in TOOLS.values()
    ]

    goal_mode_explanation = {
        "MONITOR": "Analyze, assess, observe, validate or check information. Avoid heavy state-changing actions unless needed.",
        "EXECUTE": "Perform direct actions that change system state or trigger backend functionality.",
        "MONITOR_EXECUTE": "First analyze/monitor the situation, then execute appropriate actions based on results.",
        "MONITOR_INFORM": "Analyze/monitor and then produce a human-readable summary or notification (e.g., using notify_tool).",
    }

    prompt = (
        "You are a backend orchestration agent.\n\n"
        "=== PAYLOAD JSON ===\n"
        f"{json.dumps(payload_dict, indent=2)}\n\n"
        "=== AVAILABLE TOOLS ===\n"
        f"{json.dumps(tools_desc, indent=2)}\n\n"
        "=== CHOSEN GOALS ===\n"
        f"{json.dumps(chosen_goals, indent=2)}\n\n"
        "=== GOAL MODES (goal -> mode) ===\n"
        f"{json.dumps(goal_modes, indent=2)}\n\n"
        "Mode guidance (do not override):\n"
        f"{json.dumps(goal_mode_explanation, indent=2)}\n\n"
        "Instructions:\n"
        "- Based only on the payload, the chosen goals, and their modes, decide which tools to call (zero or more).\n"
        "- Use multiple tools if appropriate.\n"
        "- Do not invent fields not present in the payload.\n"
        "- If required fields are missing for a tool, omit that tool.\n\n"
        'Respond with ONLY JSON: { "tool_calls": [ { "tool": "<tool_name>", "args": { ... } } ] }'
    )

    print("[AGENT] Asking model to plan tool calls...")
    response = llm.invoke(prompt)
    text = (
        response.content if isinstance(response.content, str) else str(response.content)
    )
    print("[AGENT] Gemini plan raw response:")
    print(text)

    obj = extract_json_object(text)
    tool_calls = obj.get("tool_calls", [])
    if not isinstance(tool_calls, list):
        raise ValueError("Gemini response JSON must contain 'tool_calls' list")

    return tool_calls
