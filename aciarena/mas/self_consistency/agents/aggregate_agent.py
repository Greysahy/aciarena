from aciarena.agent_components import BaseAgent
from typing import List, Dict

class AggregateAgent(BaseAgent):
    def __init__(self, llm_config):
        super().__init__(llm_config=llm_config)
        self.name = "aggregate"
        self.profile = "You are a helpful assistant."
        self.update_memory(role="system", content=self.profile)

    def step(self, query: str, *args, **kwargs) -> str:
            self.memory.conversation[0]["content"] = self.profile
            self.update_memory(role="user", content=query)
            messages = self.retrieve_memory()
            response = self.llm.call_llm(messages)
            self.update_memory(role="assistant", content=response)

            return response

    def retrieve_memory(self) -> List[Dict]:
        return self.memory.conversation

    def update_memory(self, role, content) -> None:
        self.memory.conversation.append({"role": role, "content": content})
