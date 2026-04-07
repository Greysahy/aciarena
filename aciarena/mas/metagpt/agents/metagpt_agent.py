from typing import List, Dict, Optional, Any
from aciarena.agent_components.base_agent import BaseAgent
import os

class MetaGPTAgent(BaseAgent):
    def __init__(
        self,
        llm_config,
        name: str,
        description: str,
        role: str,
        goals: List[str],
        constraints: List[str],
        profile: Optional[str] = None,
    ):
        """
        MetaGPTAgent combines structured goal-based attributes with BaseAgent capabilities.
        """
        super().__init__(llm_config=llm_config, name=name, profile=profile)
        self.description = description         # Natural language description of the agent
        self.role = role                       # Role identifier (e.g., "Planner", "Developer")
        self.goals = goals                     # High-level task goals
        self.constraints = constraints         # Limitations or rules the agent must follow

        # Initialize structured memory
        self.memory = self.init_memory()

    def step(self, query: str, *args, **kwargs) -> str:
        """
        Define how the PMAgent responds to an input query (e.g., code generation prompt).
        """
        
        messages = [
            {"role": "system", "content": self.profile},
            {"role": "user", "content": str(query)}
        ]
        response = self.llm.call_llm(messages)
        self.update_memory(role="user", content=str(query))
        self.update_memory(role="assistant", content=response)
        return response