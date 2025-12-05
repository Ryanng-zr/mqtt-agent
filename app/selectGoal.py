from mqttPayloadSchema import BaseMessage
from typing import List
from llm import llm
import json
from helper import extract_json_object

def select_best_goal_for_message(base_msg: BaseMessage, candidate_goals: List[str]) -> str:
    """
    Given a message payload and a list of candidate goals (strings),
    ask Gemini to choose the most appropriate goal or none for this message.
    """
    if not candidate_goals:
        raise ValueError("candidate_goals must not be empty")

    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        # "correlationId": base_msg.correlationId,
        "data": base_msg.data,
    }

    prompt = {
        "role": "user",
        "parts": [
            "You are a goal selector for a backend orchestration AI.",
            "",
            "You will receive:",
            "- A JSON payload representing a message from another system.",
            "- A list of possible goals (strings).",
            "",
            "Your job:",
            "- Choose zero or more goals from the list that best matches what should be done",
            "  for this specific payload.",
            "- Consider both the semantics of the payload and the wording of each goal.",
            "- If more than one seems reasonable, pick the one that is most specific.",
            "",
            "Important:",
            "- If it matches none of the goals, return nothing.",
            "- Return the goals exactly as it appears in the list.",
            "- Do NOT modify the text.",
            "- Do NOT invent new goals.",
            "",
            "=== PAYLOAD JSON ===",
            json.dumps(payload_dict, indent=2),
            "",
            "=== CANDIDATE GOALS ===",
            json.dumps(candidate_goals, indent=2),
            "",
            "Respond with ONLY a JSON object:",
            '{ "chosen_goal": "<one_of_the_candidate_strings>" }',
        ],
    }

    print("[AGENT] Asking Gemini to select best goal...")
    response = llm.generate_content(prompt)
    text = response.text
    print("[AGENT] Goal selection raw response:")
    print(text)

    obj = extract_json_object(text)
    chosen = obj.get("chosen_goal", "").strip()

    if chosen not in candidate_goals:
        print("[AGENT] Chosen goal not in candidate list, falling back to first candidate.")
        return candidate_goals[0]

    return chosen


def classify_goal_mode(goal: str) -> str:
    """
    Convert goal into one of:
    - MONITOR
    - EXECUTE
    - MONITOR_EXECUTE
    - MONITOR_INFORM
    """
    prompt = {
        "role": "user",
        "parts": [
            "You are a goal interpreter for a backend orchestration AI.",
            "You will receive a single human-written goal.",
            "",
            "You must classify it into exactly one of these modes:",
            "- MONITOR",
            "- EXECUTE",
            "- MONITOR_EXECUTE",
            "- MONITOR_INFORM",
            "",
            "Examples:",
            "- 'Monitor all sensor states' -> MONITOR",
            "- 'Change all Warning States to RED' -> EXECUTE",
            "- 'Check for sensor gap and if exist, change warning state to red' -> MONITOR_EXECUTE",
            "- 'Monitor tracks and notify me' -> MONITOR_INFORM",
            "",
            "Return ONLY the mode name.",
            "",
            "Goal:",
            goal,
        ],
    }

    response = llm.generate_content(prompt)
    mode = response.text.strip().upper()

    valid = {"MONITOR", "EXECUTE", "MONITOR_EXECUTE", "MONITOR_INFORM"}
    if mode not in valid:
        print(f"[AGENT] Invalid mode '{mode}', defaulting to MONITOR.")
        return "MONITOR"

    return mode