from abc import ABC, abstractmethod
from aciarena.agent_components.llms import BaseLLM, OpenAILLM
from aciarena.agent_components.memory import Memory, Message
from typing import List, Dict, Optional, Any

def get_llm(llm_config: dict) -> BaseLLM:
    if llm_config.get("provider") == "openai":
        llm = OpenAILLM()
        return llm.from_config(llm_config)
    else:
        raise ValueError(f"Unsupported LLM provider: {llm_config.get('provider')}")

class BaseAgent:
    def __init__(self, llm_config, name: str = "", tools=[], profile: Optional[str] = None):
        self.name = name                    # Agent name (e.g., "assistant")
        self.profile = profile              # System message or persona description
        self.tools = tools
        self.memory = self.init_memory()    # Conversation memory
        self.llm = self.init_llm(llm_config)          # LLM interface to be implemented by subclass
        self.user_information = None

    def init_memory(self):
        """Initialize the memory component. Can be overridden for custom memory implementations."""
        return Memory()

    def init_llm(self, llm_config):
        """
        Initialize the LLM interface.
        """
        return get_llm(llm_config=llm_config)

    def update_memory(self, role: str, content: str):
        """Append a message to the conversation history."""
        self.memory.conversation.append({"role": role, "content": content})

    def retrieve_memory(self) -> Any:
        """Return the current conversation history."""
        return self.memory.conversation

    def refresh_memory(self) -> None:
        """Refresh the agent memory for new query."""
        self.memory.conversation = self.memory.conversation[:1]
        self.memory.received_messages.clear()
        self.memory.short_memory = ""


    def pre_step(self, query: str) -> str:
        """
        Pre-process the query before the step.
        """
        return query

    def post_step(self, response: str) -> str:
        """
        Post-process the response after the step.
        """
        return response

    def step(self, query: str, *args, **kwargs) -> str:
        """
        Single interaction step.
        Should be overridden in subclasses to define specific behavior.
        """
        raise NotImplementedError("Subclasses must implement the step method.")

    def run_step(self, query: str, *args, **kwargs) -> str:
        query = self.pre_step(query)
        response = self.step(query, *args, **kwargs)
        response = self.post_step(response)
        return response