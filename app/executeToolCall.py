import json
from typing import Any, List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain.agents import create_agent

from helper import extract_json_object
from llm import llm
from mqttPayloadSchema import BaseMessage
from tools import (
    TOOLS,
    call_dss_tool,
    check_sensor_gap_tool,
    notify_tool,
)


def _wrap_tool(fn, *, name: str, description: str):
    @tool(name, description=description)
    def _inner(**kwargs):
        if "kwargs" in kwargs and isinstance(kwargs["kwargs"], dict):
            nested = kwargs.pop("kwargs")
            kwargs.update(nested)

        return fn(**kwargs)

    return _inner


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

_agent = create_agent(llm, tools=wrapped_tools)


def _render_payload(base_msg: BaseMessage) -> str:
    payload_dict = {
        "type": base_msg.type,
        "action": base_msg.action,
        "userId": base_msg.userId,
        "data": base_msg.data,
    }
    return json.dumps(payload_dict, indent=2)


# Extract Text Helper from AI Response
def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(str(part) for part in content)
    return str(content)


def run_agent_for_message(base_msg: BaseMessage, candidate_goals: List[str]) -> str:
    """
    Agentic pipeline implemented with LangGraph's create_agent helper.
    The agent chooses zero, one, or multiple goals, decides goal modes,
    calls tools, and returns a concise textual summary.
    """

    if not candidate_goals:
        raise ValueError("candidate_goals must not be empty")

    # Internalise the payload
    payload_str = _render_payload(base_msg)

    # Internalise the candidate goals
    goals_str = json.dumps(candidate_goals, indent=2)

    # Construct system message to determine GOAL SELECTION
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

    # Add payload and goals to human message
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
    text_content = _extract_text(getattr(final_message, "content", ""))

    # If the model embedded a JSON summary, surface it cleanly for logs
    extracted = extract_json_object(text_content)
    if extracted:
        print("[AGENT] Extracted structured summary:")
        print(json.dumps(extracted, indent=2))

    return text_content
