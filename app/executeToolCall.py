import json
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain.agents import create_agent

from helper import extract_json_object, _extract_text, _wrap_tool, _render_payload
from llm import llm
from mqttPayloadSchema import BaseMessage
from tools import (
    TOOLS,
    call_dss_tool,
    check_sensor_gap_tool,
    notify_tool,
)

# Tools to be retrieved from SWAGGER JSON from product teams
wrapped_tools = [
    _wrap_tool(
        check_sensor_gap_tool,
        name="check_sensor_gap_tool",
        description=TOOLS["check_sensor_gap_tool"].description,
    ),
    _wrap_tool(
        call_dss_tool,
        name="call_dss_tool",
        description=TOOLS["call_dss_tool"].description,
    ),
    _wrap_tool(
        notify_tool,
        name="notify_tool",
        description=TOOLS["notify_tool"].description,
    ),
]

# Main Agent to run tool calls
_agent = create_agent(llm, tools=wrapped_tools)


def run_agent_for_message(base_msg: BaseMessage, candidate_goals: List[str]) -> str:
    """
    Choose zero, one, or multiple goals, classify goals into goal modes,
    then execute tools, and return a summary.
    """
    # throw error if no goals
    if not candidate_goals:
        raise ValueError("candidate_goals must not be empty")

    # Deconstruct the payload into a string
    payload_str = _render_payload(base_msg)

    # Deconstruct the goals into a string
    goals_str = json.dumps(candidate_goals, indent=2)

    # Main Prompt to determine GOAL SELECTION
    system_msg = SystemMessage(
        content=(
            "You are an orchestration agent that must ground every action in the "
            "incoming MQTT payload. Choose zero, one, or multiple goals from the list, "
            "infer a goal mode (MONITOR, EXECUTE, MONITOR_EXECUTE, MONITOR_INFORM) for each, "
            "and use the available tools to satisfy them. Prefer monitoring/analysis "
            "before execution when uncertain. Avoid inventing data; if required "
            "fields are missing, explain the gap instead of hallucinating. If no goals "
            "apply, respond with an empty selection and refrain from tool calls."
        )
    )

    # Add payload and goals
    human_msg = HumanMessage(
        content=(
            "=== PAYLOAD ===\n"
            f"{payload_str}\n\n"
            "=== CANDIDATE GOALS ===\n"
            f"{goals_str}\n\n"
            "Decide which goals to pursue (including possibly none), determine a mode for each, "
            "and call tools as needed. End with a final assistant message containing a short summary "
            "plus a JSON block with keys: chosen_goals (array), goal_modes (object mapping goal->mode), "
            "chosen_tools (object mapping goal->tool) and results (any structured data)."
        )
    )

    print("[AGENT] Running LangGraph agent with create_agent...")
    result = _agent.invoke({"messages": [system_msg, human_msg]})

    messages = result.get("messages", [])
    final_message = messages[-1] if messages else None
    # Extract text content from final message
    text_content = _extract_text(getattr(final_message, "content", ""))

    # Extract chosen_goals from final message
    extracted = extract_json_object(text_content)
    if extracted:
        print("[AGENT] Extracted structured summary:")
        print(json.dumps(extracted, indent=2))

    return text_content
