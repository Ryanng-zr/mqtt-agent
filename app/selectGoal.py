import json
from typing import List

from llm import llm
from mqttPayloadSchema import BaseMessage
from helper import extract_json_object


def select_best_goal_for_message(
    base_msg: BaseMessage, candidate_goals: List[str]
) -> List[str]:
    """
    Given a message payload and a list of candidate goals (strings),
    ask Gemini to choose zero, one, or multiple matching goals.
    """
    if not candidate_goals:
        raise ValueError("candidate_goals must not be empty")

    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        "data": base_msg.data,
    }

    prompt = (
        "You are a goal selector for a backend orchestration AI.\n\n"
        "You will receive a JSON payload and a list of possible goals. Choose zero or more goals "
        "that best match this payload. If more than one fits, include all that apply, "
        "favoring the most specific matches.\n\n"
        "Important rules:\n"
        "- If none match, return an empty array.\n"
        "- Return goals exactly as written.\n"
        "- Do NOT invent new goals.\n\n"
        "=== PAYLOAD JSON ===\n"
        f"{json.dumps(payload_dict, indent=2)}\n\n"
        "=== CANDIDATE GOALS ===\n"
        f"{json.dumps(candidate_goals, indent=2)}\n\n"
        "Respond with ONLY a JSON object such as:"
        ' { "chosen_goals": ["goal_a", "goal_b"] }'
    )

    print("[AGENT] Asking model to select best goal(s)...")
    response = llm.invoke(prompt)
    text = (
        response.content if isinstance(response.content, str) else str(response.content)
    )
    print("[AGENT] Goal selection raw response:")
    print(text)

    obj = extract_json_object(text)
    raw_chosen = obj.get("chosen_goals", [])
    if isinstance(raw_chosen, str):
        raw_chosen = [raw_chosen]
    if not isinstance(raw_chosen, list):
        print("[AGENT] Unexpected format for chosen_goals; returning empty list.")
        return []

    chosen_list = []
    for goal in raw_chosen:
        if isinstance(goal, str) and goal.strip() in candidate_goals:
            chosen_list.append(goal.strip())

    return chosen_list


def classify_goal_mode(goal: str) -> str:
    """
    Convert a single goal into one of:
    - MONITOR
    - EXECUTE
    - MONITOR_EXECUTE
    - MONITOR_INFORM
    """
    prompt = (
        "You are a goal interpreter for a backend orchestration AI.\n"
        "Classify the provided goal into exactly one of: MONITOR, EXECUTE, MONITOR_EXECUTE, MONITOR_INFORM.\n\n"
        "Examples:\n"
        "- 'Monitor all sensor states' -> MONITOR\n"
        "- 'Change all Warning States to RED' -> EXECUTE\n"
        "- 'Check for sensor gap and if exist, change warning state to red' -> MONITOR_EXECUTE\n"
        "- 'Monitor tracks and notify me' -> MONITOR_INFORM\n\n"
        f"Goal: {goal}\n"
        "Return ONLY the mode name."
    )

    response = llm.invoke(prompt)
    mode = (
        (
            response.content
            if isinstance(response.content, str)
            else str(response.content)
        )
        .strip()
        .upper()
    )

    valid = {"MONITOR", "EXECUTE", "MONITOR_EXECUTE", "MONITOR_INFORM"}
    if mode not in valid:
        print(f"[AGENT] Invalid mode '{mode}', defaulting to MONITOR.")
        return "MONITOR"
    return mode


def classify_goal_modes(goals: List[str]) -> List[str]:
    """Classify multiple goals, preserving order."""
    modes: List[str] = []
    for goal in goals:
        modes.append(classify_goal_mode(goal))
    return modes
