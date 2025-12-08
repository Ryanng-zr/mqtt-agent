from pydantic import BaseModel, Field
from typing import Dict, Any


class BaseMessage(BaseModel):
    """
    Baseline Struct for messages received by agent.
    """

    type: str
    action: str
    userId: str
    data: Dict[str, Any] = Field(default_factory=dict)
