from typing import Dict, Any, List
import json
from mqttPayloadSchema import BaseMessage
from tools import TOOLS
from llm import llm
from selectGoal import select_best_goal_for_message, classify_goal_mode
from chooseToolCall import plan_tool_calls_with_gemini

# Collate tool calls and execute

def execute_tool_calls(tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("args", {})
        print(f"[AGENT] Planned tool: {tool_name} with args {args}")

        tdef = TOOLS.get(tool_name)
        if not tdef:
            print(f"[AGENT] Unknown tool '{tool_name}', skipping.")
            results.append(
                {"tool": tool_name, "args": args, "result": {"error": f"Unknown tool '{tool_name}'"}}
            )
            continue

        try:
            result = tdef.fn(**args)
            results.append({"tool": tool_name, "args": args, "result": result})
        except TypeError as e:
            print(f"[AGENT] Argument error for tool '{tool_name}': {e}")
            results.append({"tool": tool_name, "args": args, "result": {"error": f"Argument error: {e}"}})
        except Exception as e:
            print(f"[AGENT] Exception while executing '{tool_name}': {e}")
            results.append({"tool": tool_name, "args": args, "result": {"error": f"Execution error: {e}"}})

    return results


# Summarise results for demo purpose

def summarize_run_with_gemini(base_msg: BaseMessage, goals: List[str], tool_results: List[Dict[str, Any]]) -> str:
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
            "You are summarizing the result of a backend orchestration run.",
            "",
            "Original JSON payload:",
            json.dumps(payload_dict, indent=2),
            "",
            "Goals for this run:",
            json.dumps(goals, indent=2),
            "",
            "Tool calls and results (as JSON):",
            json.dumps(tool_results, indent=2),
            "",
            "In a concise paragraph:",
            "- Explain which tools were called and why.",
            "- Mention any important results or errors.",
            "- Mention if any goals Fcould not be satisfied due to missing data.",
        ],
    }

    response = llm.generate_content(prompt)
    return response.text


# Logic for handling message

def run_agent_for_message(base_msg: BaseMessage, candidate_goals: List[str]) -> str:
    """
    Pipeline for each MQTT message:
    - Select best goal from candidate_goals
    - Classify goal into mode
    - Plan tools
    - Execute
    - Summarize
    """
    chosen_goal = select_best_goal_for_message(base_msg, candidate_goals)
    print(f"[AGENT] Chosen goal: {chosen_goal}")

    goal_mode = classify_goal_mode(chosen_goal)
    print(f"[AGENT] Goal mode: {goal_mode}")

    tool_calls = plan_tool_calls_with_gemini(base_msg, goal_mode, chosen_goal)
    tool_results = execute_tool_calls(tool_calls)

    summary = summarize_run_with_gemini(
        base_msg,
        goals=[chosen_goal, f"MODE={goal_mode}"],
        tool_results=tool_results,
    )
    return summary

