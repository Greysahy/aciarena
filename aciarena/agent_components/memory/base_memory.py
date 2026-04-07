from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class Message(BaseModel):
    content: str = Field(..., description="The content of the message being sent")
    sender: str = Field(..., description="The identifier or name of the message sender")
    recipient: str = Field(..., description="The identifier or name of the message recipient")

    def __str__(self):
        return f"{self.sender} to {self.recipient}: {self.content}"


class Memory(BaseModel):
    conversation: List[Dict] = Field(default_factory=list, description="Full conversation history as a list of message dicts")
    received_messages: List[Message] = Field(default_factory=list, description="List of structured messages received by the agent")
    short_memory: Optional[str] = Field(default="", description="Summarized or compressed short-term memory")
