import requests
from typing import Dict, Any, Callable
import os

# REPLACE
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://localhost:5001/demo")
COMMON_HEADERS = {"X-Service-Name": "mqtt-agent"}


def check_sensor_gap_tool(user_id: str, incident_id: str) -> Dict[str, Any]:
    """
    Check sensor coverage and detect any sensor gaps in breach scenarios and user.
    Used to assess whether sensors cover an incident.
    """
    url = f"{BACKEND_BASE_URL}"
    payload = {
        "userId": user_id,
        "incidentId": incident_id,
    }
    print(f"[TOOL] check_sensor_gap_tool -> {url} {payload}")
    resp = requests.get(url, json=payload, headers=COMMON_HEADERS, timeout=10)
    resp.raise_for_status()
    print(f"[TOOL] check_sensor_gap_tool called")
    return resp.json()


def call_dss_tool(user_id: str, scenario: str) -> Dict[str, Any]:
    """
    Run DSS for a given user and in breach scenario to perform a set of actions.
    """
    url = f"{BACKEND_BASE_URL}"
    payload = {
        "userId": user_id,
        "scenario": scenario,
    }
    print(f"[TOOL] call_dss_tool -> {url} {payload}")
    resp = requests.get(url, json=payload, headers=COMMON_HEADERS, timeout=10)
    resp.raise_for_status()
    print(f"[TOOL] call_dss_tool called")
    return resp.json()


def notify_tool(user_id: str, message: str) -> Dict[str, Any]:
    """
    Send a notification associated with a specific user.
    Used when required to log or notify about what was done or a specific event.
    """
    url = f"{BACKEND_BASE_URL}"
    payload = {
        "userId": user_id,
        "message": message,
    }
    print(f"[TOOL] notify_tool -> {url} {payload}")
    resp = requests.get(url, json=payload, headers=COMMON_HEADERS, timeout=10)
    resp.raise_for_status()
    print(f"[TOOL] notify_tool called")
    return resp.json()


# Tool registry
class ToolDef:
    def __init__(self, name: str, description: str, fn: Callable[..., Dict[str, Any]]):
        self.name = name
        self.description = description
        self.fn = fn


TOOLS: Dict[str, ToolDef] = {
    "check_sensor_gap_tool": ToolDef(
        name="check_sensor_gap_tool",
        description=(
            "Check sensor coverage and detect any sensor gaps for a specific incident, user and in breach scenarios. "
            "Arguments: user_id (string), incident_id (string)."
        ),
        fn=check_sensor_gap_tool,
    ),
    "call_dss_tool": ToolDef(
        name="call_dss_tool",
        description=(
            "Run the decision support system (DSS) for a given user and only when in breach scenario for execution purpose. "
            "Arguments: user_id (string), scenario (string)."
        ),
        fn=call_dss_tool,
    ),
    "notify_tool": ToolDef(
        name="notify_tool",
        description=(
            "Always monitor and send a notification or log entry associated with a user. "
            "Arguments: user_id (string), message (string)."
        ),
        fn=notify_tool,
    ),
}
