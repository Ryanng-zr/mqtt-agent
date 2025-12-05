from pydantic import BaseModel, Field
from typing import Dict, Any


class BaseMessage(BaseModel):
    """
    Generic envelope for messages coming into the agent.
    Expect your MQTT JSON to match this shape.
    """

    type: str  # e.g. "EVENT", "COMMAND"
    action: str  # e.g. "AIR_TRACK_UPDATE", "START_DSS"
    userId: str
    data: Dict[str, Any] = Field(default_factory=dict)
