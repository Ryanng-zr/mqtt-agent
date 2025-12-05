import json
from mqttPayloadSchema import BaseMessage
from typing import Dict, Any, List
from tools import TOOLS
from llm import llm
from helper import extract_json_object

def plan_tool_calls_with_gemini(base_msg: BaseMessage, goal_mode: str, chosen_goal: str) -> List[Dict[str, Any]]:
    """
    Ask Gemini to plan tool calls based on:
    - JSON payload
    - goal_mode (MONITOR / EXECUTE / MONITOR_EXECUTE / MONITOR_INFORM)
    - chosen_goal (the textual description)
    - tool descriptions
    """
    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        # "correlationId": base_msg.correlationId,
        "data": base_msg.data,
    }

    tools_desc = [
        {"name": t.name, "description": t.description}
        for t in TOOLS.values()
    ]

    goal_mode_explanation = {
        "MONITOR": "Analyze, assess, observe, validate or check information. Avoid heavy state-changing actions unless needed.",
        "EXECUTE": "Perform direct actions that change system state or trigger backend functionality.",
        "MONITOR_EXECUTE": "First analyze/monitor the situation, then execute appropriate actions based on results.",
        "MONITOR_INFORM": "Analyze/monitor and then produce a human-readable summary or notification (e.g., using notify_tool).",
    }

    prompt = {
        "role": "user",
        "parts": [
            "You are a backend orchestration agent.",
            "",
            "=== PAYLOAD JSON ===",
            json.dumps(payload_dict, indent=2),
            "",
            "=== AVAILABLE TOOLS ===",
            json.dumps(tools_desc, indent=2),
            "",
            "=== CHOSEN GOAL ===",
            chosen_goal,
            "",
            "=== GOAL MODE ===",
            goal_mode,
            goal_mode_explanation.get(goal_mode, ""),
            "",
            "Instructions:",
            "- Based only on the payload, the chosen goals, and the goal mode:",
            "- Decide which tools to call (zero or more).",
            "- Use multiple tools if appropriate.",
            "- Do not invent fields not present in the payload.",
            "- If required fields are missing for a tool, omit that tool.",
            "",
            "Respond with ONLY JSON:",
            '{ "tool_calls": [ { "tool": "<tool_name>", "args": { ... } } ] }',
        ],
    }

    print("[AGENT] Asking Gemini to plan tool calls...")
    response = llm.generate_content(prompt)
    text = response.text
    print("[AGENT] Gemini plan raw response:")
    print(text)

    obj = extract_json_object(text)
    tool_calls = obj.get("tool_calls", [])
    if not isinstance(tool_calls, list):
        raise ValueError("Gemini response JSON must contain 'tool_calls' list")

    return tool_calls
